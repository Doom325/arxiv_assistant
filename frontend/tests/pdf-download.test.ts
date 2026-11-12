/**
 * On-demand PDF download: structured-error parsing + UI wiring.
 *
 * `node --test` ships no DOM, so we verify the pure parser and the shared
 * formatter (the download-error detail reuses the summary_error shape), plus
 * the structural guarantee that the api client and the paper page are wired
 * for the feature. The parser tests fail on the old code (the export does not
 * exist) and pass on the fix.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { parsePdfDownloadError, PdfDownloadFailedError } from "../lib/api.ts";
import { formatSummaryError } from "../lib/summaryError.ts";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_ROOT = path.resolve(__dirname, "..");

function readFrontendFile(relPath: string): string {
    return fs.readFileSync(path.join(FRONTEND_ROOT, relPath), "utf8");
}

describe("parsePdfDownloadError", () => {
    it("reads a structured backend detail (disk full, not retryable)", () => {
        const detail = parsePdfDownloadError(
            {
                detail: {
                    code: "pdf_disk_full",
                    message: "No space left on the PDF storage volume.",
                    retryable: false,
                },
            },
            "fallback",
        );
        assert.equal(detail.code, "pdf_disk_full");
        assert.equal(detail.message, "No space left on the PDF storage volume.");
        assert.equal(detail.retryable, false);
    });

    it("reads an upstream HTTP detail with status + retryable", () => {
        const detail = parsePdfDownloadError(
            {
                detail: {
                    code: "pdf_http_error",
                    message: "arXiv returned HTTP 429 while downloading the PDF.",
                    retryable: true,
                    http_status: 429,
                },
            },
            "fallback",
        );
        assert.equal(detail.retryable, true);
        assert.equal(detail.http_status, 429);
    });

    it("accepts a plain string detail", () => {
        const detail = parsePdfDownloadError({ detail: "Paper not found" }, "fallback");
        assert.equal(detail.message, "Paper not found");
    });

    it("falls back when the body is missing or malformed", () => {
        assert.equal(parsePdfDownloadError(null, "fallback").message, "fallback");
        assert.equal(parsePdfDownloadError({}, "fallback").message, "fallback");
        assert.equal(parsePdfDownloadError("oops", "fallback").message, "fallback");
    });
});

describe("PdfDownloadFailedError", () => {
    it("carries the server's real reason as message + structured fields", () => {
        const err = new PdfDownloadFailedError({
            code: "pdf_disk_full",
            message: "No space left on the PDF storage volume.",
            retryable: false,
        });
        assert.ok(err instanceof Error);
        assert.equal(err.message, "No space left on the PDF storage volume.");
        assert.equal(err.code, "pdf_disk_full");
        assert.equal(err.retryable, false);
    });
});

describe("formatSummaryError renders a PDF download error (shared shape)", () => {
    it("surfaces a disk-full message verbatim (no retry hint)", () => {
        assert.equal(
            formatSummaryError({
                code: "pdf_disk_full",
                message: "No space left on the PDF storage volume.",
                retryable: false,
            }),
            "No space left on the PDF storage volume.",
        );
    });

    it("appends a retry hint for a transient upstream failure", () => {
        assert.equal(
            formatSummaryError({
                code: "pdf_http_error",
                message: "arXiv returned HTTP 429 while downloading the PDF.",
                retryable: true,
            }),
            "arXiv returned HTTP 429 while downloading the PDF. (This may be temporary — try again.)",
        );
    });
});

describe("the download feature is wired end to end", () => {
    it("api client exposes downloadPaperPdf and the pdf_available field", () => {
        const apiSrc = readFrontendFile("lib/api.ts");
        assert.match(apiSrc, /downloadPaperPdf\s*:/);
        assert.match(apiSrc, /pdf_available\?/);
        assert.match(apiSrc, /\/pdf\/download/);
    });

    it("the paper detail page offers the download action when pdf_available is false", () => {
        const pageSrc = readFrontendFile("app/paper/[id]/page.tsx");
        assert.match(pageSrc, /pdf_available === false/);
        assert.match(pageSrc, /handleDownloadPdf/);
        assert.match(pageSrc, /downloadPaperPdf\(/);
    });
});
