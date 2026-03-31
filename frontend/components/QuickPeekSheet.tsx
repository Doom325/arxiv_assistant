"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useDrag } from "@use-gesture/react";
import { useState, useRef, useEffect } from "react";
import { X, ChevronLeft, ChevronRight, ExternalLink, Calendar, Clock, Lightbulb, GitBranch } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import Link from "next/link";
import { Paper } from "../lib/api";
import BookmarkButton from "./BookmarkButton";
import RippleButton from "./RippleButton";
import { getCategoryColor, estimateReadingTime } from "../lib/categoryColors";
import { useSummarize } from "../lib/useSummarize";

interface QuickPeekSheetProps {
    paper: Paper | null;
    onClose: () => void;
    onPrev?: () => void;
    onNext?: () => void;
    hasPrev?: boolean;
    hasNext?: boolean;
    onPaperUpdated?: (paper: Paper) => void;
}

export default function QuickPeekSheet({
    paper,
    onClose,
    onPrev,
    onNext,
    hasPrev = false,
    hasNext = false,
    onPaperUpdated,
}: QuickPeekSheetProps) {
    const [dragY, setDragY] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);
    const { summarizing, updatedSummary, error, triggerSummarize } = useSummarize(paper?.db_id ?? null);

    // Propagate updated summary back to parent
    useEffect(() => {
        if (updatedSummary && paper && onPaperUpdated) {
            onPaperUpdated({ ...paper, generated_summary: updatedSummary });
        }
    }, [updatedSummary]);

    const bind = useDrag(
        ({ movement: [mx, my], velocity: [, vy], direction: [dx, dy], cancel, last }) => {
            // Vertical drag to dismiss
            if (my > 0) {
                setDragY(my);
            }

            if (last) {
                if (my > 100 || vy > 0.5) {
                    onClose();
                } else if (Math.abs(mx) > 80 && Math.abs(mx) > Math.abs(my)) {
                    // Horizontal swipe for prev/next
                    if (mx > 0 && hasPrev && onPrev) {
                        onPrev();
                    } else if (mx < 0 && hasNext && onNext) {
                        onNext();
                    }
                }
                setDragY(0);
            }
        },
        { axis: "lock", filterTaps: true },
    );

    if (!paper) return null;

    const primaryCategory = paper.categories?.[0] || "cs.AI";
    const catColor = getCategoryColor(primaryCategory);
    const readTime = estimateReadingTime(paper.summary);
    const displaySummary = updatedSummary || paper.generated_summary;
    const isRegenerate = !!displaySummary;

    return (
        <AnimatePresence>
            {paper && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        className="fixed inset-0 z-[80] bg-black/60"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onMouseDown={(e) => {
                            // Only close if clicking the backdrop itself, not portaled elements
                            if (e.target === e.currentTarget) onClose();
                        }}
                    />

                    {/* Sheet */}
                    <motion.div
                        ref={containerRef}
                        className="fixed bottom-0 left-0 right-0 z-[81] bg-surface-card/95 glass-modal border-t border-border-default rounded-t-3xl max-h-[80vh] overflow-y-auto"
                        initial={{ y: "100%" }}
                        animate={{ y: dragY }}
                        exit={{ y: "100%" }}
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    >
                        {/* Drag handle */}
                        <div
                            {...bind()}
                            className="flex justify-center pt-3 pb-2 cursor-grab active:cursor-grabbing"
                            style={{ touchAction: "none" }}
                        >
                            <div className="w-10 h-1 rounded-full bg-foreground-muted" />
                        </div>

                        <div className="px-6 pb-8 max-w-3xl mx-auto">
                            {/* Header */}
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    {paper.categories.slice(0, 3).map((cat) => {
                                        const cc = getCategoryColor(cat);
                                        return (
                                            <span
                                                key={cat}
                                                className={`px-2.5 py-1 ${cc.bg} ${cc.text} border ${cc.border} text-xs rounded-full font-medium`}
                                            >
                                                {cat}
                                            </span>
                                        );
                                    })}
                                </div>
                                <div className="flex items-center gap-2">
                                    <BookmarkButton paper={paper} />
                                    <button
                                        onClick={onClose}
                                        className="p-1.5 rounded-lg hover:bg-surface-inset text-foreground-secondary hover:text-foreground transition-colors"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>
                            </div>

                            {/* Title */}
                            <Link href={`/paper/${paper.db_id || paper.id}`} onClick={onClose}>
                                <h2 className="text-xl font-bold text-foreground mb-3 hover:text-accent transition-colors">
                                    {paper.title}
                                </h2>
                            </Link>

                            {/* Meta */}
                            <div className="flex items-center gap-3 text-sm text-foreground-secondary mb-4">
                                <Calendar className="h-4 w-4" />
                                <span suppressHydrationWarning>
                                    {paper.published_date
                                        ? new Date(paper.published_date).toLocaleDateString()
                                        : "Unknown"}
                                </span>
                                {readTime && (
                                    <>
                                        <span className="text-foreground-muted">·</span>
                                        <Clock className="h-3.5 w-3.5" />
                                        <span className="text-xs">{readTime}</span>
                                    </>
                                )}
                                {paper.arxiv_id && (
                                    <>
                                        <span className="text-foreground-muted">·</span>
                                        <span className="text-xs font-mono text-foreground-muted">{paper.arxiv_id}</span>
                                    </>
                                )}
                            </div>

                            {/* Abstract */}
                            <div className="mb-6">
                                <h3 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wider mb-2">Abstract</h3>
                                <div className="prose prose-sm max-w-none">
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm, remarkMath]}
                                        rehypePlugins={[rehypeKatex]}
                                    >
                                        {paper.summary || "No abstract available."}
                                    </ReactMarkdown>
                                </div>
                            </div>

                            {/* AI Summary */}
                            <div className="mb-6 bg-surface-inset border border-border-default rounded-2xl p-5">
                                <div className="flex items-center justify-between mb-3">
                                    <h3 className="text-sm font-semibold text-foreground-secondary uppercase tracking-wider flex items-center gap-2">
                                        <Lightbulb className="h-4 w-4 text-yellow-400" />
                                        AI Summary
                                    </h3>
                                    <RippleButton
                                        onClick={() => triggerSummarize(isRegenerate)}
                                        disabled={summarizing}
                                        className="bg-accent hover:bg-accent/90 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-all shadow-warm-sm disabled:opacity-50"
                                    >
                                        {summarizing ? (
                                            <span className="flex items-center gap-2">
                                                <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                Analyzing...
                                            </span>
                                        ) : isRegenerate ? (
                                            "Regenerate"
                                        ) : (
                                            "Analyze with Gemini"
                                        )}
                                    </RippleButton>
                                </div>

                                {error && (
                                    <p className="text-red-400 text-sm mb-2">{error}</p>
                                )}

                                {displaySummary ? (
                                    <div className="prose prose-sm max-w-none text-foreground-secondary">
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm, remarkMath]}
                                            rehypePlugins={[rehypeKatex]}
                                        >
                                            {displaySummary}
                                        </ReactMarkdown>
                                    </div>
                                ) : !summarizing && (
                                    <p className="text-foreground-muted text-sm italic">
                                        Click &quot;Analyze with Gemini&quot; to generate an AI summary.
                                    </p>
                                )}

                                {summarizing && !displaySummary && (
                                    <div className="flex items-center gap-2 text-foreground-secondary text-sm">
                                        <div className="h-4 w-4 border-2 border-border-default border-t-accent rounded-full animate-spin" />
                                        Generating summary... This may take a minute.
                                    </div>
                                )}
                            </div>

                            {/* Actions */}
                            <div className="flex items-center gap-3">
                                <Link
                                    href={`/paper/${paper.db_id || paper.id}`}
                                    onClick={onClose}
                                    className="px-4 py-2 bg-surface-inset hover:bg-surface-card text-foreground-secondary text-sm font-medium rounded-xl transition-colors"
                                >
                                    Full Details
                                </Link>
                                <Link
                                    href={`/timeline?paper=${paper.db_id || paper.id}`}
                                    onClick={onClose}
                                    className="flex items-center gap-2 px-4 py-2 bg-surface-inset hover:bg-surface-card text-foreground-secondary text-sm font-medium rounded-xl transition-colors"
                                >
                                    <GitBranch className="h-4 w-4" />
                                    Timeline
                                </Link>
                                {paper.pdf_url && (
                                    <a
                                        href={paper.pdf_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-2 px-4 py-2 bg-surface-inset hover:bg-surface-card text-foreground-secondary text-sm font-medium rounded-xl transition-colors"
                                    >
                                        <ExternalLink className="h-4 w-4" />
                                        PDF
                                    </a>
                                )}
                            </div>

                            {/* Prev / Next navigation */}
                            <div className="flex items-center justify-between mt-6 pt-4 border-t border-border-default">
                                <button
                                    onClick={onPrev}
                                    disabled={!hasPrev}
                                    className="flex items-center gap-1 text-sm text-foreground-secondary hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                                >
                                    <ChevronLeft className="h-4 w-4" /> Previous
                                </button>
                                <span className="text-xs text-foreground-muted">Swipe or use arrows</span>
                                <button
                                    onClick={onNext}
                                    disabled={!hasNext}
                                    className="flex items-center gap-1 text-sm text-foreground-secondary hover:text-foreground disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                                >
                                    Next <ChevronRight className="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
