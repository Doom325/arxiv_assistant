"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useInView } from "react-intersection-observer";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { Paper } from "../lib/api";
import { SkeletonGrid, SkeletonList, SkeletonBentoGrid } from "./SkeletonCard";
import { api } from "../lib/api";
import ErrorBoundary from "./ErrorBoundary";
import { useKeyboardNav } from "../lib/useKeyboardNav";
import ShortcutOverlay from "./ShortcutOverlay";
import { useLibrary } from "./LibraryContext";

// New dashboard components
import HeroLeadStory from "./dashboard/HeroLeadStory";
import ActivityStats from "./dashboard/ActivityStats";
import CategoryChart from "./dashboard/CategoryChart";
import DashboardFilterBar from "./dashboard/DashboardFilterBar";
import DashboardPaperCard from "./dashboard/DashboardPaperCard";
import DashboardDateGroup from "./dashboard/DashboardDateGroup";
import DashboardQuickPeek from "./dashboard/DashboardQuickPeek";
import { DashboardEmptyState, DashboardNoResults } from "./dashboard/DashboardEmptyStates";

/* ── Constants ──────────────────────────────────────── */

const CATEGORIES = [
    "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO",
    "cs.NE", "cs.MA", "cs.IR", "cs.SI", "cs.HC", "cs.CY",
];

const LIMIT = 20;
const ANALYTICS_CATEGORY = "cs.AI";

/* ── Helpers ────────────────────────────────────────── */

/** Parse an ISO date string into YYYY-MM-DD for grouping */
function toDateKey(dateStr: string | undefined): string {
    if (!dateStr) return "unknown";
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return "unknown";
        return d.toISOString().slice(0, 10);
    } catch {
        return "unknown";
    }
}

/** Format a YYYY-MM-DD key into a human-readable label */
function formatDateLabel(key: string): string {
    if (key === "unknown") return "Unknown Date";
    const d = new Date(key + "T12:00:00"); // noon to avoid timezone shift
    const today = new Date();
    today.setHours(12, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const dStr = d.toISOString().slice(0, 10);
    const todayStr = today.toISOString().slice(0, 10);
    const yesterdayStr = yesterday.toISOString().slice(0, 10);

    const formatted = d.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
    });

    if (dStr === todayStr) return `Today ${formatted}`;
    if (dStr === yesterdayStr) return `Yesterday ${formatted}`;
    return d.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
    });
}

/** Check if a date key is today */
function isToday(key: string): boolean {
    if (key === "unknown") return false;
    const today = new Date();
    return key === today.toISOString().slice(0, 10);
}

/* ── Component ──────────────────────────────────────── */

