"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { Paper } from "../../lib/api";
import { api } from "../../lib/api";
import { useLibrary } from "../../components/LibraryContext";
import { StaggerGrid, StaggerItem } from "../../components/animations/StaggerList";
import SearchHero from "../../components/discovery/SearchHero";
import SearchFilters from "../../components/discovery/SearchFilters";
import SearchResultCard from "../../components/discovery/SearchResultCard";
import { SearchNoResults, SearchError, SearchSkeleton } from "../../components/discovery/SearchEmptyStates";

function ResearchContent() {
    const { refreshLibrary } = useLibrary();
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();

    // Search state
    const [query, setQuery] = useState(searchParams.get("q") || "");
    const [papers, setPapers] = useState<Paper[]>([]);
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Filter state
    const [category, setCategory] = useState("");
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");
    const [sortBy, setSortBy] = useState("relevance");

    const hasActiveFilters = category !== "" || startDate !== "" || endDate !== "" || sortBy !== "relevance";

    const clearFilters = () => {
        setCategory("");
        setStartDate("");
        setEndDate("");
        setSortBy("relevance");
    };

    const handleSearch = async (e?: React.FormEvent, searchOverride?: string) => {
        if (e) e.preventDefault();
        const searchQuery = searchOverride || query;
        if (!searchQuery.trim()) return;

        setLoading(true);
        setHasSearched(true);
        setError(null);

        // Sync to URL
        if (!searchOverride) {
            const params = new URLSearchParams(searchParams);
            params.set("q", searchQuery);
            router.push(`${pathname}?${params.toString()}`);
        }

        try {
            // Map sort option to API sort parameter
            let apiSortBy = "relevance";
            if (sortBy === "date_desc" || sortBy === "date_asc") {
                apiSortBy = "date";
            }

            const data = await api.searchPapers(
                searchQuery,
                0,
                1000,
                apiSortBy,
                {
                    category: category || undefined,
                    startDate: startDate || undefined,
                    endDate: endDate || undefined,
                },
            );
            const transformed = data.map((p: any) => ({
                ...p,
                id: p.arxiv_id,
                db_id: p.id,
                categories: Array.isArray(p.categories)
                    ? p.categories
                    : [p.category || "cs.AI"],
            }));

            // Client-side sort for date direction
            if (sortBy === "date_asc") {
                transformed.sort(
                    (a: Paper, b: Paper) =>
                        new Date(a.published_date).getTime() -
                        new Date(b.published_date).getTime(),
                );
            }

            setPapers(transformed);
        } catch (err: unknown) {
            console.error(err);
            setError(err instanceof Error ? err.message : "Failed to execute search query.");
        } finally {
            setLoading(false);
        }
    };

    // Re-search when filters change (if we already have a query)
    useEffect(() => {
        if (hasSearched && query.trim()) {
            handleSearch(undefined, query);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [category, startDate, endDate, sortBy]);

    // Initial search if query in URL
    useEffect(() => {
        const urlQuery = searchParams.get("q");
        if (urlQuery && !hasSearched) {
            handleSearch(undefined, urlQuery);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams, hasSearched]);

    // Result count label
    const resultCountLabel = hasSearched && !loading && !error && papers.length > 0
        ? `${papers.length} result${papers.length !== 1 ? "s" : ""}`
        : null;

    return (
        <div className="bg-background px-12 pt-8 pb-24 space-y-10">
            {/* Search Hero */}
            <SearchHero
                query={query}
                setQuery={setQuery}
                onSearch={handleSearch}
                loading={loading}
            />

            {/* Filters — visible after first search */}
            {hasSearched && (
                <SearchFilters
                    category={category}
                    setCategory={setCategory}
                    startDate={startDate}
                    setStartDate={setStartDate}
                    endDate={endDate}
                    setEndDate={setEndDate}
                    sortBy={sortBy}
                    setSortBy={setSortBy}
                    onClear={clearFilters}
                    hasActiveFilters={hasActiveFilters}
                />
            )}

            {/* Result count */}
            {resultCountLabel && (
                <p
                    className="text-[10px] font-bold uppercase text-foreground-muted"
                    style={{ letterSpacing: "var(--tracking-label)" }}
                >
                    {resultCountLabel}
                </p>
            )}

            {/* Results / States */}
            {loading ? (
                <SearchSkeleton count={6} />
            ) : error ? (
                <SearchError
                    errorMessage={error}
                    onRetry={() => handleSearch(undefined, query)}
                />
            ) : papers.length > 0 ? (
                <StaggerGrid className="grid grid-cols-2 lg:grid-cols-3 gap-6">
                    {papers.map((paper) => (
                        <StaggerItem key={paper.id}>
                            <SearchResultCard paper={paper} />
                        </StaggerItem>
                    ))}
                </StaggerGrid>
            ) : hasSearched ? (
                <SearchNoResults />
            ) : null}
        </div>
    );
}

export default function ResearchPage() {
    return (
        <Suspense
            fallback={
                <div className="bg-background px-12 pt-8 pb-24">
                    <div className="bg-surface-featured rounded-2xl px-12 py-16 text-center">
                        <div className="skeleton h-8 w-64 mx-auto mb-4 rounded" />
                        <div className="skeleton h-12 w-full max-w-2xl mx-auto rounded-xl" />
                    </div>
                </div>
            }
        >
            <ResearchContent />
        </Suspense>
    );
}
