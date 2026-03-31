"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
    Sparkles,
    RefreshCw,
    Loader2,
    ChevronDown,
    ChevronUp,
    ChevronRight,
    SlidersHorizontal,
    X,
} from "lucide-react";
import { api, QueueItem, QueueStats } from "../../lib/api";
import QueueCard from "../../components/QueueCard";
import QuickPeekSheet from "../../components/QuickPeekSheet";
import QuickPreviewPanel from "@/components/queue/QuickPreviewPanel";
import QueueFAB from "@/components/queue/QueueFAB";
import AddPaperForm from "@/components/AddPaperForm";
import FeaturedStatBlock from "@/components/queue/FeaturedStatBlock";
import { toast } from "sonner";

type SourceFilter = string;
type StatusFilter = "all" | "unread" | "reading" | "read" | "skipped";
type SortField = "priority" | "published_date" | "added_at";
type SortDir = "desc" | "asc";
type GroupBy = "none" | "day" | "week" | "month";

const SOURCE_TABS: { id: string; label: string }[] = [
    { id: 'all', label: 'All Sources' },
    { id: 'arxiv', label: 'ArXiv' },
    { id: 'jstor', label: 'JSTOR' },
    { id: 'personal', label: 'Personal' },
];

const STATUS_TABS: { label: string; value: StatusFilter }[] = [
    { label: "All", value: "all" },
    { label: "Unread", value: "unread" },
    { label: "Reading", value: "reading" },
    { label: "Read", value: "read" },
    { label: "Skipped", value: "skipped" },
];

const SORT_OPTIONS: { id: string; label: string; field: SortField; dir: SortDir }[] = [
    { id: "priority-desc", label: "Priority (High → Low)", field: "priority", dir: "desc" },
    { id: "priority-asc", label: "Priority (Low → High)", field: "priority", dir: "asc" },
    { id: "published-desc", label: "Published (Newest)", field: "published_date", dir: "desc" },
    { id: "published-asc", label: "Published (Oldest)", field: "published_date", dir: "asc" },
    { id: "added-desc", label: "Added (Newest)", field: "added_at", dir: "desc" },
    { id: "added-asc", label: "Added (Oldest)", field: "added_at", dir: "asc" },
];

const GROUP_OPTIONS: { id: GroupBy; label: string }[] = [
    { id: "day", label: "Day" },
    { id: "week", label: "Week" },
    { id: "month", label: "Month" },
    { id: "none", label: "None" },
];

// ── Grouping helpers ─────────────────────────────────

function getGroupKey(item: QueueItem, groupBy: GroupBy): string {
    const raw = item.published_date;
    if (!raw) return "Unknown Date";
    const d = new Date(raw);
    if (isNaN(d.getTime())) return "Unknown Date";

    switch (groupBy) {
        case "day":
            return d.toLocaleDateString("en-US", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
            });
        case "week": {
            // ISO week start (Monday)
            const day = d.getDay();
            const mondayOffset = day === 0 ? -6 : 1 - day;
            const monday = new Date(d);
            monday.setDate(d.getDate() + mondayOffset);
            const sunday = new Date(monday);
            sunday.setDate(monday.getDate() + 6);
            const fmt = (dt: Date) =>
                dt.toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                });
            return `Week of ${fmt(monday)} – ${fmt(sunday)}, ${monday.getFullYear()}`;
        }
        case "month":
            return d.toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
            });
        default:
            return "";
    }
}

function groupItems(
    items: QueueItem[],
    groupBy: GroupBy,
): { key: string; items: QueueItem[] }[] {
    if (groupBy === "none") return [{ key: "", items }];

    const map = new Map<string, QueueItem[]>();
    for (const item of items) {
        const key = getGroupKey(item, groupBy);
        const arr = map.get(key);
        if (arr) {
            arr.push(item);
        } else {
            map.set(key, [item]);
        }
    }
    return Array.from(map.entries()).map(([key, items]) => ({
        key,
        items,
    }));
}

// ── Sorting helper ───────────────────────────────────

