"use client";

import Link from "next/link";
import { Calendar, Clock, ListPlus } from "lucide-react";
import React, { useState } from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Paper } from "../../lib/api";
import { useLibrary } from "../LibraryContext";
import BookmarkButton from "../BookmarkButton";
import { getCategoryColor, estimateReadingTime } from "../../lib/categoryColors";

interface SearchResultCardProps {
    paper: Paper;
}

export default function SearchResultCard({ paper }: SearchResultCardProps) {
    const { bookmarkedMap } = useLibrary();
    const paperLists = paper.db_id ? (bookmarkedMap[paper.db_id] || []) : [];
    const [queued, setQueued] = useState(false);

    const addToQueue = async (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            const apiBase = "/api";
            const res = await fetch(`${apiBase}/batch/queue/${paper.db_id || paper.id}`, {
                method: "POST",
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
            className="bg-surface-card rounded-2xl p-5 shadow-warm-sm cursor-pointer group h-full flex flex-col relative overflow-visible"
            whileHover={{ y: -4 }}
            whileTap={{ scale: 0.98 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
        >
            {/* Category accent bar */}
            <div
                className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-2xl"
                style={{ backgroundColor: catColor.accent }}
            />

            {/* Category chip + list badges */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 flex-wrap">
                    {paper.categories.slice(0, 3).map((cat) => {
                        const cc = getCategoryColor(cat);
                        return (
                            <span
                                key={cat}
                                className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase inline-flex items-center"
                                style={{
                                    letterSpacing: "var(--tracking-label)",
                                    backgroundColor: `${cc.accent}15`,
                                    color: cc.accent,
                                }}
                            >
                                {cat}
                            </span>
                        );
                    })}
                    {paperLists.map((list) => (
                        <span
                            key={list}
                            className="px-2 py-0.5 bg-accent/10 text-accent rounded-full text-[10px] font-medium uppercase"
                            style={{ letterSpacing: "var(--tracking-label)" }}
                        >
                            {list}
                        </span>
                    ))}
                </div>
                <div className="flex items-center gap-1">
                    <BookmarkButton paper={paper} />
                    {!queued ? (
                        <button
                            onClick={addToQueue}
                            className="p-1 rounded-full hover:bg-surface-inset transition-colors text-foreground-muted hover:text-accent"
                            title="Add to Reading Queue"
                        >
                            <ListPlus className="h-4 w-4" />
                        </button>
                    ) : (
                        <span className="p-1 text-accent" title="Added to queue">
                            <ListPlus className="h-4 w-4" />
                        </span>
                    )}
                </div>
            </div>

            {/* Title */}
            <Link href={`/paper/${paper.db_id || paper.id}`}>
                <h3 className="text-base font-semibold text-foreground mb-2 group-hover:text-accent transition-colors leading-snug">
                    {paper.title}
                </h3>
            </Link>

            {/* Abstract */}
            <div className="text-foreground-secondary text-sm line-clamp-3 flex-grow mb-3 leading-relaxed">
                <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                >
                    {paper.summary || "No AI summary available yet."}
                </ReactMarkdown>
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-2 text-foreground-muted mb-3">
                <Calendar className="h-3.5 w-3.5" />
                <span
                    className="text-[10px] uppercase font-medium"
                    style={{ letterSpacing: "var(--tracking-label)" }}
                    suppressHydrationWarning
                >
                    {paper.published_date
                        ? new Date(paper.published_date).toLocaleDateString()
                        : "Unknown Date"}
                </span>
                {readTime && (
                    <>
                        <span className="text-foreground-muted/50">·</span>
                        <Clock className="h-3 w-3" />
                        <span
                            className="text-[10px] uppercase font-medium"
                            style={{ letterSpacing: "var(--tracking-label)" }}
                        >
                            {readTime}
                        </span>
                    </>
                )}
            </div>

            {/* Footer links */}
            <div className="flex items-center justify-between pt-3 mt-auto" style={{ borderTop: "1px solid var(--color-surface-inset)" }}>
                <a
                    href={paper.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent hover:text-accent-hover text-sm font-medium flex items-center transition-colors"
                    onClick={(e) => e.stopPropagation()}
                >
                    Read PDF &rarr;
                </a>
                <Link
                    href={`/paper/${paper.db_id || paper.id}`}
                    className="text-foreground-muted hover:text-foreground-secondary text-sm flex items-center transition-colors"
                    onClick={(e) => e.stopPropagation()}
                >
                    Full Details &rarr;
                </Link>
            </div>
        </motion.div>
    );
}
