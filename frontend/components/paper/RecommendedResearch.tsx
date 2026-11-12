"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { AlertCircle, Calendar, Clock, Lightbulb, RefreshCw, Sparkles } from "lucide-react";
import ErrorBoundary from "../ErrorBoundary";
import { Paper } from "../../lib/api";

export interface RecommendedResearchProps {
  papers: Paper[];
  isFinding?: boolean;
  hasSearchedOnDemand?: boolean;
  error?: string | null;
  onFindSimilar?: (force?: boolean) => void;
}

function estimateReadingTime(summary?: string): string {
  if (!summary) return "5 min read";
  const words = summary.split(/\s+/).length;
  const minutes = Math.max(3, Math.ceil(words / 200));
  return `${minutes} min read`;
}

function SpinnerIcon({ reducedMotion }: { reducedMotion: boolean }) {
  return (
    <motion.span
      aria-hidden="true"
      className="inline-flex items-center justify-center"
      animate={{ rotate: 360 }}
      transition={{
        repeat: Infinity,
        ease: "linear",
        duration: reducedMotion ? 6 : 1.2,
      }}
    >
      <RefreshCw className="h-4 w-4" />
    </motion.span>
  );
}

function RecommendedPaperCard({
  paper,
  reducedMotion,
}: {
  paper: Paper;
  reducedMotion: boolean;
}) {
  return (
    <motion.li
      initial={reducedMotion ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={reducedMotion ? undefined : { y: -2 }}
      transition={{ duration: 0.2 }}
      className="bg-surface-card rounded-xl p-5 shadow-warm-sm"
    >
      {paper.categories && paper.categories.length > 0 && (
        <span className="bg-surface-inset text-foreground-muted rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-wider inline-block mb-2">
          {paper.categories[0]}
        </span>
      )}
      <Link
        href={`/paper/${paper.arxiv_id}`}
        className="text-foreground font-medium hover:text-accent block leading-snug mb-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        {paper.title}
      </Link>
      <div className="flex items-center gap-3 text-foreground-muted text-xs">
        <span className="flex items-center gap-1">
          <Calendar aria-hidden="true" className="h-3 w-3" />
          {new Date(paper.published_date).toLocaleDateString()}
        </span>
        <span className="flex items-center gap-1">
          <Clock aria-hidden="true" className="h-3 w-3" />
          {estimateReadingTime(paper.summary)}
        </span>
      </div>
    </motion.li>
  );
}

function EmptyRecommendationsState({
  isFinding,
  hasSearchedOnDemand,
  reducedMotion,
  onFindSimilar,
}: {
  isFinding: boolean;
  hasSearchedOnDemand: boolean;
  reducedMotion: boolean;
  onFindSimilar?: (force?: boolean) => void;
}) {
  const message = isFinding
    ? "Generating embedding and searching your research library..."
    : hasSearchedOnDemand
      ? "No closely related papers were found in your local library yet."
      : "No precomputed recommendations yet. Search your library on demand to find related papers.";

  return (
    <div className="bg-surface-card rounded-2xl p-6 md:p-8 shadow-warm-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div className="space-y-1">
        {isFinding && <progress aria-label="Finding similar papers" className="sr-only" />}
        <p className="text-sm text-foreground-secondary">{message}</p>
      </div>
      {onFindSimilar && (
        <motion.button
          type="button"
          onClick={() => onFindSimilar(hasSearchedOnDemand)}
          disabled={isFinding}
          whileHover={reducedMotion || isFinding ? undefined : { scale: 1.02 }}
          whileTap={reducedMotion || isFinding ? undefined : { scale: 0.98 }}
          className="min-h-9 shrink-0 bg-accent text-on-accent rounded-full px-5 py-2 text-sm font-medium inline-flex items-center justify-center gap-2 shadow-warm-sm disabled:opacity-60 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          {isFinding ? (
            <>
              <SpinnerIcon reducedMotion={reducedMotion} />
              Finding Similar...
            </>
          ) : (
            <>
              <Sparkles aria-hidden="true" className="h-4 w-4" />
              {hasSearchedOnDemand ? "Search Again" : "Find Similar Papers"}
            </>
          )}
        </motion.button>
      )}
    </div>
  );
}

export function RecommendedResearch({
  papers,
  isFinding = false,
  hasSearchedOnDemand = false,
  error = null,
  onFindSimilar,
}: RecommendedResearchProps) {
  const reducedMotion = Boolean(useReducedMotion());

  if (papers.length === 0 && !onFindSimilar) return null;

  return (
    <section className="mt-20">
      <div className="flex items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="bg-accent/15 rounded-lg p-1.5">
            <Lightbulb aria-hidden="true" className="h-5 w-5 text-accent" />
          </div>
          <h2 className="text-[10px] uppercase tracking-widest font-bold text-foreground-muted">
            Recommended Research
          </h2>
        </div>

        {papers.length > 0 && onFindSimilar && (
          <motion.button
            type="button"
            onClick={() => onFindSimilar(true)}
            disabled={isFinding}
            whileHover={reducedMotion || isFinding ? undefined : { scale: 1.02 }}
            whileTap={reducedMotion || isFinding ? undefined : { scale: 0.98 }}
            className="min-h-9 bg-surface-card text-foreground-secondary hover:text-foreground rounded-full px-3.5 py-1.5 text-xs font-medium inline-flex items-center gap-1.5 shadow-warm-sm disabled:opacity-60 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            {isFinding ? (
              <>
                <progress aria-label="Refreshing similar papers" className="sr-only" />
                <SpinnerIcon reducedMotion={reducedMotion} />
                Refreshing...
              </>
            ) : (
              <>
                <RefreshCw aria-hidden="true" className="h-3.5 w-3.5" />
                Refresh Similar
              </>
            )}
          </motion.button>
        )}
      </div>

      <div className="h-px bg-foreground-muted/15 mb-6" />

      {error && (
        <div
          role="alert"
          className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-xs text-red-600 dark:text-red-400 flex items-center gap-2"
        >
          <AlertCircle aria-hidden="true" className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <ErrorBoundary fallback={<div className="text-foreground-muted">Failed to load recommendations.</div>}>
        {papers.length === 0 ? (
          <EmptyRecommendationsState
            isFinding={isFinding}
            hasSearchedOnDemand={hasSearchedOnDemand}
            reducedMotion={reducedMotion}
            onFindSimilar={onFindSimilar}
          />
        ) : (
          <ul role="list" className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {papers.map((item) => (
              <RecommendedPaperCard
                key={item.db_id ?? item.arxiv_id}
                paper={item}
                reducedMotion={reducedMotion}
              />
            ))}
          </ul>
        )}
      </ErrorBoundary>
    </section>
  );
}

export default RecommendedResearch;
