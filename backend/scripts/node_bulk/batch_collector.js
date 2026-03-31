import pg from 'pg';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
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

// Regex to extract arXiv IDs from raw citation text
function extractArxivId(text) {
    if (!text) return null;
    // Match common arxiv formats: 2401.12345 or cond-mat/0101123
    const match = text.match(/(\d{4}\.\d{4,5}(v\d+)?)|([a-z\-]+\/\d{7}(v\d+)?)/i);
    return match ? match[0] : null;
}

async function run() {
    console.log("🚀 Starting Batch Collector...");
    if (!API_KEY) {
        console.error("❌ FINAL_GOOGLE_API_KEY not found in environment.");
        process.exit(1);
    }

    const client = await pool.connect();

    try {
        const jobsRes = await client.query(`
            SELECT DISTINCT batch_job_id 
            FROM bulk_process_tracker 
            WHERE status = 'queued_batch'
        `);

        if (jobsRes.rows.length === 0) {
            console.log("No queued batch jobs found in tracker.");
            return;
        }

        for (const job of jobsRes.rows) {
            const jobId = job.batch_job_id;
            console.log(`Checking status of job: ${jobId}`);

            try {
                const statusRes = await axios.get(
                    `https://generativelanguage.googleapis.com/v1beta/${jobId}?key=${API_KEY}`
                );

                const jobData = statusRes.data;
                const state = jobData.state;
                console.log(`Job state: ${state}`);

                if (state === 'SUCCEEDED') {
                    // Output file is usually in the response metadata's output_config or direct field
                    const outputFileUri = jobData.response?.output_config?.source || jobData.output_config?.source;
                    if (!outputFileUri) {
                        console.error("❌ SUCCEEDED but no output file URI found in job metadata.");
                        console.log("Full Job Data:", JSON.stringify(jobData, null, 2));
                        continue;
                    }

                    console.log(`Downloading results from ${outputFileUri}...`);
                    // URI format: https://generativelanguage.googleapis.com/v1beta/files/file-id
                    const downloadRes = await axios.get(
                        `${outputFileUri}?key=${API_KEY}`,
                        { responseType: 'text' }
                    );

                    const results = downloadRes.data.split('\n').filter(l => l.trim());
                    console.log(`Processing ${results.length} results...`);

                    for (const line of results) {
                        const result = JSON.parse(line);
                        const customId = result.custom_id;
                        const paperId = parseInt(customId.replace('paper_', ''));

                        try {
                            if (result.status && result.status.code !== 0) {
                                throw new Error(`API Error ${result.status.code}: ${result.status.message}`);
                            }

                            const content = result.response.candidates[0].content.parts[0].text;
                            // Clean markdown
                            const cleanJson = content.replace(/```json\n?|\n?```/g, '').trim();
                            const citations = JSON.parse(cleanJson);

                            // 1. Update papers table
                            await client.query(`
                                UPDATE papers SET citations = $1 WHERE id = $2
                            `, [JSON.stringify(citations), paperId]);

                            // 2. Resolve and Link
                            for (const cit of citations) {
                                const resolvedArxivId = extractArxivId(cit.raw);
                                if (resolvedArxivId) {
                                    const linkedPaper = await client.query(
                                        "SELECT id FROM papers WHERE arxiv_id = $1",
                                        [resolvedArxivId]
                                    );
                                    if (linkedPaper.rows.length > 0) {
                                        await client.query(`
                                            INSERT INTO citation_links (source_paper_id, resolved_paper_id, arxiv_id, title)
                                            VALUES ($1, $2, $3, $4)
                                            ON CONFLICT DO NOTHING
                                        `, [paperId, linkedPaper.rows[0].id, resolvedArxivId, cit.title]);
                                    }
                                }
                            }

                            // 3. Mark tracker as completed
                            await client.query(`
                                UPDATE bulk_process_tracker SET status = 'completed' WHERE paper_id = $1
                            `, [paperId]);

                        } catch (e) {
                            console.error(`Error processing result for paper ${paperId}:`, e.message);
                            await client.query(`
                                UPDATE bulk_process_tracker SET status = 'failed', metadata = $1 WHERE paper_id = $2
                            `, [JSON.stringify({ error: e.message, raw: result }), paperId]);
                        }
                    }
                    console.log(`✅ Job ${jobId} fully synced.`);
                } else if (state === 'FAILED') {
                    console.error(`❌ Job ${jobId} failed:`, jobData.error);
                } else {
                    console.log(`... Job ${jobId} still in progress (${state}).`);
                }
            } catch (e) {
                console.error(`Error checking job ${jobId}:`, e.response?.data || e.message);
            }
        }
    } finally {
        client.release();
        await pool.end();
    }
}

run();