export default function DashboardContent() {
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const { bookmarkedMap, refreshLibrary } = useLibrary();

    /* ── Paper state ── */
    const [papers, setPapers] = useState<Paper[]>([]);
    const [loading, setLoading] = useState(true);
    const [hasMore, setHasMore] = useState(true);
    const [page, setPage] = useState(0);
    const [isInitialLoad, setIsInitialLoad] = useState(true);
    const [isMounted, setIsMounted] = useState(false);

    /* ── Filter state ── */
    const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
    const [dateStart, setDateStart] = useState<string | null>(null);
    const [dateEnd, setDateEnd] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [sortBy, setSortBy] = useState("relevance");
    const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

    /* ── Collapse state for date groups ── */
    const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());

    const toggleGroup = (date: string) => {
        setCollapsedGroups((prev) => {
            const next = new Set(prev);
            if (next.has(date)) {
                next.delete(date);
            } else {
                next.add(date);
            }
            return next;
        });
    };

    /* ── Analytics state ── */
    const [stats, setStats] = useState<{
        total_papers: number;
        today_count: number;
        yesterday_count: number;
        library_count: number;
        category_count: number;
    } | null>(null);
    const [sparklineData, setSparklineData] = useState<{ date: string; count: number }[]>([]);
    const [categoryData, setCategoryData] = useState<{ category: string; count: number }[]>([]);

    /* ── Quick-peek state ── */
    const [peekIndex, setPeekIndex] = useState<number>(-1);
    const peekPaper = peekIndex >= 0 && peekIndex < papers.length ? papers[peekIndex] : null;

    /* ── Infinite scroll ── */
    const { ref, inView } = useInView({
        threshold: 0,
        triggerOnce: false,
    });

    /* ── Keyboard navigation (9.11) ── */
    const { focusedIndex, showShortcuts, setShowShortcuts } = useKeyboardNav({
        itemCount: papers.length,
        onPeek: (index) => setPeekIndex(index),
    });

    // Derive focusedPaperId from focusedIndex
    const focusedPaperId = focusedIndex >= 0 && focusedIndex < papers.length
        ? papers[focusedIndex].arxiv_id
        : null;

    /* ── Grouped papers (memoized) ── */
    const groupedPapers = useMemo(() => {
        const groups: Record<string, Paper[]> = {};
        papers.forEach((paper) => {
            const key = toDateKey(paper.published_date);
            if (!groups[key]) groups[key] = [];
            groups[key].push(paper);
        });
        return groups;
    }, [papers]);

    // Flat list for peek prev/next
    const flatPapers = useMemo(() => Object.values(groupedPapers).flat(), [groupedPapers]);

    /* ── Library helpers ── */
    const isInLibrary = (arxivId: string): boolean => {
        // bookmarkedMap is keyed by db_id (number), check all entries
        const paper = papers.find((p) => p.arxiv_id === arxivId);
        if (!paper?.db_id) return false;
        return (bookmarkedMap[paper.db_id] ?? []).length > 0;
    };

    const handleBookmark = async (paper: Paper) => {
        if (!paper.db_id) return;
        const { addBookmark, removeBookmark } = await import("../lib/api");
        const currentLists = bookmarkedMap[paper.db_id] ?? [];
        try {
            if (currentLists.length > 0) {
                await removeBookmark(paper.db_id, currentLists[0] || "default");
            } else {
                await addBookmark(paper.db_id, "default");
            }
            await refreshLibrary();
        } catch (e) {
            console.error("Bookmark error", e);
        }
    };

    /* ── Peek navigation ── */
    const handlePeekPrev = () => setPeekIndex((prev) => Math.max(prev - 1, 0));
    const handlePeekNext = () => setPeekIndex((prev) => Math.min(prev + 1, papers.length - 1));

    /* ── viewMode persistence (9.12.4) ── */
    useEffect(() => {
        if (typeof window === "undefined") return;
        const saved = localStorage.getItem("dashboard_viewMode");
        if (saved === "grid" || saved === "list") {
            setViewMode(saved);
        }
    }, []);

    useEffect(() => {
        if (typeof window === "undefined") return;
        localStorage.setItem("dashboard_viewMode", viewMode);
    }, [viewMode]);

    /* ── Mount ── */
    useEffect(() => {
        setIsMounted(true);
        // Initialize filters from URL params after mount
        const cat = searchParams.get("category");
        if (cat) setSelectedCategories(cat.split(","));
        setDateStart(searchParams.get("start") || null);
        setDateEnd(searchParams.get("end") || null);
        setSearchQuery(searchParams.get("q") || "");
        setSortBy(searchParams.get("sort") || "relevance");
    }, []); // Only on mount

    /* ── Fetch papers ── */
    const fetchPapers = useCallback(async (pageNum: number, isRefresh = false) => {
        setLoading(true);
        try {
            const skip = pageNum * LIMIT;
            // Use first selected category for API filter (API takes single category)
            const categoryFilter = selectedCategories.length > 0 ? selectedCategories[0] : undefined;
            const filters = {
                category: categoryFilter,
                startDate: dateStart || undefined,
                endDate: dateEnd || undefined,
            };

            let data;
            if (searchQuery) {
                data = await api.searchPapers(searchQuery, skip, LIMIT, sortBy, filters);
            } else {
                data = await api.getPapers(skip, LIMIT, filters);
            }

            if (!data || !Array.isArray(data)) {
                setHasMore(false);
                setLoading(false);
                return;
            }

            const transformed = data.map((p: any) => ({
                ...p,
                id: p.arxiv_id || `paper-${p.id}`,
                db_id: p.id,
                categories: Array.isArray(p.categories) ? p.categories : [p.category || "cs.AI"],
            }));

            if (data.length < LIMIT) {
                setHasMore(false);
            } else {
                setHasMore(true);
            }

            setPapers((prev) => {
                const next = isRefresh ? transformed : [...prev, ...transformed];
                if (typeof sessionStorage !== "undefined") {
                    try {
                        sessionStorage.setItem("dashboard_papers", JSON.stringify(next));
                        sessionStorage.setItem("dashboard_page", pageNum.toString());
                        sessionStorage.setItem("dashboard_has_more", (data.length >= LIMIT).toString());
                    } catch (e) {
                        console.error("Storage error", e);
                    }
                }
                return next;
            });
        } catch (error) {
            console.error("Fetch error", error);
        } finally {
            setLoading(false);
        }
    }, [selectedCategories, dateStart, dateEnd, searchQuery, sortBy]);

    /* ── Infinite Scroll Hook ── */
    useEffect(() => {
        if (inView && hasMore && !loading && isMounted) {
            const nextPage = page + 1;
            setPage(nextPage);
            fetchPapers(nextPage);
        }
    }, [inView, hasMore, loading, page, fetchPapers, isMounted]);

    /* ── Sync filters to URL (9.14 — REQ-D14) ── */
    useEffect(() => {
        if (!isMounted || isInitialLoad) return;

        const params = new URLSearchParams();
        if (selectedCategories.length > 0) params.set("category", selectedCategories.join(","));
        if (dateStart) params.set("start", dateStart);
        if (dateEnd) params.set("end", dateEnd);
        if (searchQuery) params.set("q", searchQuery);
        if (sortBy !== "relevance") params.set("sort", sortBy);

        const query = params.toString();
        router.push(query ? `${pathname}?${query}` : pathname, { scroll: false });

        // Reset and fetch
        setPage(0);
        setHasMore(true);
        fetchPapers(0, true);
    }, [selectedCategories, dateStart, dateEnd, searchQuery, sortBy, isMounted]);

    /* ── Initial Load / State Restore (9.14 — REQ-D08) ── */
    useEffect(() => {
        if (!isMounted) return;

        const savedPapers = sessionStorage.getItem("dashboard_papers");
        const savedPage = sessionStorage.getItem("dashboard_page");
        const savedHasMore = sessionStorage.getItem("dashboard_has_more");
        const savedScroll = sessionStorage.getItem("dashboard_scroll");

        if (savedPapers && isInitialLoad && !searchParams.toString()) {
            try {
                const parsed = JSON.parse(savedPapers);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    setPapers(parsed);
                    setPage(parseInt(savedPage || "0"));
                    setHasMore(savedHasMore === "true");
                    setIsInitialLoad(false);
                    setLoading(false);

                    setTimeout(() => {
                        window.scrollTo(0, parseInt(savedScroll || "0"));
                    }, 100);
                    return;
                }
            } catch (e) {
                console.error("Restore failed", e);
                sessionStorage.clear();
            }
        }

        if (isInitialLoad) {
            setIsInitialLoad(false);
            fetchPapers(0, true);
        }
    }, [isMounted, isInitialLoad, fetchPapers, searchParams]);

    /* ── Scroll Persistence ── */
    useEffect(() => {
        if (!isMounted) return;
        const handleScroll = () => {
            sessionStorage.setItem("dashboard_scroll", window.scrollY.toString());
        };
        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, [isMounted]);

    /* ── Fetch analytics data for bento tiles (fault-tolerant) ── */
    useEffect(() => {
        if (!isMounted) return;
        Promise.allSettled([
            api.getAnalyticsSummaryStats(ANALYTICS_CATEGORY),
            api.getAnalyticsPapersOverTime("day", 14, ANALYTICS_CATEGORY),
            api.getAnalyticsCategoryDist(30, ANALYTICS_CATEGORY),
        ]).then(([statsResult, sparkResult, catResult]) => {
            if (statsResult.status === "fulfilled") setStats(statsResult.value);
            if (sparkResult.status === "fulfilled") setSparklineData(sparkResult.value);
            if (catResult.status === "fulfilled") setCategoryData(catResult.value);
        });
    }, [isMounted]);

    /* ── Handlers ── */
    const handleRefresh = () => {
        setPage(0);
        setHasMore(true);
        fetchPapers(0, true);
    };

    const handleResetFilters = () => {
        setSelectedCategories([]);
        setDateStart(null);
        setDateEnd(null);
        setSearchQuery("");
        setSortBy("relevance");
    };

    /* ── Pre-mount loading state ── */
    if (!isMounted) {
        return <div className="text-center text-foreground-muted py-24">Initializing Dashboard...</div>;
    }

    /* ── Derived: weekly delta and trend for ActivityStats ── */
    const weeklyDelta = stats ? stats.today_count - stats.yesterday_count : 0;
    const weeklyTrend: "up" | "down" | "flat" =
        weeklyDelta > 0 ? "up" : weeklyDelta < 0 ? "down" : "flat";

    /* ── Sorted date keys ── */
    const sortedDateKeys = Object.keys(groupedPapers).sort((a, b) => {
        if (a === "unknown") return 1;
        if (b === "unknown") return -1;
        return b.localeCompare(a); // newest first
    });

    return (
        <div className="bg-background space-y-12 px-12 pt-8 pb-24">
            {/* ── Hero Lead Story (full width) ── */}
            <section>
                <HeroLeadStory
                    paper={papers[0] ?? null}
                    onReadFull={(p) => router.push(`/paper/${p.db_id || p.id}`)}
                    onBookmark={handleBookmark}
                    isBookmarked={papers[0] ? isInLibrary(papers[0].arxiv_id) : false}
                />
            </section>

            {/* ── Stats + Category Chart row ── */}
            {papers.length > 0 && (
                <section className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Category chart: spans 2 cols on large screens */}
                    <div className="lg:col-span-2">
                        <CategoryChart
                            categoryData={categoryData ?? []}
                            dailyData={sparklineData ?? []}
                        />
                    </div>

                    {/* Stats sidebar: right column */}
                    <ActivityStats
                        totalPapers={stats?.total_papers ?? 0}
                        weeklyDelta={weeklyDelta}
                        weeklyTrend={weeklyTrend}
                        pulseScore={stats?.category_count ?? 0}
                    />
                </section>
            )}

            {/* ── Filter Bar (full width) ── */}
            <section>
                <DashboardFilterBar
                    categories={CATEGORIES}
                    selectedCategories={selectedCategories}
                    onCategoryChange={setSelectedCategories}
                    dateStart={dateStart}
                    dateEnd={dateEnd}
                    onDateChange={(s, e) => {
                        setDateStart(s);
                        setDateEnd(e);
                    }}
                    sortBy={sortBy}
                    onSortChange={setSortBy}
                    viewMode={viewMode}
                    onViewModeChange={setViewMode}
                    searchQuery={searchQuery}
                    onSearchChange={setSearchQuery}
                    onReset={handleResetFilters}
                />
            </section>

            {/* ── Paper Feed (date-grouped) ── */}
            {papers.length === 0 && loading ? (
                <>
                    <SkeletonBentoGrid />
                    {viewMode === "grid" ? <SkeletonGrid count={6} /> : <SkeletonList />}
                </>
            ) : (
                <ErrorBoundary>
                    <div className="space-y-10">
                        {sortedDateKeys.map((dateKey) => {
                            const groupPapers = groupedPapers[dateKey];
                            const todayGroup = isToday(dateKey);
                            return (
                                <DashboardDateGroup
                                    key={dateKey}
                                    label={formatDateLabel(dateKey)}
                                    itemCount={groupPapers.length}
                                    isCollapsed={collapsedGroups.has(dateKey)}
                                    onToggle={() => toggleGroup(dateKey)}
                                    badge={todayGroup ? `${groupPapers.length} new` : undefined}
                                >
                                    {/* 9.12: Grid vs List layout */}
                                    {viewMode === "grid" ? (
                                        <div
                                            className={
                                                todayGroup
                                                    ? "grid grid-cols-2 gap-6"
                                                    : "grid grid-cols-2 lg:grid-cols-3 gap-4"
                                            }
                                        >
                                            {groupPapers.map((paper) => (
                                                <DashboardPaperCard
                                                    key={paper.arxiv_id}
                                                    paper={paper}
                                                    variant={todayGroup ? "large" : "compact"}
                                                    onPreview={(p) => {
                                                        const idx = papers.indexOf(p);
                                                        setPeekIndex(idx >= 0 ? idx : 0);
                                                    }}
                                                    onBookmark={handleBookmark}
                                                    isBookmarked={isInLibrary(paper.arxiv_id)}
                                                    isFocused={focusedPaperId === paper.arxiv_id}
                                                />
                                            ))}
                                        </div>
                                    ) : (
                                        <div className="space-y-3">
                                            {groupPapers.map((paper) => (
                                                <DashboardPaperCard
                                                    key={paper.arxiv_id}
                                                    paper={paper}
                                                    variant="compact"
                                                    onPreview={(p) => {
                                                        const idx = papers.indexOf(p);
                                                        setPeekIndex(idx >= 0 ? idx : 0);
                                                    }}
                                                    onBookmark={handleBookmark}
                                                    isBookmarked={isInLibrary(paper.arxiv_id)}
                                                    isFocused={focusedPaperId === paper.arxiv_id}
                                                />
                                            ))}
                                        </div>
                                    )}
                                </DashboardDateGroup>
                            );
                        })}
                    </div>
                </ErrorBoundary>
            )}

            {/* ── Empty States ── */}
            {!loading && papers.length === 0 && !searchQuery && (
                <DashboardEmptyState onDiscover={handleRefresh} />
            )}
            {!loading && papers.length === 0 && searchQuery && (
                <DashboardNoResults onClearFilters={handleResetFilters} />
            )}

            {/* ── Infinite Scroll Trigger + Loading Indicator (9.13) ── */}
            {hasMore && papers.length > 0 && (
                <div ref={ref} className="flex justify-center py-8">
                    {loading ? (
                        <div className="text-center py-8">
                            <p
                                style={{ fontFamily: "var(--font-display)" }}
                                className="italic text-foreground-muted text-sm"
                            >
                                Fetching deeper archives...
                            </p>
                            <div className="mt-3 mx-auto w-48 h-1 bg-surface-inset rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-accent rounded-full animate-pulse"
                                    style={{ width: "60%" }}
                                />
                            </div>
                        </div>
                    ) : (
                        <div className="h-4" />
                    )}
                </div>
            )}

            {/* ── Keyboard Shortcuts Overlay ── */}
            <ShortcutOverlay open={showShortcuts} onClose={() => setShowShortcuts(false)} />

            {/* ── Dashboard Quick Peek (9.9.8 wiring) ── */}
            <DashboardQuickPeek
                paper={peekPaper}
                isOpen={peekPaper !== null}
                onClose={() => setPeekIndex(-1)}
                onPrev={handlePeekPrev}
                onNext={handlePeekNext}
                hasPrev={peekIndex > 0}
                hasNext={peekIndex < papers.length - 1}
                onReadFull={(p) => router.push(`/paper/${p.db_id || p.id}`)}
                prevTitle={peekIndex > 0 ? papers[peekIndex - 1]?.title : undefined}
                nextTitle={peekIndex < papers.length - 1 ? papers[peekIndex + 1]?.title : undefined}
            />
        </div>
    );
}
