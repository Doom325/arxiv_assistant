"use client";

import { useState, useCallback, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
    Search,
    GitBranch,
    Loader2,
    SearchX,
    Library,
    Globe,
    Cpu,
    Brain,
    Dna,
    Info,
} from "lucide-react";
import { api, type TimelineResponse, type TimelineNode } from "../../lib/api";
import TimelineGraph from "../../components/TimelineGraph";
import TimelineDetailPanel from "../../components/TimelineDetailPanel";

export default function TimelinePage() {
    return (
        <Suspense
            fallback={
                <div className="flex items-center justify-center py-24">
                    <div className="flex items-center gap-3 text-[var(--color-foreground-muted)]">
                        <Loader2 className="h-5 w-5 animate-spin" />
                        <span className="text-sm font-[var(--font-body)]">Loading timeline...</span>
                    </div>
                </div>
            }
        >
            <TimelineContent />
        </Suspense>
    );
}

const SUGGESTIONS = [
    {
        icon: Cpu,
        title: "Retrieval Augmented Generation",
        description:
            "How RAG evolved from early retrieval systems to modern multi-hop reasoning pipelines.",
    },
    {
        icon: Brain,
        title: "Chain of Thought",
        description:
            "The progression of prompting strategies that unlock step-by-step reasoning in LLMs.",
    },
    {
        icon: Dna,
        title: "Vision Transformers",
        description:
            "From ViT to DINOv2 — tracing the transformer revolution in computer vision.",
    },
] as const;

