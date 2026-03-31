"use client";

import { useEffect, useState } from "react";
import {
    getPatternOverview,
    getPatternPapers,
    CategoryOverview,
    PatternOverview,
    PaperPattern,
    PatternCount,
} from "../../lib/api";
import {
    Layers,
    Brain,
    Route,
    Wrench,
    Users,
    ClipboardCheck,
    Dumbbell,
    Zap,
    Building2,
    Globe,
    Activity,
    ChevronRight,
    ArrowLeft,
    Filter,
    Sparkles,
    BookOpen,
    ExternalLink,
    ChevronDown,
    ChevronUp,
} from "lucide-react";
import Link from "next/link";

// ─────────────────────────────────────────────────────
// Icon mapping for categories
// ─────────────────────────────────────────────────────
const CATEGORY_ICONS: Record<string, React.ElementType> = {
    agent_memory: Brain,
    agent_planning: Route,
    agent_tool_use: Wrench,
    multi_agent: Users,
    agent_evaluation: ClipboardCheck,
    training: Dumbbell,
    inference: Zap,
    architecture: Building2,
    world_models: Globe,
    state_space_models: Activity,
};

// ─────────────────────────────────────────────────────
// View state machine: overview → category → papers
// ─────────────────────────────────────────────────────
type ViewState =
    | { view: "overview" }
    | { view: "category"; category: CategoryOverview }
    | { view: "papers"; category: CategoryOverview; pattern: PatternCount };

