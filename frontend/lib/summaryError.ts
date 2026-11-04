import type { SummaryError } from "./api";

const RETRY_HINT = "This may be temporary — try again.";

/**
 * Builds the user-facing summarization error string from the backend's
 * structured `summary_error`.
 *
 * The upstream message (e.g. "NVIDIA API 429: ...") is surfaced verbatim so a
 * reader can tell a transient failure from a structural one. When the backend
 * flagged the failure as retryable, a short hint is appended; structural
 * errors (bad key, wrong model, bad request) are shown as-is.
 */
export function formatSummaryError(error?: SummaryError | null): string {
    const base = error?.message?.trim() || "Summarization failed.";
    return error?.retryable ? `${base} (${RETRY_HINT})` : base;
}
