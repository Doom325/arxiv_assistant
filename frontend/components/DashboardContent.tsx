"use client";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useInView } from "react-intersection-observer";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { Paper } from "../lib/api";
import { SkeletonGrid, SkeletonList, SkeletonBentoGrid } from "./SkeletonCard";
import { api } from "../lib/api";
import ErrorBoundary from "./ErrorBoundary";
import { useKeyboardNav } from "../lib/useKeyboardNav";
import {
    parseDashboardSearchParams,
    serializeDashboardSearchParams,
    hasActiveDashboardFilters,
    shouldUseDashboardSearchApi,
    writeDashboardCacheIfEligible,
} from "../lib/navigation";

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

/** Parse an ISO date string into YYYY-MM-DD for grouping.
 *
 * The backend's ``published_date`` is a SQL date column (no time-of-day);
 * SQLAlchemy serialises it as ``YYYY-MM-DDT00:00:00`` with no timezone
 * suffix. ``new Date(naiveISO)`` parses that as LOCAL time, then
 * ``.toISOString()`` converts to UTC — for any user east of UTC (IST
 * +05:30, KST +09:00, etc.), this rolls every paper back one calendar
 * day, so May 1 papers appear bucketed under April 30. We side-step by
 * slicing the YYYY-MM-DD prefix directly — that's the date the paper
 * was actually published per the backend's date column.
 */
function toDateKey(dateStr: string | undefined): string {
    if (!dateStr) return "unknown";
    const m = dateStr.match(/^(\d{4}-\d{2}-\d{2})/);
    if (m) return m[1];
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return "unknown";
        return d.toISOString().slice(0, 10);
    } catch {
        return "unknown";
    }
}

/** YYYY-MM-DD in the user's local timezone (NOT UTC). Used for "today"
 * / "yesterday" comparisons against keys produced by toDateKey, which
 * are already calendar-day strings. */
function localDateKey(d: Date): string {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

/** Format a YYYY-MM-DD key into a human-readable label */
function formatDateLabel(key: string): string {
    if (key === "unknown") return "Unknown Date";
    // Parse YYYY-MM-DD via the explicit (year, month, day, hour) Date
    // constructor instead of string concat. The constructor treats the
    // arguments as local time unambiguously across engines, whereas
    // ``new Date(key + "T12:00:00")`` depends on string-parser behavior
    // (some engines treat naive ISO as UTC, which would render the
    // prior calendar day for users west of UTC).
    const m = key.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!m) return key;
    const [, y, mo, d] = m;
    const dt = new Date(+y, +mo - 1, +d, 12, 0, 0);

    const today = new Date();
    today.setHours(12, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const todayStr = localDateKey(today);
    const yesterdayStr = localDateKey(yesterday);

    const formatted = dt.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
    });

    if (key === todayStr) return `Today ${formatted}`;
    if (key === yesterdayStr) return `Yesterday ${formatted}`;
    return dt.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
    });
}

/** Check if a date key is today (in local time, matching toDateKey's
 * calendar-day semantics). */
function isToday(key: string): boolean {
    if (key === "unknown") return false;
    return key === localDateKey(new Date());
}

/* ── Component ──────────────────────────────────────── */