function sortItems(
    items: QueueItem[],
    field: SortField,
    dir: SortDir,
): QueueItem[] {
    const sorted = [...items];
    sorted.sort((a, b) => {
        let cmp = 0;
        switch (field) {
            case "priority":
                cmp = a.priority_score - b.priority_score;
                break;
            case "published_date": {
                const da = a.published_date
                    ? new Date(a.published_date).getTime()
                    : 0;
                const db = b.published_date
                    ? new Date(b.published_date).getTime()
                    : 0;
                cmp = da - db;
                break;
            }
            case "added_at": {
                const aa = a.added_at
                    ? new Date(a.added_at).getTime()
                    : 0;
                const ab = b.added_at
                    ? new Date(b.added_at).getTime()
                    : 0;
                cmp = aa - ab;
                break;
            }
        }
        return dir === "desc" ? -cmp : cmp;
    });
    return sorted;
}

// ── Main component ───────────────────────────────────

export default function QueuePage() {
    const router = useRouter();
    const [items, setItems] = useState<QueueItem[]>([]);
    const [stats, setStats] = useState<QueueStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [discovering, setDiscovering] = useState(false);
    const [rescoring, setRescoring] = useState(false);
    const [sourceFilter, setSourceFilter] = useState<SourceFilter>("all");
    const [statusFilter, setStatusFilter] = useState<StatusFilter>("unread");
    const [sortField, setSortField] = useState<SortField>("priority");
    const [sortDir, setSortDir] = useState<SortDir>("desc");
    const [groupBy, setGroupBy] = useState<GroupBy>("none");
    const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(
        new Set(),
    );
    const [showCompleted, setShowCompleted] = useState(false);
    const [peekPaper, setPeekPaper] = useState<QueueItem | null>(null);
    const [fabOpen, setFabOpen] = useState(false);
    const [focusedIndex, setFocusedIndex] = useState<number>(-1);

    // Controls row open/close state
    const [sortOpen, setSortOpen] = useState(false);
    const [groupOpen, setGroupOpen] = useState(false);
    const [filterOpen, setFilterOpen] = useState(false);

    // Advanced filter panel state (status multi-select + date range)
    const [statusFilters, setStatusFilters] = useState<Set<StatusFilter>>(new Set());
    const [dateFilterFrom, setDateFilterFrom] = useState("");
    const [dateFilterTo, setDateFilterTo] = useState("");

    const fetchData = useCallback(async () => {
        try {
            const filterStatus =
                statusFilter === "all" ? undefined : statusFilter;
            // TODO: pass provider param when backend supports provider-level filtering
            const filterProvider =
                sourceFilter === "all" ? undefined : sourceFilter;
            const [queueData, statsData] = await Promise.all([
                api.getQueue(filterStatus, 500, 0, filterProvider),
                api.getQueueStats(),
            ]);
            setItems(queueData);
            setStats(statsData);
        } catch (err) {
            console.error("Failed to fetch queue:", err);
        } finally {
            setLoading(false);
        }
    }, [statusFilter, sourceFilter]);

    useEffect(() => {
        setLoading(true);
        fetchData();
    }, [fetchData]);

    // Auto-group by date when sorting by published_date
    const handleSortChange = (optId: string) => {
        const opt = SORT_OPTIONS.find((o) => o.id === optId);
        if (!opt) return;
        setSortField(opt.field);
        setSortDir(opt.dir);
        setSortOpen(false);
        // Auto-set grouping when sorting by date
        if (opt.field === "published_date" && groupBy === "none") {
            setGroupBy("week");
        }
    };

    const toggleGroup = (key: string) => {
        setCollapsedGroups((prev) => {
            const next = new Set(prev);
            if (next.has(key)) next.delete(key);
            else next.add(key);
            return next;
        });
    };

    const handleDiscover = async () => {
        setDiscovering(true);
        try {
            const result = await api.discoverQueue(7);
            toast.success(`Found ${result.added} new papers for you`);
            await fetchData();
        } catch {
            toast.error("Discovery failed");
        } finally {
            setDiscovering(false);
        }
    };

    const handleRescore = async () => {
        setRescoring(true);
        try {
            const result = await api.rescoreQueue();
            toast.success(`Rescored ${result.rescored} papers`);
            await fetchData();
        } catch {
            toast.error("Failed to rescore queue");
        } finally {
            setRescoring(false);
        }
    };

    // Active vs completed split
    const activeItems = items.filter(
        (i) => i.read_status !== "read" && i.read_status !== "skipped",
    );
    const completedItems = items.filter(
        (i) => i.read_status === "read" || i.read_status === "skipped",
    );
    const rawShowItems = statusFilter === "all" ? activeItems : items;

    // Sort then group
    const sorted = useMemo(
        () => sortItems(rawShowItems, sortField, sortDir),
        [rawShowItems, sortField, sortDir],
    );
    const groups = useMemo(
        () => groupItems(sorted, groupBy),
        [sorted, groupBy],
    );

    // Keyboard j/k navigation (E-008)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) return;
            if (e.key === 'j' || e.key === 'ArrowDown') {
                e.preventDefault();
                setFocusedIndex(prev => Math.min(prev + 1, sorted.length - 1));
            } else if (e.key === 'k' || e.key === 'ArrowUp') {
                e.preventDefault();
                setFocusedIndex(prev => Math.max(prev - 1, 0));
            } else if (e.key === ' ' && focusedIndex >= 0) {
                e.preventDefault();
                setPeekPaper(sorted[focusedIndex]);
            } else if (e.key === 'Escape') {
                setFocusedIndex(-1);
                setPeekPaper(null);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [sorted, focusedIndex]);

    // Current sort option
    const currentSortOpt = SORT_OPTIONS.find(
        (o) => o.field === sortField && o.dir === sortDir,
    );
    const currentSortLabel = currentSortOpt?.label ?? "Priority (High → Low)";

    // Active filter count (non-default filter values)
    const activeFilterCount =
        statusFilters.size +
        (dateFilterFrom ? 1 : 0) +
        (dateFilterTo ? 1 : 0);

    const previewOpen = peekPaper !== null;

    // previewIndex for QuickPreviewPanel prev/next navigation
    const previewIndex = sorted.findIndex((item) => item.paper_id === peekPaper?.paper_id);
    const handlePreviewPrev = () => {
        if (previewIndex > 0) setPeekPaper(sorted[previewIndex - 1]);
    };
    const handlePreviewNext = () => {
        if (previewIndex < sorted.length - 1) setPeekPaper(sorted[previewIndex + 1]);
    };

    const handleMarkReading = async (paperId: number) => {
        try {
            await api.markReading(paperId);
            fetchData();
        } catch {
            toast.error("Failed to update status");
        }
    };

    // QueueCard calls api.removeFromQueue internally; this callback just refreshes the list
    const handleRemoveFromQueue = (_arxivId: string) => {
        fetchData();
    };

    // Derived hero header values
    const totalItems = items.length;
    // Count distinct category values across all queue items
    const clusterCount = useMemo(
        () => new Set(items.map((i) => i.category).filter(Boolean)).size,
        [items],
    );

    return (
        <div className="relative min-h-screen bg-background">
            {/* Main canvas — takes full width minus right gutter when preview is open */}
            <div className={`px-12 pt-8 pb-24 space-y-6 transition-all duration-300 ${previewOpen ? "mr-[400px]" : "mr-0"}`}>
                {/* Hero Header — Task 3.2 */}
                <div className="mb-2">
                    <h1 className="leading-tight">
                        <span
                            style={{ fontFamily: 'var(--font-display)' }}
                            className="block font-extralight text-3xl text-foreground"
                        >
                            Your Reading
                        </span>
                        <span
                            style={{ fontFamily: 'var(--font-display)' }}
                            className="block font-black italic text-5xl text-foreground"
                        >
                            Queue
                        </span>
                    </h1>
                </div>

                {/* Subtitle */}
                <p
                    style={{ fontFamily: 'var(--font-display)' }}
                    className="italic text-foreground-secondary text-sm mt-2 mb-8"
                >
                    Curating {totalItems} open investigations across {clusterCount} research clusters.
                </p>

                {/* CTA buttons */}
                <div className="flex gap-3 mb-8">
                    <button
                        onClick={handleRescore}
                        className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-surface-card shadow-warm-sm text-foreground-secondary text-sm font-medium hover:bg-surface-inset transition-colors"
                    >
                        <RefreshCw size={15} />
                        Recalculate Scores
                    </button>
                    <button
                        onClick={handleDiscover}
                        className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-accent text-on-accent text-sm font-medium hover:bg-accent-hover transition-colors shadow-warm-sm"
                    >
                        <Sparkles size={15} />
                        AI Scan
                    </button>
                </div>

                {/* Featured Stat Block */}
                <FeaturedStatBlock
                    featuredPaper={items[0] ?? null}
                    stats={stats}
                    onStartReading={(paper) => router.push(`/paper/${paper.arxiv_id}`)}
                />

                {/* Filters + Sort + Group row */}
                <div className="flex flex-col gap-3">
                    {/* Source tabs + status pills */}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                        <div className="flex gap-1 items-center">
                            {SOURCE_TABS.map((tab) => {
                                const isActive = sourceFilter === tab.id;
                                return (
                                    <button
                                        key={tab.id}
                                        onClick={() =>
                                            setSourceFilter(tab.id)
                                        }
                                        className={
                                            isActive
                                                ? "bg-accent text-on-accent rounded-full px-4 py-1.5 text-sm font-medium"
                                                : "text-foreground-muted rounded-full px-4 py-1.5 text-sm hover:text-foreground hover:bg-surface-inset transition-colors"
                                        }
                                    >
                                        {tab.label}
                                    </button>
                                );
                            })}
                        </div>

                        <div className="flex items-center gap-1.5 overflow-x-auto">
                            {STATUS_TABS.map((tab) => (
                                <button
                                    key={tab.value}
                                    onClick={() => setStatusFilter(tab.value)}
                                    className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors whitespace-nowrap ${
                                        statusFilter === tab.value
                                            ? "bg-accent/15 text-accent border border-accent/30"
                                            : "text-foreground-muted hover:text-foreground border border-transparent"
                                    }`}
                                >
                                    {tab.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Sort + Group + Filter controls row */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            {/* Sort dropdown */}
                            <div className="relative">
                                <button
                                    onClick={() => { setSortOpen(!sortOpen); setGroupOpen(false); }}
                                    className="flex items-center gap-1.5 text-sm text-foreground-secondary hover:text-foreground transition-colors"
                                >
                                    <span className="text-foreground-muted">Sort by:</span>
                                    <span className="text-accent font-medium">{currentSortLabel}</span>
                                    <ChevronDown size={14} className="text-foreground-muted" />
                                </button>
                                {sortOpen && (
                                    <div className="absolute top-full left-0 mt-1 bg-surface-card shadow-warm-lg rounded-xl py-1 z-20 min-w-[200px]">
                                        {SORT_OPTIONS.map((opt) => (
                                            <button
                                                key={opt.id}
                                                onClick={() => handleSortChange(opt.id)}
                                                className={`w-full text-left px-4 py-2 text-sm transition-colors
                                                    ${currentSortOpt?.id === opt.id
                                                        ? "text-accent font-medium"
                                                        : "text-foreground-secondary hover:bg-surface-inset hover:text-foreground"
                                                    }`}
                                            >
                                                {opt.label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Group dropdown */}
                            <div className="relative">
                                <button
                                    onClick={() => { setGroupOpen(!groupOpen); setSortOpen(false); }}
                                    className="flex items-center gap-1.5 text-sm text-foreground-secondary hover:text-foreground transition-colors"
                                >
                                    <span className="text-foreground-muted">Group by:</span>
                                    <span className="text-accent font-medium">
                                        {GROUP_OPTIONS.find((g) => g.id === groupBy)?.label ?? "Week"}
                                    </span>
                                    <ChevronDown size={14} className="text-foreground-muted" />
                                </button>
                                {groupOpen && (
                                    <div className="absolute top-full left-0 mt-1 bg-surface-card shadow-warm-lg rounded-xl py-1 z-20 min-w-[140px]">
                                        {GROUP_OPTIONS.map((opt) => (
                                            <button
                                                key={opt.id}
                                                onClick={() => { setGroupBy(opt.id); setGroupOpen(false); }}
                                                className={`w-full text-left px-4 py-2 text-sm transition-colors
                                                    ${groupBy === opt.id
                                                        ? "text-accent font-medium"
                                                        : "text-foreground-secondary hover:bg-surface-inset hover:text-foreground"
                                                    }`}
                                            >
                                                {opt.label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Filter button */}
                        <div>
                            <button
                                onClick={() => setFilterOpen(!filterOpen)}
                                className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-full transition-colors
                                    ${filterOpen
                                        ? "bg-accent text-on-accent"
                                        : "bg-surface-inset text-foreground-muted hover:text-foreground"
                                    }`}
                            >
                                <SlidersHorizontal size={14} />
                                Filters
                                {activeFilterCount > 0 && (
                                    <span className="bg-on-accent/20 text-on-accent rounded-full px-1.5 text-xs font-medium">
                                        {activeFilterCount}
                                    </span>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Advanced filter panel */}
                    {filterOpen && (
                        <div className="bg-surface-card shadow-warm-lg rounded-2xl p-6 mt-3">
                            <div className="flex items-center justify-between mb-5">
                                <span className="text-sm font-semibold text-foreground">Advanced Filters</span>
                                <button
                                    onClick={() => setFilterOpen(false)}
                                    className="text-foreground-muted hover:text-foreground transition-colors"
                                >
                                    <X size={16} />
                                </button>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                                {/* Status section */}
                                <div>
                                    <p className="text-xs font-semibold text-foreground-muted uppercase tracking-widest mb-3">Status</p>
                                    <div className="flex flex-col gap-2">
                                        {(["unread", "reading", "read", "skipped"] as StatusFilter[]).map((s) => (
                                            <label key={s} className="flex items-center gap-2 cursor-pointer group">
                                                <input
                                                    type="checkbox"
                                                    checked={statusFilters.has(s)}
                                                    onChange={() => {
                                                        setStatusFilters((prev) => {
                                                            const next = new Set(prev);
                                                            if (next.has(s)) next.delete(s);
                                                            else next.add(s);
                                                            return next;
                                                        });
                                                    }}
                                                    className="accent-[var(--color-accent)] w-3.5 h-3.5 rounded"
                                                />
                                                <span className="text-sm text-foreground-secondary group-hover:text-foreground transition-colors capitalize">
                                                    {s}
                                                </span>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                {/* Source section */}
                                <div>
                                    <p className="text-xs font-semibold text-foreground-muted uppercase tracking-widest mb-3">Source</p>
                                    <div className="flex flex-wrap gap-2">
                                        {SOURCE_TABS.filter((t) => t.id !== "all").map((tab) => (
                                            <button
                                                key={tab.id}
                                                onClick={() => setSourceFilter(sourceFilter === tab.id ? "all" : tab.id)}
                                                className={`px-3 py-1 rounded-full text-sm transition-colors
                                                    ${sourceFilter === tab.id
                                                        ? "bg-accent text-on-accent font-medium"
                                                        : "bg-surface-inset text-foreground-secondary hover:text-foreground"
                                                    }`}
                                            >
                                                {tab.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Date range section */}
                                <div>
                                    <p className="text-xs font-semibold text-foreground-muted uppercase tracking-widest mb-3">Date Range</p>
                                    <div className="flex flex-col gap-2">
                                        <div>
                                            <label className="text-xs text-foreground-muted mb-1 block">From</label>
                                            <input
                                                type="date"
                                                value={dateFilterFrom}
                                                onChange={(e) => setDateFilterFrom(e.target.value)}
                                                className="w-full bg-surface-inset text-foreground text-sm rounded-lg px-3 py-1.5 border-0 focus:outline-none focus:ring-1 focus:ring-accent/40"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-foreground-muted mb-1 block">To</label>
                                            <input
                                                type="date"
                                                value={dateFilterTo}
                                                onChange={(e) => setDateFilterTo(e.target.value)}
                                                className="w-full bg-surface-inset text-foreground text-sm rounded-lg px-3 py-1.5 border-0 focus:outline-none focus:ring-1 focus:ring-accent/40"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex items-center justify-between mt-6 pt-4 border-t border-surface-inset">
                                <button
                                    onClick={() => {
                                        setStatusFilters(new Set());
                                        setDateFilterFrom("");
                                        setDateFilterTo("");
                                        setSourceFilter("all");
                                    }}
                                    className="text-sm text-foreground-muted hover:text-foreground transition-colors"
                                >
                                    Clear All
                                </button>
                                <button
                                    onClick={() => setFilterOpen(false)}
                                    className="px-5 py-2 rounded-xl bg-accent text-on-accent text-sm font-medium hover:bg-accent-hover transition-colors"
                                >
                                    Apply
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Queue list */}
                {loading ? (
                    <div className="flex items-center justify-center py-16 bg-background">
                        <div className="h-6 w-6 rounded-full border-2 border-surface-inset border-t-accent animate-spin" />
                    </div>
                ) : sorted.length === 0 &&
                  (statusFilter !== "all" ||
                      completedItems.length === 0) ? (
                    <EmptyQueue
                        sourceFilter={sourceFilter}
                        onDiscover={handleDiscover}
                        discovering={discovering}
                    />
                ) : (
                    <div className="space-y-4">
                        {groups.map((group) => (
                            <DateGroup
                                key={group.key || "__flat"}
                                groupKey={group.key}
                                items={group.items}
                                collapsed={collapsedGroups.has(group.key)}
                                onToggle={() => toggleGroup(group.key)}
                                onStatusChange={fetchData}
                                onPeek={setPeekPaper}
                                onRemove={handleRemoveFromQueue}
                                focusedPaperId={focusedIndex >= 0 ? sorted[focusedIndex]?.paper_id ?? null : null}
                            />
                        ))}
                    </div>
                )}

                {/* Completed section */}
                {statusFilter === "all" && completedItems.length > 0 && (
                    <div className="bg-surface-card shadow-warm-sm rounded-2xl p-4 mt-2">
                        <button
                            onClick={() => setShowCompleted(!showCompleted)}
                            className="flex items-center gap-2 text-sm text-foreground-muted hover:text-foreground transition-colors mb-3"
                        >
                            {showCompleted ? (
                                <ChevronDown className="h-4 w-4" />
                            ) : (
                                <ChevronRight className="h-4 w-4" />
                            )}
                            <span>Completed ({completedItems.length})</span>
                        </button>
                        <AnimatePresence>
                            {showCompleted && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="grid grid-cols-2 gap-4 overflow-hidden"
                                >
                                    {completedItems.map((item) => (
                                        <QueueCard
                                            key={item.paper_id}
                                            item={item}
                                            onStatusChange={fetchData}
                                            onPeek={() => setPeekPaper(item)}
                                            onRemove={handleRemoveFromQueue}
                                        />
                                    ))}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )}

                {/* Pagination footer — Task 3.10 */}
                <div className="text-center py-12">
                    <button
                        onClick={handleDiscover}
                        style={{ fontFamily: "var(--font-display)" }}
                        className="italic text-foreground-muted text-sm hover:text-foreground-secondary transition-colors"
                    >
                        Discover more insights in the archive →
                    </button>
                </div>

                {/* FAB — Task 3.9 */}
                <QueueFAB onOpen={() => setFabOpen(true)} />
            </div>

            {/* Quick Preview Panel — Task 3.8.5 (desktop, ≥1024px) */}
            <QuickPreviewPanel
                paper={peekPaper}
                isOpen={peekPaper !== null}
                onClose={() => setPeekPaper(null)}
                onPrev={handlePreviewPrev}
                onNext={handlePreviewNext}
                hasPrev={previewIndex > 0}
                hasNext={previewIndex < sorted.length - 1}
                currentIndex={previewIndex >= 0 ? previewIndex : undefined}
                totalCount={sorted.length}
                onBeginReading={(paper) => {
                    handleMarkReading(paper.paper_id);
                    router.push(`/paper/${paper.arxiv_id}`);
                }}
            />

            {/* Peek sheet — Task 3.8.6: mobile fallback (hidden on lg+, handled by QuickPreviewPanel's isWide check) */}
            {peekPaper && (
                <QuickPeekSheet
                    paper={{
                        id: peekPaper.arxiv_id,
                        db_id: peekPaper.paper_id,
                        arxiv_id: peekPaper.arxiv_id,
                        title: peekPaper.title,
                        summary: peekPaper.summary || "",
                        published_date: peekPaper.published_date || "",
                        categories: [peekPaper.category],
                        pdf_url: peekPaper.pdf_url,
                        generated_summary:
                            peekPaper.generated_summary ?? undefined,
                    }}
                    onClose={() => setPeekPaper(null)}
                />
            )}

            {/* AddPaperForm modal — Task 3.9 */}
            {fabOpen && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 backdrop-blur-sm"
                    onClick={() => setFabOpen(false)}
                >
                    <div
                        className="bg-surface-card rounded-2xl shadow-warm-lg p-8 w-full max-w-md"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex items-center justify-between mb-6">
                            <h2
                                style={{ fontFamily: "var(--font-display)" }}
                                className="font-bold text-xl text-foreground"
                            >
                                Add Research Item
                            </h2>
                            <button
                                onClick={() => setFabOpen(false)}
                                className="text-foreground-muted hover:text-foreground"
                            >
                                <X size={20} />
                            </button>
                        </div>
                        <AddPaperForm />
                    </div>
                </div>
            )}
        </div>
    );
}

// ── Date group section ───────────────────────────────

function DateGroup({
    groupKey,
    items,
    collapsed,
    onToggle,
    onStatusChange,
    onPeek,
    onRemove,
    focusedPaperId,
}: {
    groupKey: string;
    items: QueueItem[];
    collapsed: boolean;
    onToggle: () => void;
    onStatusChange: () => void;
    onPeek: (item: QueueItem) => void;
    onRemove: (id: string) => void;
    focusedPaperId: number | null;
}) {
    // No grouping — render flat
    if (!groupKey) {
        return (
            <div className="grid grid-cols-2 gap-4">
                <AnimatePresence mode="popLayout">
                    {items.map((item) => (
                        <QueueCard
                            key={item.paper_id}
                            item={item}
                            onStatusChange={onStatusChange}
                            onPeek={() => onPeek(item)}
                            onRemove={onRemove}
                            isFocused={focusedPaperId === item.paper_id}
                        />
                    ))}
                </AnimatePresence>
            </div>
        );
    }

    return (
        <div>
            <div className="flex items-center gap-3 mb-4">
                {/* Thin warm rule */}
                <div className="h-px flex-1 bg-surface-inset" />
                {/* Label */}
                <span className="text-xs uppercase tracking-[0.2em] text-foreground-muted font-medium whitespace-nowrap">
                    {groupKey} <span className="text-foreground-muted/60 ml-2">{items.length}</span>
                </span>
                {/* Thin warm rule */}
                <div className="h-px flex-1 bg-surface-inset" />
                {/* Collapse toggle */}
                <button onClick={onToggle} className="text-foreground-muted hover:text-foreground transition-colors">
                    {collapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
                </button>
            </div>

            <AnimatePresence>
                {!collapsed && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="grid grid-cols-2 gap-4 overflow-hidden"
                    >
                        {items.map((item) => (
                            <QueueCard
                                key={item.paper_id}
                                item={item}
                                onStatusChange={onStatusChange}
                                onPeek={() => onPeek(item)}
                                onRemove={onRemove}
                                isFocused={focusedPaperId === item.paper_id}
                            />
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// ── Small components ─────────────────────────────────

function EmptyQueue({
    sourceFilter,
    onDiscover,
    discovering,
}: {
    sourceFilter: SourceFilter;
    onDiscover: () => void;
    discovering: boolean;
}) {
    return (
        <div className="flex flex-col items-center justify-center py-24 text-center">
            <h2
                style={{ fontFamily: "var(--font-display)" }}
                className="font-extralight text-3xl text-foreground mb-2"
            >
                {sourceFilter === "personal" ? "No personal papers in" : "Your queue is"}
            </h2>
            <h2
                style={{ fontFamily: "var(--font-display)" }}
                className="font-black italic text-4xl text-foreground mb-6"
            >
                {sourceFilter === "personal" ? "your queue." : "ready."}
            </h2>
            <p
                className="text-foreground-secondary text-sm mb-8 max-w-sm italic"
                style={{ fontFamily: "var(--font-display)" }}
            >
                {sourceFilter === "personal"
                    ? "Add personal papers to your library to see them here."
                    : "Run an AI scan to discover papers matched to your research interests."}
            </p>
            {sourceFilter !== "personal" && (
                <button
                    onClick={onDiscover}
                    disabled={discovering}
                    className="flex items-center gap-2 px-6 py-3 bg-accent text-on-accent rounded-2xl font-medium shadow-warm-sm hover:bg-accent-hover transition-colors disabled:opacity-50"
                >
                    {discovering ? (
                        <Loader2 size={16} className="animate-spin" />
                    ) : (
                        <Sparkles size={16} />
                    )}
                    {discovering ? "Scanning..." : "Discover Papers"}
                </button>
            )}
        </div>
    );
}
