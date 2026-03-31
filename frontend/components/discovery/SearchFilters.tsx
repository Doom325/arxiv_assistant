"use client";

import { X } from "lucide-react";

// Hardcoded from categoryColorMap (E-S01 resolution)
const CATEGORIES = [
    "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO",
    "cs.NE", "cs.MA", "cs.IR", "cs.SI", "cs.HC",
    "cs.CY", "stat.ML",
];

const SORT_OPTIONS = [
    { value: "relevance", label: "Relevance" },
    { value: "date_desc", label: "Date: Newest" },
    { value: "date_asc", label: "Date: Oldest" },
];

interface SearchFiltersProps {
    category: string;
    setCategory: (c: string) => void;
    startDate: string;
    setStartDate: (d: string) => void;
    endDate: string;
    setEndDate: (d: string) => void;
    sortBy: string;
    setSortBy: (s: string) => void;
    onClear: () => void;
    hasActiveFilters: boolean;
}

export default function SearchFilters({
    category,
    setCategory,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    sortBy,
    setSortBy,
    onClear,
    hasActiveFilters,
}: SearchFiltersProps) {
    return (
        <div className="bg-surface-card rounded-2xl p-4 shadow-warm-sm">
            <div className="flex flex-wrap items-center gap-4">
                {/* Category filter */}
                <div className="flex items-center gap-2">
                    <label
                        className="text-[10px] font-bold uppercase text-foreground-muted"
                        style={{ letterSpacing: "var(--tracking-label)" }}
                    >
                        Category
                    </label>
                    <select
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        className="bg-surface-inset rounded-lg px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/30 appearance-none cursor-pointer"
                    >
                        <option value="">All</option>
                        {CATEGORIES.map((cat) => (
                            <option key={cat} value={cat}>
                                {cat}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Date range */}
                <div className="flex items-center gap-2">
                    <label
                        className="text-[10px] font-bold uppercase text-foreground-muted"
                        style={{ letterSpacing: "var(--tracking-label)" }}
                    >
                        From
                    </label>
                    <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="bg-surface-inset rounded-lg px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/30"
                    />
                </div>

                <div className="flex items-center gap-2">
                    <label
                        className="text-[10px] font-bold uppercase text-foreground-muted"
                        style={{ letterSpacing: "var(--tracking-label)" }}
                    >
                        To
                    </label>
                    <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="bg-surface-inset rounded-lg px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/30"
                    />
                </div>

                {/* Sort */}
                <div className="flex items-center gap-2 ml-auto">
                    <label
                        className="text-[10px] font-bold uppercase text-foreground-muted"
                        style={{ letterSpacing: "var(--tracking-label)" }}
                    >
                        Sort by
                    </label>
                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="bg-surface-inset rounded-lg px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent/30 appearance-none cursor-pointer"
                    >
                        {SORT_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Clear button */}
                {hasActiveFilters && (
                    <button
                        onClick={onClear}
                        className="flex items-center gap-1 text-sm text-accent hover:text-accent-hover transition-colors"
                    >
                        <X className="h-3.5 w-3.5" />
                        Clear
                    </button>
                )}
            </div>
        </div>
    );
}