function TimelineContent() {
    const searchParams = useSearchParams();
    const initialQuery = searchParams.get("q") || "";
    const paperIdParam = searchParams.get("paper");

    const [query, setQuery] = useState(initialQuery);
    const [loading, setLoading] = useState(false);
    const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
    const [selectedNode, setSelectedNode] = useState<TimelineNode | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [libraryOnly, setLibraryOnly] = useState(false);

    const handleSearch = useCallback(
        async (searchQuery?: string) => {
            const q = searchQuery || query;
            if (!q.trim()) return;

            setLoading(true);
            setError(null);
            setSelectedNode(null);

            try {
                const result = await api.getTimelineByTopic(
                    q.trim(),
                    50,
                    libraryOnly,
                );
                setTimeline(result);
            } catch (e) {
                console.error("Timeline search failed:", e);
                setError("Failed to load timeline. Try a different query.");
            } finally {
                setLoading(false);
            }
        },
        [query, libraryOnly],
    );

    const handlePaperTimeline = useCallback(async (paperId: number) => {
        setLoading(true);
        setError(null);
        setSelectedNode(null);

        try {
            const result = await api.getTimelineByPaper(paperId);
            setTimeline(result);
        } catch (e) {
            console.error("Timeline paper query failed:", e);
            setError("Failed to load timeline for this paper.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (paperIdParam) {
            handlePaperTimeline(Number(paperIdParam));
        } else if (initialQuery) {
            handleSearch(initialQuery);
        }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const handleNodeSelect = useCallback(
        (paperId: number) => {
            if (!timeline) return;
            const node = timeline.nodes.find((n) => n.paper_id === paperId);
            setSelectedNode(node || null);
        },
        [timeline],
    );

    const handleSuggestionClick = useCallback(
        (topic: string) => {
            setQuery(topic);
            handleSearch(topic);
        },
        [handleSearch],
    );

    const hasResults =
        !loading && !error && timeline && timeline.nodes.length > 0;
    const noResults =
        !loading && !error && timeline && timeline.nodes.length === 0;
    const showEmpty = !loading && !error && !timeline;

    return (
        <div className="-mx-8 -mt-16">
            {/* Search bar — sticky, warm card surface */}
            <div className="sticky top-0 z-30 bg-[var(--color-surface-card)]/95 backdrop-blur-xl border-b border-[#D5CFC4] px-8 py-3">
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleSearch();
                    }}
                    className="flex items-center gap-4 max-w-5xl mx-auto"
                >
                    <div className="relative flex-1">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-foreground-muted)]" />
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search a topic, paper title, or field..."
                            className="w-full rounded-full bg-[var(--color-surface-inset)] border border-[#D5CFC4] py-2.5 pl-12 pr-24 text-sm text-[var(--color-foreground)] placeholder:text-[var(--color-foreground-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]/50"
                        />
                        {/* Library toggle pill inside input */}
                        <button
                            type="button"
                            onClick={() => setLibraryOnly(!libraryOnly)}
                            className={`absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-semibold uppercase tracking-wider transition-colors ${
                                libraryOnly
                                    ? "bg-[var(--color-accent)]/15 text-[var(--color-accent)]"
                                    : "bg-[var(--color-surface-card)] hover:bg-[var(--color-surface-inset)] text-[var(--color-foreground-muted)]"
                            }`}
                            title={
                                libraryOnly
                                    ? "Showing library papers only"
                                    : "Showing all papers"
                            }
                        >
                            {libraryOnly ? (
                                <Library className="h-3 w-3" />
                            ) : (
                                <Globe className="h-3 w-3" />
                            )}
                            {libraryOnly ? "Library" : "All"}
                        </button>
                    </div>

                    {/* Search button */}
                    <button
                        type="submit"
                        disabled={loading || !query.trim()}
                        className="flex items-center gap-2 px-5 py-2.5 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white text-sm font-medium rounded-full transition-colors disabled:opacity-40 whitespace-nowrap"
                    >
                        {loading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Search className="h-4 w-4" />
                        )}
                        <span className="hidden sm:inline">Search</span>
                    </button>
                </form>
            </div>

            {/* Loading state */}
            {loading && (
                <div className="flex items-center justify-center py-32 relative">
                    <div className="flex items-center gap-3 text-[var(--color-foreground-secondary)] relative z-10">
                        <Loader2 className="h-5 w-5 animate-spin text-[var(--color-accent)]" />
                        <span className="text-sm">Building timeline...</span>
                    </div>
                </div>
            )}

            {/* Error state */}
            {error && !loading && (
                <div className="flex items-center justify-center py-24 px-8">
                    <div className="text-center bg-[var(--color-surface-card)] rounded-xl p-16 max-w-md w-full shadow-warm border border-[#D5CFC4]">
                        <SearchX className="h-10 w-10 text-[var(--color-accent)]/70 mx-auto mb-4" />
                        <p className="text-[var(--color-accent)] text-sm">{error}</p>
                    </div>
                </div>
            )}

            {/* Empty state — hero with featured surface header + suggestion cards */}
            {showEmpty && (
                <div className="flex flex-col items-center justify-center relative min-h-[70vh]">
                    {/* Featured surface hero header */}
                    <div className="w-full bg-[var(--color-surface-featured)] px-8 py-20 flex flex-col items-center">
                        {/* Hero icon */}
                        <div className="relative mb-8">
                            <div className="relative w-28 h-28 md:w-36 md:h-36 border-2 border-white/20 rounded-full flex items-center justify-center">
                                <GitBranch className="h-12 w-12 md:h-16 md:w-16 text-white/80" />
                            </div>
                        </div>

                        {/* Title */}
                        <h1 className="font-[var(--font-display)] font-bold text-4xl md:text-5xl tracking-tight text-[var(--color-on-featured)] text-center mb-4">
                            Explore the{" "}
                            <span className="text-[var(--color-accent)] italic">
                                research timeline
                            </span>
                        </h1>

                        {/* Subtitle */}
                        <p className="text-white/70 text-lg max-w-lg mx-auto leading-relaxed text-center">
                            Input a keyword, paper title, or academic field to
                            visualize the evolution of thought and identify
                            seminal breakthroughs.
                        </p>
                    </div>

                    {/* Suggestion cards — below hero, on page background */}
                    <div className="px-8 py-12 w-full flex flex-col items-center">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl w-full">
                            {SUGGESTIONS.map((s) => (
                                <button
                                    key={s.title}
                                    type="button"
                                    onClick={() => handleSuggestionClick(s.title)}
                                    className="p-6 rounded-2xl bg-[var(--color-surface-card)] border border-[#D5CFC4] shadow-warm-sm hover:shadow-warm transition-all duration-300 cursor-pointer text-left"
                                >
                                    <s.icon className="h-5 w-5 text-[var(--color-accent)] mb-3" />
                                    <h3 className="font-[var(--font-display)] font-bold text-sm text-[var(--color-foreground)] mb-1">
                                        {s.title}
                                    </h3>
                                    <p className="text-xs text-[var(--color-foreground-secondary)] leading-relaxed">
                                        {s.description}
                                    </p>
                                </button>
                            ))}
                        </div>

                        {/* Bottom hint */}
                        <div className="mt-10 flex items-center gap-2 text-[var(--color-foreground-muted)] text-xs uppercase tracking-widest">
                            <Info className="h-3 w-3" />
                            <span>Powered by citation graph analysis</span>
                        </div>
                    </div>
                </div>
            )}

            {/* No results */}
            {noResults && (
                <div className="flex items-center justify-center py-24 px-8">
                    <div className="text-center bg-[var(--color-surface-card)] rounded-xl p-16 max-w-md w-full shadow-warm border border-[#D5CFC4]">
                        <SearchX className="h-10 w-10 text-[var(--color-foreground-muted)] mx-auto mb-4" />
                        <h3 className="font-[var(--font-display)] font-bold text-lg text-[var(--color-foreground)] mb-2">
                            No papers found
                        </h3>
                        <p className="text-sm text-[var(--color-foreground-secondary)]">
                            Try a different query or broader topic.
                        </p>
                    </div>
                </div>
            )}

            {/* Timeline graph */}
            {hasResults && (
                <div className="px-8 py-6">
                    <TimelineGraph
                        data={timeline}
                        onNodeSelect={handleNodeSelect}
                    />
                    {selectedNode && (
                        <TimelineDetailPanel node={selectedNode} />
                    )}
                </div>
            )}
        </div>
    );
}
