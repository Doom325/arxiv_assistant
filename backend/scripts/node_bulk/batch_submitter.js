import pg from 'pg';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import pdf from 'pdf-parse/lib/pdf-parse.js';
import pLimit from 'p-limit';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Load .env from backend root
dotenv.config({ path: path.join(__dirname, '../../.env') });

const { Pool } = pg;
let connectionString = process.env.DATABASE_URL;
if (connectionString.includes('db:5432')) {
    console.log("🔄 Adjusting DATABASE_URL for host network access...");
    connectionString = connectionString.replace('db:5432', 'localhost:5434');
}
const pool = new Pool({
    connectionString: connectionString
});

const API_KEY = (process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || "").replace(/"/g, '').trim();
const MODEL = 'models/gemini-2.0-flash-lite-preview-02-05';
const PDF_DIR = process.env.PDF_SAVE_DIR || '/app/data';
const PARALLEL_PDF_PARSING = 20;

async function extractReferences(arxivId) {
    const pdfPath = path.join(PDF_DIR, `${arxivId}.pdf`);
    if (!fs.existsSync(pdfPath)) {
        console.warn(`PDF not found for ${arxivId}: ${pdfPath}`);
        return null;
    }

    try {
        const dataBuffer = fs.readFileSync(pdfPath);
        const data = await pdf(dataBuffer);
        const text = data.text;
        // Take the last 15,000 characters which reliably contain the bibliography
        return text.slice(-15000);
    } catch (e) {
        // console.error(`Error parsing PDF for ${arxivId}:`, e.message);
        return null;
    }
}

async function run() {
    console.log("🚀 Starting Batch Submitter (Full Scale)...");
    if (!API_KEY) {
        console.error("❌ GEMINI_API_KEY not found in environment.");
        process.exit(1);
    }

    const client = await pool.connect();
    const limit = pLimit(PARALLEL_PDF_PARSING);

    try {
        console.log("Fetching pending papers from bulk_process_tracker...");
        const res = await client.query(`
            SELECT p.id, p.arxiv_id, p.summary 
            FROM bulk_process_tracker t
            JOIN papers p ON t.paper_id = p.id
            WHERE t.status = 'pending'
            ORDER BY p.id ASC
            LIMIT 100000 
        `);

        console.log(`Found ${res.rows.length} papers to process.`);
        if (res.rows.length === 0) return;

        const jsonlPath = path.join(__dirname, 'bulk_backfill.jsonl');
        const jsonlStream = fs.createWriteStream(jsonlPath);

        const promptTemplate = (text) => `
Extract the papers cited in the following text. 
For each citation, extract:
1. Title: The title of the paper.
2. Authors: A list of author names.
3. URL: Any URL or link mentioned.
4. Raw: The full original citation text.

Text:
${text}

Return the result as a JSON list of objects. Each object should have keys: "title", "authors", "url", "raw".
If you cannot find specific fields, use null or empty list for authors.
Respond ONLY with the JSON.`.trim();

        let count = 0;

        // Process in chunks to manage memory and DB updates
        const chunkSize = 100;
        for (let i = 0; i < res.rows.length; i += chunkSize) {
            const chunk = res.rows.slice(i, i + chunkSize);

            const tasks = chunk.map(row => limit(async () => {
                const refText = (await extractReferences(row.arxiv_id)) || row.summary;
                return {
                    id: row.id,
                    request: {
                        custom_id: `paper_${row.id}`,
                        request: {
                            contents: [{ role: "user", parts: [{ text: promptTemplate(refText) }] }]
                        }
                    }
                };
            }));

            const results = await Promise.all(tasks);

            for (const result of results) {
                jsonlStream.write(JSON.stringify(result.request) + '\n');
                await client.query('UPDATE bulk_process_tracker SET status = $1 WHERE paper_id = $2', ['in_jsonl', result.id]);
            }

            count += chunk.length;
            console.log(`Processed: ${count}/${res.rows.length} (${((count / res.rows.length) * 100).toFixed(1)}%)`);
        }

        jsonlStream.end();
        console.log(`✅ JSONL generation complete: ${jsonlPath}`);

        // --- UPLOAD TO GEMINI FILE API ---
        const stats = fs.statSync(jsonlPath);
        console.log(`Uploading ${stats.size} bytes (${(stats.size / 1024 / 1024).toFixed(2)} MB) to Gemini File API...`);

        console.log("Initiating resumable upload...");
        const initiateRes = await axios.post(
            `https://generativelanguage.googleapis.com/upload/v1beta/files?key=${API_KEY}`,
            { file: { display_name: "bulk_backfill_full" } },
            {
                headers: {
                    'X-Goog-Upload-Protocol': 'resumable',
                    'X-Goog-Upload-Command': 'start',
                    'X-Goog-Upload-Header-Content-Length': stats.size,
                    'X-Goog-Upload-Header-Content-Type': 'application/json',
                    'Content-Type': 'application/json'
                }
            }
        );

        const uploadUrl = initiateRes.headers['x-goog-upload-url'] || initiateRes.headers['location'];
        if (!uploadUrl) {
            throw new Error("Failed to get upload URL from Gemini API.");
        }
        console.log(`✅ Upload session initiated.`);

        const uploadFinalRes = await axios.post(
            uploadUrl,
            fs.readFileSync(jsonlPath),
            {
                headers: {
                    'X-Goog-Upload-Command': 'upload, finalize',
                    'X-Goog-Upload-Offset': 0,
                    'Content-Length': stats.size,
                    'Content-Type': 'application/json'
                }
            }
        );

        const fileUri = uploadFinalRes.data.file.uri;
        console.log(`✅ Upload successful. File URI: ${fileUri}`);
        console.log("Next step: Run 'python3 batch_submitter_v2.py --file bulk_backfill.jsonl' to submit the job.");

        // --- SUBMIT BATCH JOB ---
        console.log(`Submitting Batch Job for model ${MODEL}...`);

        try {
            const batchRes = await axios.post(
                `https://generativelanguage.googleapis.com/v1beta/batches?key=${API_KEY}`,
                {
                    model: MODEL,
                    src: {
                        file_uri: fileUri
                    }
                }
            );
            const jobName = batchRes.data.name;
            console.log(`🚀 Batch Job Submitted! Job ID: ${jobName}`);
            await client.query('UPDATE bulk_process_tracker SET batch_job_id = $1, status = $2 WHERE status = $3', [jobName, 'queued_batch', 'in_jsonl']);
        } catch (submitE) {
            console.error("❌ Submission Fatal Error:", submitE.response?.data || submitE.message);
            throw submitE;
        }
        console.log("Done. Monitor the job using batch_collector.js");

    } catch (e) {
        console.error("❌ Fatal Error:", e.response?.data || e.message);
    } finally {
        client.release();
        await pool.end();
    }
}

run();