export default function PatternsPage() {
    const [isMounted, setIsMounted] = useState(false);
    const [loading, setLoading] = useState(true);
    const [overview, setOverview] = useState<PatternOverview | null>(null);
    const [papers, setPapers] = useState<PaperPattern[]>([]);
    const [papersLoading, setPapersLoading] = useState(false);
    const [viewState, setViewState] = useState<ViewState>({ view: "overview" });

    // Filters
    const [agenticOnly, setAgenticOnly] = useState<boolean | undefined>(undefined);
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");

    // Expandable reasoning
    const [expandedReasoning, setExpandedReasoning] = useState<string | null>(null);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    useEffect(() => {
        if (isMounted) {
            loadOverview();
        }
    }, [agenticOnly, startDate, endDate, isMounted]);

    const loadOverview = async () => {
        setLoading(true);
        try {
            const data = await getPatternOverview({
                is_agentic: agenticOnly,
                startDate: startDate || undefined,
                endDate: endDate || undefined,
            });
            setOverview(data);
        } catch (e) {
            console.error("Error loading pattern overview:", e);
        } finally {
            setLoading(false);
        }
    };

    const loadPapers = async (category: string, pattern?: string) => {
        setPapersLoading(true);
        try {
            const data = await getPatternPapers({
                category,
                pattern,
                is_agentic: agenticOnly,
                startDate: startDate || undefined,
                endDate: endDate || undefined,
                limit: 100,
            });
            setPapers(data);
        } catch (e) {
            console.error("Error loading pattern papers:", e);
        } finally {
            setPapersLoading(false);
        }
    };

    const handleCategoryClick = (cat: CategoryOverview) => {
        setViewState({ view: "category", category: cat });
        loadPapers(cat.category);
    };

    const handlePatternClick = (cat: CategoryOverview, pat: PatternCount) => {
        setViewState({ view: "papers", category: cat, pattern: pat });
        loadPapers(cat.category, pat.name);
    };

    const handleBack = () => {
        if (viewState.view === "papers") {
            setViewState({ view: "category", category: viewState.category });
            loadPapers(viewState.category.category);
        } else {
            setViewState({ view: "overview" });
        }
    };

    if (!isMounted) return null;

    return (
        <div className="max-w-7xl mx-auto px-4 py-12">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-10">
                <div>
                    <div className="flex items-center gap-2 mb-3">
                        {viewState.view !== "overview" && (
                            <button
                                onClick={handleBack}
                                className="p-2 rounded-xl bg-surface-card hover:bg-surface-inset text-foreground-muted hover:text-foreground transition-all mr-2"
                            >
                                <ArrowLeft className="h-5 w-5" />
                            </button>
                        )}
                        <h1 className="text-4xl font-extrabold text-foreground tracking-tight flex items-center">
                            <Layers className="h-10 w-10 mr-4 text-accent" />
                            Pattern Library
                        </h1>
                    </div>
                    {/* Breadcrumb */}
                    <div className="flex items-center gap-2 text-sm text-foreground-muted ml-14">
                        <button
                            onClick={() => setViewState({ view: "overview" })}
                            className={`hover:text-foreground transition-colors ${viewState.view === "overview" ? "text-foreground font-medium" : ""}`}
                        >
                            All Categories
                        </button>
                        {(viewState.view === "category" || viewState.view === "papers") && (
                            <>
                                <ChevronRight className="h-4 w-4" />
                                <button
                                    onClick={() => handleCategoryClick(viewState.category)}
                                    className={`hover:text-foreground transition-colors ${viewState.view === "category" ? "text-foreground font-medium" : ""}`}
                                >
                                    {viewState.category.label}
                                </button>
                            </>
                        )}
                        {viewState.view === "papers" && (
                            <>
                                <ChevronRight className="h-4 w-4" />
                                <span className="text-foreground font-medium">{viewState.pattern.label}</span>
                            </>
                        )}
                    </div>
                </div>

                {/* Filters */}
                <div className="flex flex-wrap items-center gap-4 bg-surface-card p-4 rounded-2xl border border-border-default shadow-warm-sm">
                    <div className="flex items-center gap-2">
                        <Filter className="h-4 w-4 text-foreground-muted" />
                        <select
                            value={agenticOnly === undefined ? "" : agenticOnly ? "true" : "false"}
                            onChange={(e) => {
                                const v = e.target.value;
                                setAgenticOnly(v === "" ? undefined : v === "true");
                            }}
                            className="bg-surface-inset text-foreground px-3 py-2 rounded-xl border border-border-default focus:ring-2 focus:ring-accent/50 outline-none min-w-[140px] text-xs font-medium"
                        >
                            <option value="" className="bg-surface-card">All Papers</option>
                            <option value="true" className="bg-surface-card">Agentic Only</option>
                            <option value="false" className="bg-surface-card">Non-Agentic Only</option>
                        </select>
                    </div>
                    <div className="flex items-center gap-2">
                        <label className="text-[10px] font-bold text-foreground-muted uppercase tracking-wider">From</label>
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="bg-surface-inset text-foreground px-3 py-2 rounded-xl border border-border-default focus:ring-2 focus:ring-accent/50 outline-none text-xs"
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <label className="text-[10px] font-bold text-foreground-muted uppercase tracking-wider">To</label>
                        <input
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="bg-surface-inset text-foreground px-3 py-2 rounded-xl border border-border-default focus:ring-2 focus:ring-accent/50 outline-none text-xs"
                        />
                    </div>
                </div>
            </div>

            {/* Stats bar */}
            {overview && viewState.view === "overview" && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
                    <div className="bg-surface-card rounded-2xl border border-border-default p-5 text-center">
                        <p className="text-3xl font-black text-foreground">{overview.total_classified.toLocaleString()}</p>
                        <p className="text-xs text-foreground-muted font-bold uppercase tracking-wider mt-1">Papers Classified</p>
                    </div>
                    <div className="bg-surface-card rounded-2xl border border-border-default p-5 text-center">
                        <p className="text-3xl font-black text-accent">{overview.total_agentic.toLocaleString()}</p>
                        <p className="text-xs text-foreground-muted font-bold uppercase tracking-wider mt-1">Agentic Papers</p>
                    </div>
                    <div className="bg-surface-card rounded-2xl border border-border-default p-5 text-center">
                        <p className="text-3xl font-black text-emerald-400">
                            {overview.categories.filter(c => c.is_agentic_category).length}
                        </p>
                        <p className="text-xs text-foreground-muted font-bold uppercase tracking-wider mt-1">Agentic Categories</p>
                    </div>
                    <div className="bg-surface-card rounded-2xl border border-border-default p-5 text-center">
                        <p className="text-3xl font-black text-amber-400">{overview.categories.length}</p>
                        <p className="text-xs text-foreground-muted font-bold uppercase tracking-wider mt-1">Total Categories</p>
                    </div>
                </div>
            )}

            {/* Loading state */}
            {loading ? (
                <div className="flex flex-col items-center justify-center py-32 space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-accent"></div>
                    <p className="text-foreground-muted animate-pulse font-medium">Loading pattern taxonomy...</p>
                </div>
            ) : viewState.view === "overview" ? (
                /* ─────────────────────────────────── VIEW 1: Category Grid ─────────────────────────────────── */
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {overview?.categories.map((cat) => {
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        const IconComponent: any = CATEGORY_ICONS[cat.category] || Layers;
                        const isAgentic = cat.is_agentic_category;

                        return (
                            <button
                                key={cat.category}
                                onClick={() => handleCategoryClick(cat)}
                                className={`group text-left p-6 rounded-2xl border transition-all duration-300 hover:scale-[1.02] hover:shadow-warm-sm ${
                                    isAgentic
                                        ? "bg-accent/5 border-accent/20 hover:border-accent/40 hover:bg-accent/10"
                                        : "bg-surface-card border-border-default hover:border-border-hover hover:bg-surface-inset"
                                }`}
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className={`p-3 rounded-xl ${
                                        isAgentic ? "bg-accent/10" : "bg-surface-inset"
                                    }`}>
                                        <IconComponent className={`h-6 w-6 ${
                                            isAgentic ? "text-accent" : "text-foreground-secondary"
                                        }`} />
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        <span className={`text-2xl font-black ${
                                            isAgentic ? "text-accent" : "text-foreground-secondary"
                                        }`}>
                                            {cat.paper_count}
                                        </span>
                                        <span className="text-[10px] text-foreground-muted font-bold uppercase">papers</span>
                                    </div>
                                </div>

                                <h3 className="text-lg font-bold text-foreground mb-1 group-hover:text-accent transition-colors">
                                    {cat.label}
                                </h3>

                                {isAgentic && (
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-accent/10 text-accent text-[10px] font-bold rounded-md border border-accent/20 mb-3">
                                        <Sparkles className="h-3 w-3" />
                                        AGENTIC
                                    </span>
                                )}

                                {/* Sub-patterns as chips */}
                                <div className="flex flex-wrap gap-1.5 mt-3">
                                    {cat.patterns
                                        .filter(p => p.paper_count > 0)
                                        .sort((a, b) => b.paper_count - a.paper_count)
                                        .map((pat) => (
                                        <span
                                            key={pat.name}
                                            className={`px-2 py-1 text-[10px] font-medium rounded-md transition-colors ${
                                                isAgentic
                                                    ? "bg-accent/10 text-accent border border-accent/20"
                                                    : "bg-surface-inset text-foreground-secondary border border-border-default"
                                            }`}
                                        >
                                            {pat.label} ({pat.paper_count})
                                        </span>
                                    ))}
                                    {cat.patterns.filter(p => p.paper_count > 0).length === 0 && (
                                        <span className="text-[10px] text-foreground-muted italic">No papers yet</span>
                                    )}
                                </div>

                                <div className="flex items-center gap-1 mt-4 text-xs text-foreground-muted group-hover:text-accent transition-colors">
                                    <span>Explore patterns</span>
                                    <ChevronRight className="h-3.5 w-3.5" />
                                </div>
                            </button>
                        );
                    })}
                </div>
            ) : viewState.view === "category" ? (
                /* ─────────────────────────────────── VIEW 2: Category Detail ─────────────────────────────────── */
                <div className="space-y-4">
                    {/* Category header */}
                    <div className="bg-surface-card rounded-2xl border border-border-default p-6 mb-6">
                        <div className="flex items-center gap-4">
                            {(() => {
                                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                const IconComponent: any = CATEGORY_ICONS[viewState.category.category] || Layers;
                                return <IconComponent className="h-8 w-8 text-accent" />;
                            })()}
                            <div>
                                <h2 className="text-2xl font-bold text-foreground">{viewState.category.label}</h2>
                                <p className="text-foreground-secondary text-sm">
                                    {viewState.category.paper_count} papers classified in this category
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Pattern rows */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {viewState.category.patterns
                            .sort((a, b) => b.paper_count - a.paper_count)
                            .map((pat) => (
                            <button
                                key={pat.name}
                                onClick={() => handlePatternClick(viewState.category, pat)}
                                className="group text-left p-5 bg-surface-card hover:bg-surface-inset rounded-2xl border border-border-default hover:border-accent/30 transition-all duration-300"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-lg font-bold text-foreground group-hover:text-accent transition-colors">
                                            {pat.label}
                                        </h3>
                                        <p className="text-xs text-foreground-muted font-mono mt-1">{pat.name}</p>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="text-right">
                                            <span className="text-2xl font-black text-accent">{pat.paper_count}</span>
                                            <p className="text-[10px] text-foreground-muted font-bold uppercase">papers</p>
                                        </div>
                                        <ChevronRight className="h-5 w-5 text-foreground-muted group-hover:text-accent transition-colors" />
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>

                    {/* Papers list for this category (all patterns) */}
                    <div className="mt-8">
                        <h3 className="text-lg font-bold text-foreground mb-4">
                            All Papers in {viewState.category.label}
                        </h3>
                        {papersLoading ? (
                            <div className="flex items-center justify-center py-16">
                                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-accent"></div>
                            </div>
                        ) : (
                            <PaperList
                                papers={papers}
                                expandedReasoning={expandedReasoning}
                                onToggleReasoning={(id) =>
                                    setExpandedReasoning(expandedReasoning === id ? null : id)
                                }
                            />
                        )}
                    </div>
                </div>
            ) : (
                /* ─────────────────────────────────── VIEW 3: Papers for Pattern ─────────────────────────────────── */
                <div>
                    <div className="bg-surface-card rounded-2xl border border-border-default p-6 mb-6">
                        <h2 className="text-2xl font-bold text-foreground mb-1">{viewState.pattern.label}</h2>
                        <p className="text-foreground-secondary text-sm">
                            {viewState.pattern.paper_count} papers tagged with{" "}
                            <span className="font-mono text-accent">
                                {viewState.category.category}/{viewState.pattern.name}
                            </span>
                        </p>
                    </div>

                    {papersLoading ? (
                        <div className="flex items-center justify-center py-16">
                            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-accent"></div>
                        </div>
                    ) : (
                        <PaperList
                            papers={papers}
                            expandedReasoning={expandedReasoning}
                            onToggleReasoning={(id) =>
                                setExpandedReasoning(expandedReasoning === id ? null : id)
                            }
                        />
                    )}
                </div>
            )}
        </div>
    );
}

// ─────────────────────────────────────────────────────
// Paper List Sub-Component
// ─────────────────────────────────────────────────────
function PaperList({
    papers,
    expandedReasoning,
    onToggleReasoning,
}: {
    papers: PaperPattern[];
    expandedReasoning: string | null;
    onToggleReasoning: (id: string) => void;
}) {
    if (papers.length === 0) {
        return (
            <div className="text-center py-20 bg-surface-card rounded-3xl border border-dashed border-border-default">
                <Layers className="h-12 w-12 mx-auto text-foreground-muted mb-4" />
                <h3 className="text-lg font-bold text-foreground mb-2">No Papers Found</h3>
                <p className="text-foreground-muted text-sm">Try adjusting your filters or select a different pattern.</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 gap-4">
            {papers.map((paper) => (
                <div
                    key={paper.arxiv_id}
                    className="group bg-surface-card hover:bg-surface-inset rounded-2xl border border-border-default hover:border-border-hover transition-all duration-300 p-6"
                >
                    <div className="flex flex-col md:flex-row gap-4">
                        <div className="flex-grow">
                            {/* Badges row */}
                            <div className="flex flex-wrap items-center gap-2 mb-3">
                                <span className="px-2 py-0.5 bg-surface-inset text-foreground-secondary text-[10px] font-bold rounded-md border border-border-default font-mono">
                                    {paper.arxiv_id}
                                </span>
                                {paper.is_agentic && (
                                    <span className="px-2 py-0.5 bg-accent/10 text-accent text-[10px] font-bold rounded-md border border-accent/20 flex items-center gap-1">
                                        <Sparkles className="h-3 w-3" />
                                        Agentic
                                    </span>
                                )}
                                {paper.is_agentic === false && (
                                    <span className="px-2 py-0.5 bg-surface-inset text-foreground-muted text-[10px] font-bold rounded-md border border-border-default">
                                        Non-Agentic
                                    </span>
                                )}
                                {paper.category && (
                                    <span className="px-2 py-0.5 bg-surface-inset text-foreground-secondary text-[10px] font-bold rounded-md border border-border-default uppercase">
                                        {paper.category}
                                    </span>
                                )}
                                {paper.published_date && (
                                    <span className="text-[10px] text-foreground-muted">
                                        {new Date(paper.published_date).toLocaleDateString("en-US", {
                                            year: "numeric",
                                            month: "short",
                                            day: "numeric",
                                        })}
                                    </span>
                                )}
                            </div>

                            {/* Title */}
                            <Link
                                href={`/paper/${paper.arxiv_id}`}
                                className="text-lg font-bold text-foreground hover:text-accent transition-colors leading-tight block mb-3"
                            >
                                {paper.title}
                            </Link>

                            {/* Pattern badges with confidence */}
                            <div className="flex flex-wrap gap-2 mb-3">
                                {paper.patterns.map((p, i) => (
                                    <div
                                        key={i}
                                        className="flex items-center gap-1.5 px-2.5 py-1 bg-accent/5 border border-accent/20 rounded-lg"
                                    >
                                        <span className="text-[10px] font-mono text-accent">
                                            {p.category}/{p.name}
                                        </span>
                                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                            p.confidence >= 0.9
                                                ? "bg-emerald-500/10 text-emerald-400"
                                                : p.confidence >= 0.8
                                                ? "bg-amber-500/10 text-amber-400"
                                                : "bg-surface-inset text-foreground-secondary"
                                        }`}>
                                            {(p.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                ))}
                            </div>

                            {/* Evidence quotes */}
                            {paper.patterns.some(p => p.evidence) && (
                                <div className="space-y-1 mb-3">
                                    {paper.patterns
                                        .filter(p => p.evidence)
                                        .slice(0, 2)
                                        .map((p, i) => (
                                        <p key={i} className="text-xs text-foreground-muted italic line-clamp-1">
                                            &ldquo;{p.evidence}&rdquo;
                                        </p>
                                    ))}
                                </div>
                            )}

                            {/* Actions row */}
                            <div className="flex items-center gap-3">
                                <Link
                                    href={`/paper/${paper.arxiv_id}`}
                                    className="text-xs font-bold text-accent hover:text-accent/80 flex items-center gap-1 transition-colors"
                                >
                                    <BookOpen className="h-3.5 w-3.5" />
                                    View Paper
                                </Link>
                                <a
                                    href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs font-bold text-foreground-muted hover:text-foreground-secondary flex items-center gap-1 transition-colors"
                                >
                                    <ExternalLink className="h-3.5 w-3.5" />
                                    arXiv
                                </a>
                                {paper.reasoning && (
                                    <button
                                        onClick={() => onToggleReasoning(paper.arxiv_id)}
                                        className="text-xs font-bold text-foreground-muted hover:text-foreground-secondary flex items-center gap-1 transition-colors"
                                    >
                                        {expandedReasoning === paper.arxiv_id ? (
                                            <ChevronUp className="h-3.5 w-3.5" />
                                        ) : (
                                            <ChevronDown className="h-3.5 w-3.5" />
                                        )}
                                        CoT Reasoning
                                    </button>
                                )}
                            </div>

                            {/* Expandable reasoning */}
                            {expandedReasoning === paper.arxiv_id && paper.reasoning && (
                                <div className="mt-3 p-4 bg-surface-inset rounded-xl border border-border-default text-xs text-foreground-secondary leading-relaxed whitespace-pre-wrap font-mono">
                                    {paper.reasoning}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
