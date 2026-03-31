"use client";

import { Sparkles } from "lucide-react";

/* ── DashboardEmptyState ──────────────────────────────────
   Shown when no papers exist in the feed at all.
   Editorial serif pattern matching queue's EmptyQueue.
   ──────────────────────────────────────────────────────── */

interface DashboardEmptyStateProps {
  onDiscover: () => void;
}

export function DashboardEmptyState({ onDiscover }: DashboardEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <h2
        style={{ fontFamily: "var(--font-display)" }}
        className="font-extralight text-3xl text-foreground mb-2"
      >
        Your research feed
      </h2>
      <h2
        style={{ fontFamily: "var(--font-display)" }}
        className="font-black italic text-4xl text-foreground mb-6"
      >
        awaits.
      </h2>
      <p
        className="text-foreground-secondary text-sm mb-8 max-w-sm italic"
        style={{ fontFamily: "var(--font-display)" }}
      >
        Start by running an AI scan to discover papers matched to your
        interests.
      </p>
      <button
        onClick={onDiscover}
        className="flex items-center gap-2 px-6 py-3 bg-accent text-on-accent rounded-2xl font-medium shadow-warm-sm hover:bg-accent-hover transition-colors"
      >
        <Sparkles size={16} />
        Discover Papers
      </button>
    </div>
  );
}

/* ── DashboardNoResults ───────────────────────────────────
   Shown when a search or filter returns zero papers.
   ──────────────────────────────────────────────────────── */

interface DashboardNoResultsProps {
  onClearFilters: () => void;
}

export function DashboardNoResults({
  onClearFilters,
}: DashboardNoResultsProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <h3
        style={{ fontFamily: "var(--font-display)" }}
        className="font-bold text-xl text-foreground mb-3"
      >
        No papers found
      </h3>
      <p className="text-foreground-secondary text-sm mb-6">
        Try adjusting your search or filters.
      </p>
      <button
        onClick={onClearFilters}
        className="text-accent text-sm font-medium hover:underline"
      >
        Clear all filters
      </button>
    </div>
  );
}
