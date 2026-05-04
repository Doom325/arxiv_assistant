"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "./api";

interface UseSummarizeResult {
    summarizing: boolean;
    updatedSummary: string | null;
    error: string | null;
    triggerSummarize: (force?: boolean, model?: string) => void;
}

export function useSummarize(paperId: number | null): UseSummarizeResult {
    const [summarizing, setSummarizing] = useState(false);
    const [updatedSummary, setUpdatedSummary] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const pollRef = useRef<NodeJS.Timeout | null>(null);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);
    // Moment the most recent triggerSummarize call kicked off polling.
    // Used to reject stale failures from a prior session/reload.
    //
    // Caveat (tracked in #17 reviewer feedback F3): this compares a
    // client-local timestamp to a server-side ``summary_attempted_at``. With
    // significant clock skew between the user's device and the backend, a
    // genuinely fresh failure could look stale (or vice versa). Acceptable
    // today because the polling window is seconds and the staleness gate
    // is only used to suppress re-alerting — never to accept/reject data.
    // If this ever drives user-visible correctness, swap for a server-issued
    // polling token or a baseline ``summary_attempted_at`` captured at the
    // polling-start API response.
    const sessionStartRef = useRef<Date | null>(null);

    const cleanup = useCallback(() => {
        if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
        }
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
        }
    }, []);

    // Reset state when paperId changes
    useEffect(() => {
        cleanup();
        setSummarizing(false);
        setUpdatedSummary(null);
        setError(null);
        sessionStartRef.current = null;
    }, [paperId, cleanup]);

    // Cleanup on unmount
    useEffect(() => cleanup, [cleanup]);

    const triggerSummarize = useCallback(
        async (force?: boolean, model?: string) => {
            if (!paperId) return;
            const sessionStartedAt = new Date();
            sessionStartRef.current = sessionStartedAt;
            setSummarizing(true);
            setError(null);

            try {
                await api.generateSummary(paperId, force ?? false, model);

                pollRef.current = setInterval(async () => {
                    try {
                        const updated = await api.getPaper(String(paperId));

                        if (updated.summary_status === "failed") {
                            const attemptedAt = updated.summary_attempted_at
                                ? new Date(updated.summary_attempted_at)
                                : null;
                            const isFresh =
                                !!attemptedAt &&
                                attemptedAt >= sessionStartedAt;
                            if (!isFresh) {
                                // Stale failure — keep polling.
                                return;
                            }
                            const errorMsg =
                                updated.summary_error?.message ??
                                "Summarization failed.";
                            setError(errorMsg);
                            setSummarizing(false);
                            cleanup();
                            return;
                        }

                        if (
                            updated.summary_status === "succeeded" &&
                            updated.generated_summary
                        ) {
                            setUpdatedSummary(updated.generated_summary);
                            setSummarizing(false);
                            cleanup();
                        }
                    } catch (e) {
                        console.error("Polling error:", e);
                    }
                }, 3000);

                timeoutRef.current = setTimeout(() => {
                    cleanup();
                    setSummarizing(false);
                    setError("Summarization timed out. Check backend logs.");
                }, 1800000);
            } catch (e) {
                console.error("Summarization error:", e);
                setSummarizing(false);
                setError("Failed to start summarization.");
            }
        },
        [paperId, cleanup]
    );

    return { summarizing, updatedSummary, error, triggerSummarize };
}
