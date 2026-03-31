import Link from "next/link";
import { Calendar, Plus, Clock, TrendingUp, TrendingDown } from "lucide-react";
import React, { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { useLibrary } from "./LibraryContext";
import { Paper } from "../lib/api";
import BookmarkButton from "./BookmarkButton";
import { getCategoryColor, estimateReadingTime } from "../lib/categoryColors";
export type { Paper };

interface PaperCardProps {
    paper: Paper;
    isBookmarked?: boolean;
    onToggleBookmark?: (listName?: string) => void;
    onPeek?: () => void;
    categoryTrends?: Record<string, "up" | "down" | "flat">;
}

export default function PaperCard({ paper, onPeek, categoryTrends }: PaperCardProps) {
    const { bookmarkedMap } = useLibrary();
    const paperLists = paper.db_id ? (bookmarkedMap[paper.db_id] || []) : [];
    const [queued, setQueued] = useState(false);
    const hoverTimerRef = useRef<NodeJS.Timeout | null>(null);

    const handleMouseEnter = useCallback(() => {
        if (!onPeek) return;
        hoverTimerRef.current = setTimeout(() => onPeek(), 700);
    }, [onPeek]);

    const handleMouseLeave = useCallback(() => {
        if (hoverTimerRef.current) {
            clearTimeout(hoverTimerRef.current);
            hoverTimerRef.current = null;
        }
    }, []);

    const addToQueue = async (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            const apiBase = "/api";
            const res = await fetch(`${apiBase}/batch/queue/${paper.db_id || paper.id}`, {
                method: "POST"
            });
            if (res.ok) {
                setQueued(true);
            }
        } catch (err) {
            console.error("Queue error", err);
        }
    };
    const primaryCategory = paper.categories?.[0] || "cs.AI";
    const catColor = getCategoryColor(primaryCategory);
    const readTime = estimateReadingTime(paper.summary);

    return (
        <motion.div
            className="bg-surface-card border border-border-default glass-card rounded-2xl p-6 cursor-pointer group h-full flex flex-col relative overflow-visible"
            whileHover={{ y: -4, boxShadow: "0 20px 40px rgba(99, 102, 241, 0.08)" }}
            whileTap={{ scale: 0.97 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            {/* Category accent bar */}
            <div
                className="absolute left-0 top-0 bottom-0 w-[3px]"
                style={{ backgroundColor: catColor.accent }}
            />

            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2 text-foreground-secondary text-sm">
                    <Calendar className="h-4 w-4" />
                    <span suppressHydrationWarning>{paper.published_date ? new Date(paper.published_date).toLocaleDateString() : "Unknown Date"}</span>
                    {readTime && (
                        <>
                            <span className="text-foreground-muted">·</span>
                            <Clock className="h-3.5 w-3.5 text-foreground-muted" />
                            <span className="text-foreground-muted text-xs">{readTime}</span>
                        </>
                    )}
                </div>
                <div className="flex space-x-2 items-center">
                    {paper.categories.slice(0, 3).map(cat => {
                        const cc = getCategoryColor(cat);
                        const trend = categoryTrends?.[cat];
                        return (
                            <span key={cat} className={`px-2 py-1 ${cc.bg} ${cc.text} border ${cc.border} text-xs rounded-full inline-flex items-center gap-1`}>
                                {cat}
                                {trend === "up" && <TrendingUp className="h-3 w-3 text-emerald-400" />}
                                {trend === "down" && <TrendingDown className="h-3 w-3 text-red-400" />}
                            </span>
                        );
                    })}
                    {paperLists.map(list => (
                        <span key={list} className="px-2 py-1 bg-accent/15 text-accent text-xs rounded-full border border-accent/30">{list}</span>
                    ))}

                    <BookmarkButton paper={paper} />

                    {!paper.generated_summary && (
                        <button
                            onClick={addToQueue}
                            className={`p-1 rounded-full hover:bg-surface-inset transition-colors ${queued ? "text-green-500" : "text-foreground-muted"}`}
                            title="Add to Batch Queue"
                        >
                            <Plus className="h-5 w-5" />
                        </button>
                    )}
                </div>
            </div>

            <div
                onClick={() => onPeek?.()}
                className="block cursor-pointer"
            >
                <h3 className="text-xl font-semibold text-foreground mb-2 group-hover:text-accent transition-colors">
                    {paper.title}
                </h3>
            </div>

            <div className="text-foreground-secondary line-clamp-3 flex-grow mb-4 prose prose-p:m-0 prose-sm max-w-none">
                <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                >
                    {paper.summary || "No AI summary available yet."}
                </ReactMarkdown>
            </div>

            <div className="flex items-center justify-between mt-auto pt-4 border-t border-border-default">
                <a
                    href={paper.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent hover:text-accent/80 text-sm font-medium flex items-center"
                    onClick={(e) => e.stopPropagation()}
                >
                    Read PDF &rarr;
                </a>
                <Link
                    href={`/paper/${paper.db_id || paper.id}`}
                    className="text-foreground-muted hover:text-foreground-secondary text-sm flex items-center"
                    onClick={(e) => e.stopPropagation()}
                >
                    Full Details &rarr;
                </Link>
            </div>
        </motion.div>
    );
}