export default function DashboardContent() {
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const initialFilters = parseDashboardSearchParams(searchParams);
    const lastPushedQueryRef = useRef<string | null>(null);
    const searchParamsString = searchParams.toString();
    const latestSearchParamsStringRef = useRef(searchParamsString);
    const lastSyncedFilterKeyRef = useRef(serializeDashboardSearchParams(initialFilters));
    const isInitialLoadRef = useRef(true);

    /* ── Paper state ── */
    const [papers, setPapers] = useState<Paper[]>([]);
    const [loading, setLoading] = useState(true);
    const [hasMore, setHasMore] = useState(true);
    const [page, setPage] = useState(0);
    const [isMounted, setIsMounted] = useState(false);

    /* ── Filter state (initialized from URL searchParams) ── */
    const [selectedCategories, setSelectedCategories] = useState<string[]>(
        initialFilters.selectedCategories,
    );
    const [dateStart, setDateStart] = useState<string | null>(initialFilters.dateStart);
    const [dateEnd, setDateEnd] = useState<string | null>(initialFilters.dateEnd);
    const [searchQuery, setSearchQuery] = useState<string>(initialFilters.searchQuery);
    const [sortBy, setSortBy] = useState<string>(initialFilters.sortBy);
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
    const handlePeekByIndex = useCallback((index: number) => setPeekIndex(index), []);

    /* ── Infinite scroll ── */
    const { ref, inView } = useInView({
        threshold: 0,
        triggerOnce: false,
    });

    /* ── Item-level keyboard navigation (global chords & ? handled in AppShell) ── */
    const { focusedIndex } = useKeyboardNav({
        itemCount: papers.length,
        onPeek: handlePeekByIndex,
        enableChords: false,
        enableOverlayShortcut: false,
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
    }, []);

    /* ── Sync external URL searchParams navigation to filter state ── */
    useEffect(() => {
        latestSearchParamsStringRef.current = searchParamsString;
        if (
            lastPushedQueryRef.current !== null &&
            searchParamsString === lastPushedQueryRef.current
        ) {
            lastPushedQueryRef.current = null;
            return;
        }
        const next = parseDashboardSearchParams(searchParams);
        setSelectedCategories((prev) =>
            prev.join(",") === next.selectedCategories.join(",")
                ? prev
                : next.selectedCategories,
        );
        setDateStart((prev) => (prev === next.dateStart ? prev : next.dateStart));
        setDateEnd((prev) => (prev === next.dateEnd ? prev : next.dateEnd));
        setSearchQuery((prev) => (prev === next.searchQuery ? prev : next.searchQuery));
        setSortBy((prev) => (prev === next.sortBy ? prev : next.sortBy));
    }, [searchParams, searchParamsString]);

    /* ── Fetch papers ── */
    const fetchPapers = useCallback(async (pageNum: number, isRefresh = false) => {
        setLoading(true);
        try {
            const skip = pageNum * LIMIT;
            const categoryFilter = selectedCategories.length > 0 ? selectedCategories[0] : undefined;
            const filters = {
                category: categoryFilter,
                startDate: dateStart || undefined,
                endDate: dateEnd || undefined,
            };

            const trimmedQuery = searchQuery.trim();
            const data = shouldUseDashboardSearchApi(searchQuery)
                ? await api.searchPapers(trimmedQuery, skip, LIMIT, sortBy, filters)
                : await api.getPapers(skip, LIMIT, filters);

            if (!data || !Array.isArray(data)) {
                setHasMore(false);
                setLoading(false);
                return;
            }

            const transformed: Paper[] = data.map((p: Paper & { category?: string }) => ({
                ...p,
                id: p.arxiv_id || `paper-${p.id}`,
                db_id: p.db_id ?? (typeof p.id === "number" ? p.id : undefined),
                categories: Array.isArray(p.categories) ? p.categories : [p.category || "cs.AI"],
            }));

            setHasMore(data.length >= LIMIT);

            setPapers((prev) => {
                const next = isRefresh ? transformed : [...prev, ...transformed];
                if (typeof sessionStorage !== "undefined") {
                    writeDashboardCacheIfEligible(
                        sessionStorage,
                        { selectedCategories, dateStart, dateEnd, searchQuery, sortBy },
                        next,
                        pageNum,
                        data.length >= LIMIT,
                    );
                }
                return next;
            });
        } catch {
            // Network/API error handled by empty/retry UI
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
        if (!isMounted || isInitialLoadRef.current) return;

        const query = serializeDashboardSearchParams({
            selectedCategories,
            dateStart,
            dateEnd,
            searchQuery,
            sortBy,
        });
        if (query === lastSyncedFilterKeyRef.current) return;
        lastSyncedFilterKeyRef.current = query;

        if (query !== latestSearchParamsStringRef.current) {
            lastPushedQueryRef.current = query;
            latestSearchParamsStringRef.current = query;
            router.push(query ? `${pathname}?${query}` : pathname, { scroll: false });
        }

        // Reset and fetch
        setPage(0);
        setHasMore(true);
        fetchPapers(0, true);
    }, [
        selectedCategories,
        dateStart,
        dateEnd,
        searchQuery,
        sortBy,
        isMounted,
        fetchPapers,
        pathname,
        router,
    ]);

    /* ── Initial Load / State Restore (9.14 — REQ-D08) ── */
    useEffect(() => {
        if (!isMounted || !isInitialLoadRef.current) return;

        const savedPapers = sessionStorage.getItem("dashboard_papers");
        const savedPage = sessionStorage.getItem("dashboard_page");
        const savedHasMore = sessionStorage.getItem("dashboard_has_more");
        const savedScroll = sessionStorage.getItem("dashboard_scroll");
        const cachedAt = parseInt(sessionStorage.getItem("dashboard_cached_at") || "0");

        const CACHE_TTL_MS = 30 * 60 * 1000;
        const cacheIsFresh = cachedAt > 0 && Date.now() - cachedAt < CACHE_TTL_MS;
        const hasActiveFilters = hasActiveDashboardFilters({
            selectedCategories,
            dateStart,
            dateEnd,
            searchQuery,
            sortBy,
        });

        if (
            savedPapers &&
            cacheIsFresh &&
            !searchParams.toString() &&
            !hasActiveFilters
        ) {
            try {
                const parsed = JSON.parse(savedPapers);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    setPapers(parsed);
                    setPage(parseInt(savedPage || "0"));
                    setHasMore(savedHasMore === "true");
                    isInitialLoadRef.current = false;
                    setLoading(false);

                    setTimeout(() => {
                        window.scrollTo(0, parseInt(savedScroll || "0"));
                    }, 100);
                    return;
                }
            } catch {
                sessionStorage.clear();
            }
        }

        isInitialLoadRef.current = false;
        fetchPapers(0, true);
    }, [
        isMounted,
        fetchPapers,
        searchParams,
        selectedCategories,
        dateStart,
        dateEnd,
        searchQuery,
        sortBy,
    ]);

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
