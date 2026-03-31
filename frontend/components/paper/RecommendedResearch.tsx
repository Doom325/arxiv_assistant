"use client";

import Link from "next/link";
import { Lightbulb, Calendar, Clock } from "lucide-react";
import ErrorBoundary from "../ErrorBoundary";
import { Paper } from "../../lib/api";

interface RecommendedResearchProps {
  papers: Paper[];
}

function estimateReadingTime(summary?: string): string {
  if (!summary) return "5 min read";
  const words = summary.split(/\s+/).length;
  const minutes = Math.max(3, Math.ceil(words / 200));
  return `${minutes} min read`;
}

export default function RecommendedResearch({ papers }: RecommendedResearchProps) {
  if (papers.length === 0) return null;

  return (
    <section className="mt-20">
      {/* Section header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="bg-accent/15 rounded-lg p-1.5">
          <Lightbulb className="h-5 w-5 text-accent" />
        </div>
        <span className="text-[10px] uppercase tracking-widest font-bold text-foreground-muted">
          Recommended Research
        </span>
      </div>

      {/* Thin warm rule */}
      <div className="h-px bg-foreground-muted/15 mb-6" />

      {/* Cards grid */}
      <ErrorBoundary fallback={<div className="text-foreground-muted">Failed to load recommendations.</div>}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {papers.map((paper) => (
            <div
              key={paper.db_id ?? paper.arxiv_id}
              className="bg-surface-card rounded-xl p-5 shadow-warm-sm hover:shadow-warm transition-shadow"
            >
              {/* Category chip */}
              {paper.categories && paper.categories.length > 0 && (
                <span className="bg-surface-inset text-foreground-muted rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-wider inline-block mb-2">
                  {paper.categories[0]}
                </span>
              )}

              {/* Title */}
              <Link
                href={`/paper/${paper.arxiv_id}`}
                className="text-foreground font-medium hover:text-accent transition-colors block leading-snug mb-2"
              >
                {paper.title}
              </Link>

              {/* Date + reading time */}
              <div className="flex items-center gap-3 text-foreground-muted text-xs">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {new Date(paper.published_date).toLocaleDateString()}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {estimateReadingTime(paper.summary)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </ErrorBoundary>
    </section>
  );
}
