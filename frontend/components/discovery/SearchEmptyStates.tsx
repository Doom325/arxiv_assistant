"use client";

import { motion } from "framer-motion";
import { SearchX, AlertCircle } from "lucide-react";
import RippleButton from "../RippleButton";

/* ── No Results ────────────────────────────────── */

export function SearchNoResults() {
    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="text-center py-16 bg-surface-card/50 rounded-2xl"
            style={{ border: "2px dashed var(--color-accent)" + "33" }}
        >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-surface-inset mb-6">
                <SearchX className="h-8 w-8 text-foreground-muted" />
            </div>

            <h3 style={{ fontFamily: "var(--font-display)" }} className="mb-2">
                <span className="text-2xl font-light text-foreground">No results </span>
                <span className="text-2xl font-bold italic text-foreground">found.</span>
            </h3>

            <p
                className="text-foreground-secondary max-w-md mx-auto mb-6 italic"
                style={{ fontFamily: "var(--font-display)" }}
            >
                Try different keywords or use search operators to refine your query.
            </p>

            <div className="flex justify-center gap-4 flex-wrap">
                {[
                    { label: "category:", example: "cs.AI" },
                    { label: "after:", example: "2024" },
                    { label: "author:", example: "Vaswani" },
                ].map((hint) => (
                    <span
                        key={hint.label}
                        className="px-3 py-1.5 bg-surface-inset rounded-full text-xs text-foreground-muted font-mono"
                    >
                        {hint.label}
                        <span className="text-accent">{hint.example}</span>
                    </span>
                ))}
            </div>
        </motion.div>
    );
}

/* ── Error State ───────────────────────────────── */

interface SearchErrorProps {
    onRetry: () => void;
    errorMessage?: string | null;
}

export function SearchError({ onRetry, errorMessage }: SearchErrorProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="text-center py-16 bg-surface-card rounded-2xl shadow-warm-sm px-6"
        >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-50 mb-6">
                <AlertCircle className="h-8 w-8 text-red-500" />
            </div>

            <h3 className="text-xl font-medium text-foreground mb-2">
                Search Failed
            </h3>
            
            <p className="text-foreground-secondary max-w-md mx-auto mb-4 text-sm">
                We encountered an issue while performing your search.
            </p>

            {errorMessage && (
                <div className="max-w-lg mx-auto mb-6 p-3 rounded-lg bg-red-50/50 border border-red-200/60 text-red-700 text-xs font-mono break-words text-left">
                    <span className="font-semibold block mb-0.5 text-red-800">Error Detail:</span>
                    {errorMessage}
                </div>
            )}

            <RippleButton
                onClick={onRetry}
                className="inline-flex items-center px-5 py-2.5 bg-accent hover:bg-accent-hover text-on-accent text-sm font-medium rounded-full transition-colors"
            >
                Try Again
            </RippleButton>
        </motion.div>
    );
}

/* ── Loading Skeleton ──────────────────────────── */

function SkeletonResultCard() {
    return (
        <div className="bg-surface-card rounded-2xl p-5 shadow-warm-sm h-full flex flex-col">
            {/* Category chips */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex gap-2">
                    <div className="skeleton h-5 w-14 rounded-full" />
                    <div className="skeleton h-5 w-14 rounded-full" />
                </div>
                <div className="skeleton h-5 w-5 rounded-full" />
            </div>

            {/* Title */}
            <div className="mb-2 space-y-2">
                <div className="skeleton h-5 w-full" />
                <div className="skeleton h-5 w-3/4" />
            </div>

            {/* Abstract */}
            <div className="flex-grow mb-3 space-y-2">
                <div className="skeleton h-4 w-full" />
                <div className="skeleton h-4 w-11/12" />
                <div className="skeleton h-4 w-2/3" />
            </div>

            {/* Metadata */}
            <div className="flex gap-2 mb-3">
                <div className="skeleton h-3 w-3 rounded-full" />
                <div className="skeleton h-3 w-20" />
                <div className="skeleton h-3 w-16" />
            </div>

            {/* Footer */}
            <div className="pt-3" style={{ borderTop: "1px solid var(--color-surface-inset)" }}>
                <div className="skeleton h-4 w-20" />
            </div>
        </div>
    );
}

export function SearchSkeleton({ count = 6 }: { count?: number }) {
    return (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: count }).map((_, i) => (
                <SkeletonResultCard key={i} />
            ))}
        </div>
    );
}
