"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { motion } from "framer-motion";
import {
    Bookmark,
    ExternalLink,
    Star,
    TrendingUp,
} from "lucide-react";

export interface TimelinePaperData {
    title: string;
    arxiv_id: string;
    published_date?: string | null;
    category?: string | null;
    citation_count: number;
    is_seminal: boolean;
    is_in_library?: boolean;
    is_ghost?: boolean;
}

function TimelineNodeComponent(
    { data, selected }: NodeProps & { data: TimelinePaperData },
) {
    const nodeData = data as unknown as TimelinePaperData;
    const category = nodeData.category || "cs.AI";
    const isSeminal = nodeData.is_seminal;
    const isInLibrary = nodeData.is_in_library;
    const isGhost = nodeData.is_ghost;
    const citationCount = nodeData.citation_count || 0;
    const isHighCitation = citationCount >= 10;

    const year = nodeData.published_date
        ? new Date(nodeData.published_date).getFullYear()
        : null;

    // Ghost node
    if (isGhost) {
        return (
            <div
                className={`
                    group relative px-4 py-3 rounded-xl
                    bg-transparent
                    border border-dashed border-[var(--color-foreground-muted)]/30
                    cursor-pointer hover:border-[var(--color-foreground-muted)]/50
                    transition-all duration-200
                `}
                style={{ minWidth: 160 }}
            >
                <Handle
                    type="target"
                    position={Position.Left}
                    className="!bg-[var(--color-foreground-muted)] !w-2 !h-2 !border-0"
                />
                <p
                    className="text-xs text-[var(--color-foreground-secondary)] leading-tight
                        mb-2 italic"
                >
                    {nodeData.title.length > 40
                        ? nodeData.title.substring(0, 37) + "..."
                        : nodeData.title}
                </p>
                <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-[var(--color-foreground-muted)]">
                        {nodeData.arxiv_id}
                    </span>
                </div>
                <Handle
                    type="source"
                    position={Position.Right}
                    className="!bg-[var(--color-foreground-muted)] !w-2 !h-2 !border-0"
                />
            </div>
        );
    }

    // Seminal node
    if (isSeminal) {
        const truncTitle = nodeData.title.length > 70
            ? nodeData.title.substring(0, 67) + "..."
            : nodeData.title;

        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className="scale-110"
            >
                <div
                    className={`
                        group relative w-[320px] p-8 rounded-xl
                        bg-[var(--color-surface-card)]
                        border-2 border-[var(--color-accent)]/40
                        ring-4 ring-[var(--color-accent)]/10
                        transition-all duration-200 cursor-pointer
                        ${selected
                            ? "ring-2 ring-[var(--color-accent)]/70"
                            : ""}
                        ${isInLibrary
                            ? "ring-1 ring-[var(--color-accent)]/30"
                            : ""}
                    `}
                    style={{
                        boxShadow:
                            "0 0 30px 2px rgba(196, 97, 74, 0.15)",
                    }}
                >
                    <Handle
                        type="target"
                        position={Position.Left}
                        className="!bg-[var(--color-accent)] !w-2.5 !h-2.5
                            !border-0"
                    />

                    {/* Library bookmark */}
                    {isInLibrary && (
                        <div className="absolute -top-1.5 -left-1.5">
                            <Bookmark
                                className="h-3.5 w-3.5 text-[var(--color-accent)]
                                    fill-[var(--color-accent)]"
                            />
                        </div>
                    )}

                    {/* Seminal label with pulsing dot */}
                    <div
                        className="flex items-center gap-2 mb-6"
                    >
                        <motion.div
                            className="w-2 h-2 rounded-full bg-[var(--color-accent)]"
                            animate={{
                                opacity: [1, 0.4, 1],
                                scale: [1, 0.85, 1],
                            }}
                            transition={{
                                duration: 2,
                                repeat: Infinity,
                                ease: "easeInOut",
                            }}
                        />
                        <div
                            className="flex items-center gap-1.5"
                        >
                            <Star
                                className="w-3 h-3 text-[var(--color-accent)]"
                            />
                            <span
                                className="text-[10px] font-bold
                                    text-[var(--color-accent)] uppercase
                                    tracking-widest"
                            >
                                Seminal Paper
                            </span>
                        </div>
                    </div>

                    {/* Title */}
                    <p
                        className="text-xl font-extrabold text-[var(--color-foreground)]
                            leading-tight mb-6"
                        style={{ fontFamily: "var(--font-display)" }}
                    >
                        {truncTitle}
                    </p>

                    {/* Meta line */}
                    <div
                        className="flex items-center gap-3"
                    >
                        {/* Category badge */}
                        <span
                            className="bg-[var(--color-surface-inset)] px-2 py-0.5
                                rounded text-[var(--color-foreground-secondary)]
                                font-medium tracking-tight
                                text-[11px]"
                        >
                            {category}
                        </span>

                        {year && (
                            <span
                                className="text-[var(--color-foreground-muted)]
                                    text-[11px]"
                            >
                                {year}
                            </span>
                        )}

                        {citationCount > 0 && (
                            <span
                                className="flex items-center gap-1
                                    text-[11px] text-[var(--color-foreground-muted)]"
                            >
                                <span
                                    className="inline-block w-1.5
                                        h-1.5 rounded-full
                                        bg-[var(--color-accent)]/60"
                                />
                                {citationCount} cit.
                            </span>
                        )}
                    </div>

                    <Handle
                        type="source"
                        position={Position.Right}
                        className="!bg-[var(--color-accent)] !w-2.5 !h-2.5
                            !border-0"
                    />
                </div>
            </motion.div>
        );
    }

    // High-impact or regular node
    const truncatedTitle = nodeData.title.length > 50
        ? nodeData.title.substring(0, 47) + "..."
        : nodeData.title;

    const borderClass = isHighCitation
        ? `border border-[var(--color-accent)]/30
            hover:border-[var(--color-accent)]`
        : `border border-[#D5CFC4]
            hover:border-[var(--color-accent)]/40`;

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className={`
                group relative px-4 py-3 rounded-xl
                bg-[var(--color-surface-card)]
                ${borderClass}
                transition-all duration-200 cursor-pointer
                ${selected
                    ? "ring-2 ring-[var(--color-accent)]/50 border-[var(--color-accent)]/40"
                    : ""}
                ${isInLibrary ? "ring-1 ring-[var(--color-accent)]/30" : ""}
            `}
            style={{
                minWidth: isHighCitation ? 220 : 180,
            }}
        >
            <Handle
                type="target"
                position={Position.Left}
                className="!bg-[var(--color-foreground-muted)] !w-2 !h-2 !border-0"
            />

            {/* Library bookmark */}
            {isInLibrary && (
                <div className="absolute -top-1.5 -left-1.5">
                    <Bookmark
                        className="h-3.5 w-3.5 text-[var(--color-accent)]
                            fill-[var(--color-accent)]"
                    />
                </div>
            )}

            {/* External link icon on hover */}
            <div
                className="absolute top-2 right-2 opacity-0
                    group-hover:opacity-100 transition-opacity
                    duration-200"
            >
                <ExternalLink
                    className="w-3.5 h-3.5 text-[var(--color-foreground-muted)]"
                />
            </div>

            {/* High impact label */}
            {isHighCitation && (
                <div className="flex items-center gap-1.5 mb-4">
                    <TrendingUp
                        className="w-3 h-3 text-[var(--color-accent)]"
                    />
                    <span
                        className="text-[10px] font-bold
                            text-[var(--color-accent)] uppercase
                            tracking-widest"
                    >
                        High Impact
                    </span>
                </div>
            )}

            {/* Title */}
            <p
                className={`
                    text-[var(--color-foreground)] leading-tight mb-6 pr-6
                    ${isHighCitation
                        ? "text-base font-bold"
                        : "text-xs font-medium"}
                `}
                style={
                    isHighCitation
                        ? { fontFamily: "var(--font-display)" }
                        : undefined
                }
            >
                {truncatedTitle}
            </p>

            {/* Meta */}
            <div
                className="flex items-center gap-3
                    text-[11px] text-[var(--color-foreground-muted)]"
            >
                {/* Category badge */}
                <span
                    className="bg-[var(--color-surface-inset)] px-2 py-0.5 rounded
                        font-medium tracking-tight text-[11px]
                        text-[var(--color-foreground-secondary)]"
                >
                    {category}
                </span>

                {year && (
                    <span className="font-mono">{year}</span>
                )}

                {citationCount > 0 && (
                    <span className="flex items-center gap-1">
                        <span
                            className="inline-block w-1.5 h-1.5
                                rounded-full bg-[var(--color-accent)]/60"
                        />
                        {citationCount} cit.
                    </span>
                )}
            </div>

            <Handle
                type="source"
                position={Position.Right}
                className="!bg-[var(--color-foreground-muted)] !w-2 !h-2 !border-0"
            />
        </motion.div>
    );
}

export default memo(TimelineNodeComponent);
