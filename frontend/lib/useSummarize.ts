"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "./api";

interface UseSummarizeResult {
    summarizing: boolean;
    updatedSummary: string | null;
    error: string | null;
    triggerSummarize: (force?: boolean) => void;
}

export function useSummarize(paperId: number | null): UseSummarizeResult {
    const [summarizing, setSummarizing] = useState(false);
    const [updatedSummary, setUpdatedSummary] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const pollRef = useRef<NodeJS.Timeout | null>(null);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);

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
    }, [paperId, cleanup]);

    // Cleanup on unmount
    useEffect(() => cleanup, [cleanup]);

    const triggerSummarize = useCallback(
        async (force?: boolean) => {
            if (!paperId) return;
            setSummarizing(true);
            setError(null);

            try {
                await api.generateSummary(paperId, force ?? false);

                pollRef.current = setInterval(async () => {
                    try {
                        const updated = await api.getPaper(String(paperId));
                        if (updated.generated_summary) {
                            if (updated.generated_summary.startsWith("__ERROR__")) {
                                const errorMsg = updated.generated_summary.replace("__ERROR__: ", "");
                                setError(errorMsg);
                                setSummarizing(false);
                                cleanup();
                                return;
                            }
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
