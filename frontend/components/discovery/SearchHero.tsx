"use client";

import { Search } from "lucide-react";
import RippleButton from "../RippleButton";
import HeroDecoration from "../HeroDecoration";

interface SearchHeroProps {
    query: string;
    setQuery: (q: string) => void;
    onSearch: (e?: React.FormEvent) => void;
    loading: boolean;
}

export default function SearchHero({ query, setQuery, onSearch, loading }: SearchHeroProps) {
    return (
        <div className="relative overflow-hidden bg-surface-featured rounded-2xl px-12 py-16 text-center">
            <HeroDecoration variant="grid" />
            {/* Label */}
            <p
                className="text-[10px] font-bold uppercase text-on-featured/60 mb-4"
                style={{ letterSpacing: "var(--tracking-label)" }}
            >
                Discover
            </p>

            {/* Mixed-weight headline */}
            <h1 className="mb-3" style={{ fontFamily: "var(--font-display)" }}>
                <span className="text-3xl md:text-4xl font-extralight text-on-featured">
                    Search your{" "}
                </span>
                <span className="text-3xl md:text-4xl font-bold italic text-on-featured">
                    research library
                </span>
            </h1>

            {/* Subtitle */}
            <p
                className="text-sm text-on-featured/80 mb-8 italic"
                style={{ fontFamily: "var(--font-display)" }}
            >
                Explore thousands of AI papers with semantic search
            </p>

            {/* Search form */}
            <form
                onSubmit={onSearch}
                className="max-w-2xl mx-auto"
            >
                <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-foreground-muted" />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search papers (e.g. 'Transformers', 'RLHF')..."
                        autoFocus
                        className="w-full bg-white rounded-xl pl-12 pr-28 py-4 text-foreground shadow-warm focus:outline-none focus:ring-2 focus:ring-accent/50 text-base"
                        style={{ fontFamily: "var(--font-body)" }}
                    />
                    <RippleButton
                        type="submit"
                        disabled={loading}
                        className="absolute right-2 top-1/2 -translate-y-1/2 px-5 py-2.5 bg-accent hover:bg-accent-hover text-on-accent text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                    >
                        {loading ? "Searching..." : "Search"}
                    </RippleButton>
                </div>

                {/* Operator hints */}
                <div className="flex justify-center gap-4 mt-4">
                    {[
                        { label: "category:", example: "cs.AI" },
                        { label: "after:", example: "2024" },
                        { label: "author:", example: "Vaswani" },
                    ].map((hint) => (
                        <span
                            key={hint.label}
                            className="text-[10px] text-on-featured/50 font-mono"
                        >
                            <code className="text-on-featured/70">
                                {hint.label}{hint.example}
                            </code>
                        </span>
                    ))}
                </div>
            </form>
        </div>
    );
}
