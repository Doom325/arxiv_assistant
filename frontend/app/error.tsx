"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // Log the error to an error reporting service
        console.error("Next.js Error Boundary caught:", error);
    }, [error]);

    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 bg-surface-card border border-border-default rounded-xl text-center">
            <AlertTriangle className="h-12 w-12 text-amber-500 mb-4" />
            <h2 className="text-xl font-bold text-foreground mb-2">Something went wrong (Next.js)</h2>
            <p className="text-foreground-secondary max-w-md mx-auto mb-6">
                {error.message || "An unexpected error occurred in the dashboard."}
            </p>
            <button
                onClick={() => reset()}
                className="inline-flex items-center px-4 py-2 bg-accent hover:bg-accent/90 text-white rounded-md transition-colors"
            >
                <RefreshCcw className="h-4 w-4 mr-2" />
                Try again
            </button>
            <div className="mt-8 text-[10px] text-foreground-muted opacity-50">v1.0.1 (Clean Build: 2026-01-26 12:40)</div>
        </div>
    );
}
