"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import {
    Check,
    SkipForward,
    Clock,
    BookOpen,
    Sparkles,
    Bookmark,
    MoreVertical,
    ExternalLink,
    Eye,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { QueueItem, api } from "../lib/api";
import { getCategoryColor, getCategoryAccent, estimateReadingTime } from "../lib/categoryColors";
import { toast } from "sonner";

interface QueueCardProps {
    item: QueueItem;
    onStatusChange: () => void;
    onPeek?: () => void;
    isFocused?: boolean;
    onRemove?: (id: string) => void;
}

// ─── Priority badge (clickable — triggers popup) ───────────────────────────
function PriorityBadge({
    score,
    manualPriority,
    onClick,
}: {
    score: number;
    manualPriority?: number | null;
    onClick: () => void;
}) {
    let label: string;
    const effectiveLevel = manualPriority
        ? manualPriority >= 3
            ? "high"
            : manualPriority >= 2
              ? "med"
              : "low"
        : score >= 0.7
          ? "high"
          : score >= 0.4
            ? "med"
            : "low";

    label =
        effectiveLevel === "high"
            ? "HIGH"
            : effectiveLevel === "med"
              ? "MED"
              : "LOW";

    return (
        <button
            onClick={onClick}
            className="flex items-center gap-1 bg-surface-inset border border-accent/30 rounded-full px-2.5 py-0.5 text-foreground-secondary text-xs font-medium uppercase tracking-wider hover:border-accent/60 transition-colors cursor-pointer"
            title="Click to override priority"
        >
            {manualPriority && (
                <span className="w-1.5 h-1.5 rounded-full bg-accent inline-block" />
            )}
            {label}
        </button>
    );
}

