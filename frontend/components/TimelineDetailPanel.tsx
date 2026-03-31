"use client";

import { useState } from "react";
import { ExternalLink, FileText, Download, Loader2 } from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";
import { api, type TimelineNode } from "../lib/api";
import BookmarkButton from "./BookmarkButton";

interface TimelineDetailPanelProps {
    node: TimelineNode;
}

export default function TimelineDetailPanel({ node }: TimelineDetailPanelProps) {
    const [importing, setImporting] = useState(false);

    const paperForBookmark = {
        id: node.arxiv_id,
        db_id: node.paper_id ?? undefined,
        arxiv_id: node.arxiv_id,
        title: node.title,
        summary: node.summary || undefined,
        published_date: node.published_date || "",
        categories: node.category ? [node.category] : [],
        pdf_url: `https://arxiv.org/pdf/${node.arxiv_id}.pdf`,
    };

    const authors = Array.isArray(node.authors)
        ? (node.authors as string[]).slice(0, 8)
        : [];

    const handleImport = async () => {
        if (!node.arxiv_id) return;
        setImporting(true);
        try {
            await api.addPaper(node.arxiv_id);
            toast.success(
                "Paper imported! It will appear after processing."
            );
        } catch {
            toast.error("Failed to import paper.");
        } finally {
            setImporting(false);
        }
    };

    return (
        <div
            className={
                "bg-[var(--color-surface-card)] "
                + "border-t border-[#D5CFC4] p-8 mt-4 rounded-2xl shadow-warm"
            }
        >
            <div className="max-w-7xl mx-auto flex gap-12 items-start">
                {/* Left Column */}
                <div className="flex-1 min-w-0">
                    {/* Chip row */}
                    <div className="flex items-center gap-3 mb-4">
                        {node.is_seminal && (
                            <span
                                className={
                                    "px-3 py-1 bg-[var(--color-accent)]/10 "
                                    + "text-[var(--color-accent)] text-[10px] "
                                    + "font-bold uppercase tracking-widest "
                                    + "rounded-full border border-[var(--color-accent)]/20"
                                }
                            >
                                Seminal Node Selected
                            </span>
                        )}
                        {node.category && (
                            <span
                                className={
                                    "px-3 py-1 bg-[var(--color-surface-inset)] "
                                    + "text-[var(--color-foreground-secondary)] text-[10px] "
                                    + "font-semibold tracking-wide "
                                    + "rounded-full"
                                }
                            >
                                {node.category}
                            </span>
                        )}
                        {node.citation_count > 0 && (
                            <span
                                className={
                                    "px-3 py-1 bg-[var(--color-surface-inset)] "
                                    + "text-[var(--color-foreground-secondary)] text-[10px] "
                                    + "font-semibold tracking-wide "
                                    + "rounded-full"
                                }
                            >
                                {node.citation_count} Citation
                                {node.citation_count !== 1 ? "s" : ""}
                            </span>
                        )}
                    </div>

                    {/* Title */}
                    <h3
                        className={
                            "font-[var(--font-display)] text-3xl font-extrabold "
                            + "text-[var(--color-foreground)] tracking-tight mb-4"
                        }
                    >
                        {node.title}
                    </h3>

                    {/* Abstract / Summary */}
                    {node.summary && (
                        <p
                            className={
                                "text-sm text-[var(--color-foreground-secondary)] "
                                + "leading-relaxed max-w-4xl "
                                + "line-clamp-3"
                            }
                        >
                            {node.summary}
                        </p>
                    )}
                </div>

                {/* Right Column */}
                <div className="min-w-[280px]">
                    {/* Authors */}
                    {authors.length > 0 && (
                        <div className="mb-6">
                            <span
                                className={
                                    "text-[10px] font-bold "
                                    + "text-[var(--color-foreground-muted)] uppercase "
                                    + "tracking-widest mb-1 block"
                                }
                            >
                                Authors
                            </span>
                            <span className="text-xs font-medium text-[var(--color-foreground)]">
                                {authors.join(", ")}
                            </span>
                        </div>
                    )}

                    {/* Action buttons */}
                    <div className="flex flex-col gap-2">
                        {/* Primary CTA */}
                        {node.is_ghost ? (
                            <button
                                onClick={handleImport}
                                disabled={importing}
                                className={
                                    "w-full bg-[var(--color-accent)] "
                                    + "text-white font-[var(--font-display)] "
                                    + "font-bold text-xs py-3 rounded-xl "
                                    + "flex items-center justify-center "
                                    + "gap-2 hover:bg-[var(--color-accent-hover)] "
                                    + "transition-all shadow-warm-sm "
                                    + "active:scale-95 "
                                    + "disabled:opacity-50"
                                }
                            >
                                {importing ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Download className="h-4 w-4" />
                                )}
                                {importing ? "Importing..." : "Import Paper"}
                            </button>
                        ) : (
                            <Link
                                href={`/paper/${node.paper_id}`}
                                className={
                                    "w-full bg-[var(--color-accent)] "
                                    + "text-white font-[var(--font-display)] "
                                    + "font-bold text-xs py-3 rounded-xl "
                                    + "flex items-center justify-center "
                                    + "gap-2 hover:bg-[var(--color-accent-hover)] "
                                    + "transition-all shadow-warm-sm "
                                    + "active:scale-95"
                                }
                            >
                                <FileText className="h-4 w-4" />
                                Full Details
                            </Link>
                        )}

                        {/* Secondary row */}
                        <div className="flex gap-2">
                            <a
                                href={
                                    `https://arxiv.org/abs/${node.arxiv_id}`
                                }
                                target="_blank"
                                rel="noopener noreferrer"
                                className={
                                    "flex-1 bg-[var(--color-surface-inset)] text-[var(--color-foreground)] "
                                    + "font-[var(--font-display)] font-bold "
                                    + "text-[10px] py-2.5 rounded-xl "
                                    + "border border-[#D5CFC4] "
                                    + "flex items-center justify-center "
                                    + "gap-2 hover:bg-[var(--color-surface-card)] "
                                    + "transition-all"
                                }
                            >
                                <ExternalLink className="h-3 w-3" />
                                arXiv
                            </a>
                            <div
                                className={
                                    "flex-1 bg-[var(--color-surface-inset)] "
                                    + "font-[var(--font-display)] font-bold "
                                    + "text-[10px] py-2.5 rounded-xl "
                                    + "border border-[var(--color-accent)]/10 "
                                    + "flex items-center justify-center "
                                    + "gap-2 hover:bg-[var(--color-accent)]/5 "
                                    + "transition-all"
                                }
                            >
                                <BookmarkButton paper={paperForBookmark} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
