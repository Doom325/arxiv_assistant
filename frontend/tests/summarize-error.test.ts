/**
 * Summarization error surfacing (`fix/nvidia-summarization-error-detail`).
 *
 * Verifies the pure display formatter that turns the backend's structured
 * `summary_error` into the string shown to the user, and the structural
 * guarantee that every polling surface routes through that one formatter
 * rather than re-deriving the message (and silently dropping the detail).
 *
 * DOM rendering of the surfaces (QuickPeekSheet, DashboardQuickPeek,
 * QuickPreviewPanel) is omitted for the same reason as nav-consolidation:
 * this `node --test` lane ships no DOM libraries. The surfaces render the
 * hook's `error` string directly, so the formatter is the whole decision.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { formatSummaryError } from "../lib/summaryError.ts";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_ROOT = path.resolve(__dirname, "..");

function readFrontendFile(relPath: string): string {
    return fs.readFileSync(path.join(FRONTEND_ROOT, relPath), "utf8");
}

describe("formatSummaryError", () => {
    it("surfaces a structural upstream message verbatim (no retry hint)", () => {
        assert.equal(
            formatSummaryError({
                code: "summarization_failed",
                message: "NVIDIA API 401: invalid API key",
                retryable: false,
            }),
            "NVIDIA API 401: invalid API key",
        );
    });

    it("appends a retry hint for transient failures", () => {
        assert.equal(
            formatSummaryError({
                code: "summarization_failed",
                message: "NVIDIA API 429: Rate limit exceeded",
                retryable: true,
            }),
            "NVIDIA API 429: Rate limit exceeded (This may be temporary — try again.)",
        );
    });

    it("falls back to a generic message when none is usable", () => {
        assert.equal(formatSummaryError(null), "Summarization failed.");
        assert.equal(formatSummaryError(undefined), "Summarization failed.");
        assert.equal(
            formatSummaryError({ code: "x", message: "   " }),
            "Summarization failed.",
        );
    });
});

describe("summarization surfaces route through the shared formatter", () => {
    it("useSummarize and the paper detail page both call formatSummaryError", () => {
        const hookSrc = readFrontendFile("lib/useSummarize.ts");
        assert.match(hookSrc, /formatSummaryError\(/);
        assert.doesNotMatch(hookSrc, /summary_error\?\.message\s*\?\?/);

        const pageSrc = readFrontendFile("app/paper/[id]/page.tsx");
        assert.match(pageSrc, /formatSummaryError\(/);
        assert.doesNotMatch(pageSrc, /summary_error\?\.message\s*\?\?/);
    });
});