// ─── Priority override popup ───────────────────────────────────────────────
function PriorityPopup({
    score,
    manualPriority,
    onSelect,
    onClose,
}: {
    score: number;
    manualPriority?: number | null;
    onSelect: (priority: number | null) => void;
    onClose: () => void;
}) {
    const scorePercent = Math.round(score * 100);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClick(e: MouseEvent) {
            if (ref.current && !ref.current.contains(e.target as Node)) {
                onClose();
            }
        }
        document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, [onClose]);

    const options: { label: string; value: number; dot: string }[] = [
        { label: "High", value: 3, dot: "bg-accent" },
        { label: "Medium", value: 2, dot: "bg-amber-400" },
        { label: "Low", value: 1, dot: "bg-foreground-muted" },
    ];

    return (
        <div
            ref={ref}
            className="absolute left-0 top-full mt-2 w-64 z-50 bg-surface-card shadow-warm-lg rounded-xl p-3"
        >
            {/* AI Score display */}
            <div className="mb-3 pb-3 border-b border-surface-inset">
                <p className="text-[10px] font-medium uppercase tracking-wider text-foreground-muted mb-1">
                    AI Score
                </p>
                <div className="flex items-baseline gap-2">
                    <span
                        className="text-2xl font-bold italic"
                        style={{ fontFamily: "var(--font-display)" }}
                    >
                        {scorePercent}
                    </span>
                    <span className="text-xs text-foreground-muted">/ 100</span>
                </div>
            </div>

            {/* Manual override options */}
            <p className="text-[10px] font-medium uppercase tracking-wider text-foreground-muted mb-2">
                Manual Override
            </p>
            <div className="space-y-0.5 mb-3">
                {options.map(({ label, value, dot }) => (
                    <button
                        key={value}
                        onClick={() => {
                            onSelect(manualPriority === value ? null : value);
                            onClose();
                        }}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                            manualPriority === value
                                ? "bg-surface-inset text-accent font-medium"
                                : "text-foreground hover:bg-surface-inset"
                        }`}
                    >
                        <span>{label}</span>
                        <span className={`w-2 h-2 rounded-full ${dot}`} />
                    </button>
                ))}
            </div>

            {/* Revert to automatic */}
            <button
                onClick={() => {
                    onSelect(null);
                    onClose();
                }}
                className="w-full py-2 border border-accent/30 rounded-lg text-[10px] uppercase tracking-widest font-bold text-accent hover:bg-accent/5 transition-colors"
            >
                Revert to Automatic
            </button>
        </div>
    );
}

// ─── Source type icon ──────────────────────────────────────────────────────
function SourceIcon({ source }: { source: string }) {
    if (source === "discovery") {
        return (
            <Sparkles
                size={14}
                className="text-foreground-muted flex-shrink-0 mt-0.5"
                aria-label="AI-discovered paper"
            />
        );
    }
    return (
        <Bookmark
            size={14}
            className="text-foreground-muted flex-shrink-0 mt-0.5"
            aria-label="Manually saved paper"
        />
    );
}

// ─── Overflow menu ─────────────────────────────────────────────────────────
function OverflowMenu({
    onRemove,
    onClose,
}: {
    onRemove: () => void;
    onClose: () => void;
}) {
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClick(e: MouseEvent) {
            if (ref.current && !ref.current.contains(e.target as Node)) {
                onClose();
            }
        }
        document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, [onClose]);

    return (
        <div
            ref={ref}
            className="absolute right-0 top-full mt-1 w-48 z-50 bg-surface-card shadow-warm-lg rounded-xl py-1"
        >
            <button
                onClick={() => {
                    onRemove();
                    onClose();
                }}
                className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-surface-inset transition-colors"
            >
                Remove from Queue
            </button>
        </div>
    );
}

// ─── Main QueueCard ────────────────────────────────────────────────────────
export default function QueueCard({
    item,
    onStatusChange,
    onPeek,
    isFocused = false,
    onRemove,
}: QueueCardProps) {
    const router = useRouter();
    const [isUpdating, setIsUpdating] = useState(false);
    const [priorityPopupOpen, setPriorityPopupOpen] = useState(false);
    const [overflowOpen, setOverflowOpen] = useState(false);

    const catColor = getCategoryColor(item.category || "cs.AI");
    const readTime = estimateReadingTime(item.summary);
    const scorePercent = Math.round(item.priority_score * 100);

    const handleAction = async (
        action: () => Promise<unknown>,
        successMsg: string,
    ) => {
        if (isUpdating) return;
        setIsUpdating(true);
        try {
            await action();
            toast.success(successMsg);
            onStatusChange();
        } catch (err: unknown) {
            const message =
                err instanceof Error ? err.message : "Action failed";
            toast.error(message);
        } finally {
            setIsUpdating(false);
        }
    };

    const handleMarkRead = () =>
        handleAction(() => api.markRead(item.paper_id), "Marked as read");
    const handleMarkSkipped = () =>
        handleAction(() => api.markSkipped(item.paper_id), "Skipped");
    const handleMarkReading = () =>
        handleAction(() => api.markReading(item.paper_id), "Marked as reading");
    const handleRemove = () =>
        handleAction(async () => {
            await api.removeFromQueue(item.paper_id);
            if (onRemove) onRemove(item.arxiv_id);
        }, "Removed from queue");
    const handlePriority = (priority: number | null) =>
        handleAction(
            () => api.setManualPriority(item.paper_id, priority),
            priority ? `Priority set to ${priority}` : "Priority reset to auto",
        );

    const publishedDate = item.published_date
        ? new Date(item.published_date).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
          })
        : "";

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className={`relative bg-surface-card rounded-2xl overflow-hidden transition-all shadow-warm-sm card-hover ${
                item.read_status === "skipped" ? "opacity-60" : ""
            } ${isFocused ? "focus-ring" : ""}`}
        >
            {/* Category accent strip — 3px wide, rounded left edge */}
            <div
                className="absolute top-0 left-0 w-[3px] h-full rounded-l-2xl"
                style={{ backgroundColor: getCategoryAccent(item.category || "cs.AI") }}
            />

            {/* Priority score fill bar */}
            <div
                className="absolute bottom-0 left-0 h-0.5 opacity-20"
                style={{
                    width: `${scorePercent}%`,
                    backgroundColor: "var(--color-accent)",
                }}
            />

            {/* Reading progress indicator */}
            {item.read_status === "reading" && (
                <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-surface-inset rounded-b-2xl overflow-hidden">
                    <div className="h-full bg-accent/60 rounded-full" style={{ width: '50%' }} />
                </div>
            )}
            {item.read_status === "read" && (
                <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-accent rounded-b-2xl" />
            )}

            {/* Overflow menu trigger — top-right */}
            <div className="absolute top-3 right-3 z-10">
                <button
                    onClick={() => setOverflowOpen((v) => !v)}
                    className="p-1 rounded-lg text-foreground-muted hover:text-foreground hover:bg-surface-inset transition-colors"
                    title="More options"
                    aria-label="More options"
                >
                    <MoreVertical size={15} />
                </button>
                {overflowOpen && (
                    <OverflowMenu
                        onRemove={handleRemove}
                        onClose={() => setOverflowOpen(false)}
                    />
                )}
            </div>

            <div className="pl-4 pr-10 py-3">
                {/* Header row: source icon + title */}
                <div className="flex items-start gap-2 mb-1.5">
                    <SourceIcon source={item.source} />
                    <button
                        onClick={onPeek}
                        className="flex-1 text-left text-sm font-medium text-foreground hover:text-accent transition-colors line-clamp-2 leading-snug"
                    >
                        {item.title}
                    </button>
                </div>

                {/* "Similar to" line for discovery papers */}
                {item.source === "discovery" && item.best_match_title && (
                    <p className="text-[11px] text-foreground-muted italic mb-1.5 ml-4 line-clamp-1">
                        Similar to: {item.best_match_title}
                        {item.best_match_score != null && (
                            <span className="ml-1 opacity-60">
                                ({Math.round(item.best_match_score * 100)}%)
                            </span>
                        )}
                    </p>
                )}

                {/* Meta line */}
                <div className="flex items-center gap-2 text-[11px] text-foreground-muted italic mb-2 ml-4">
                    <span
                        className="not-italic font-medium"
                        style={{ color: catColor.accent }}
                    >
                        {item.category}
                    </span>
                    <span className="not-italic">&middot;</span>
                    <span>{publishedDate}</span>
                    {readTime && (
                        <>
                            <span className="not-italic">&middot;</span>
                            <Clock className="h-3 w-3 not-italic" />
                            <span>{readTime}</span>
                        </>
                    )}
                    <span className="not-italic">&middot;</span>
                    <span className="not-italic font-medium text-foreground-secondary">
                        {scorePercent}%
                    </span>
                </div>

                {/* Action row */}
                <div className="flex items-center gap-1 flex-wrap">
                    {/* Read-status pills */}
                    {item.read_status !== "read" && (
                        <button
                            onClick={handleMarkRead}
                            disabled={isUpdating}
                            className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs transition-colors disabled:opacity-30 ${
                                item.read_status === "read"
                                    ? "bg-accent text-on-accent"
                                    : "bg-surface-inset text-foreground-muted hover:text-foreground"
                            }`}
                            title="Mark as read"
                        >
                            <Check className="h-3 w-3" />
                            <span>Read</span>
                        </button>
                    )}

                    {item.read_status === "unread" && (
                        <button
                            onClick={handleMarkReading}
                            disabled={isUpdating}
                            className="flex items-center gap-1 rounded-full px-3 py-1 text-xs bg-surface-inset text-foreground-muted hover:text-foreground transition-colors disabled:opacity-30"
                            title="Mark as reading"
                        >
                            <BookOpen className="h-3 w-3" />
                            <span>Reading</span>
                        </button>
                    )}

                    {item.read_status === "reading" && (
                        <button
                            onClick={handleMarkReading}
                            disabled={isUpdating}
                            className="flex items-center gap-1 rounded-full px-3 py-1 text-xs bg-accent text-on-accent transition-colors disabled:opacity-30"
                            title="Currently reading"
                        >
                            <BookOpen className="h-3 w-3" />
                            <span>Reading</span>
                        </button>
                    )}

                    {item.read_status !== "skipped" &&
                        item.read_status !== "read" && (
                            <button
                                onClick={handleMarkSkipped}
                                disabled={isUpdating}
                                className="flex items-center gap-1 rounded-full px-3 py-1 text-xs bg-surface-inset text-foreground-muted hover:text-foreground transition-colors disabled:opacity-30"
                                title="Skip"
                            >
                                <SkipForward className="h-3 w-3" />
                                <span>Skip</span>
                            </button>
                        )}

                    {/* Priority badge + popup */}
                    <div className="relative ml-auto flex items-center gap-2">
                        <PriorityBadge
                            score={item.priority_score}
                            manualPriority={item.manual_priority}
                            onClick={() =>
                                setPriorityPopupOpen((v) => !v)
                            }
                        />
                        {priorityPopupOpen && (
                            <PriorityPopup
                                score={item.priority_score}
                                manualPriority={item.manual_priority}
                                onSelect={handlePriority}
                                onClose={() => setPriorityPopupOpen(false)}
                            />
                        )}

                        {/* Open Details */}
                        <button
                            onClick={() =>
                                router.push(`/paper/${item.arxiv_id}`)
                            }
                            className="flex items-center gap-1 rounded-full px-3 py-1 text-xs border border-accent/40 text-accent hover:bg-accent/5 transition-colors"
                            title="Open paper details"
                        >
                            <ExternalLink className="h-3 w-3" />
                            <span>Details</span>
                        </button>

                        {/* Preview */}
                        <button
                            onClick={onPeek}
                            className="flex items-center gap-1 rounded-full px-3 py-1 text-xs bg-surface-inset text-foreground-secondary hover:text-foreground transition-colors"
                            title="Quick preview"
                        >
                            <Eye className="h-3 w-3" />
                            <span>Preview</span>
                        </button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
