"use client";

import Link from "next/link";
import { BookOpen, ExternalLink, Award } from "lucide-react";

interface CitationCardProps {
  rank: number;
  arxivId: string | null;
  title: string | null;
  count: number;
  resolvedId: string | null;
  category: string | null;
  authors: string[] | null;
}

export default function CitationCard({
  rank,
  arxivId,
  title,
  count,
  resolvedId,
  category,
  authors,
}: CitationCardProps) {
  return (
    <div className="group relative overflow-hidden bg-surface-card hover:bg-surface-inset rounded-2xl transition-all duration-300 shadow-warm-sm hover:shadow-warm">
      {/* Rank watermark */}
      <div className="absolute top-0 right-0 p-6 flex items-baseline gap-0.5 opacity-10 group-hover:opacity-30 transition-opacity">
        <span className="text-3xl font-black text-foreground-muted">#</span>
        <span className="text-5xl font-black text-foreground-muted tracking-tighter">
          {rank}
        </span>
      </div>

      <div className="p-6 md:p-8 flex flex-col md:flex-row gap-6 relative z-10">
        {/* Citation count circle */}
        <div className="flex-shrink-0 flex flex-col items-center justify-center w-20 h-20 bg-accent/10 rounded-2xl">
          <span className="text-2xl font-black text-accent leading-none">
            {count}
          </span>
          <span
            className="text-[10px] text-foreground-muted font-bold uppercase mt-1"
            style={{ letterSpacing: "0.08em" }}
          >
            Cites
          </span>
        </div>

        <div className="flex-grow min-w-0">
          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-2 mb-2">
            {arxivId && (
              <span
                className="px-2.5 py-0.5 bg-surface-inset text-foreground-muted text-[10px] font-bold rounded-lg uppercase"
                style={{ letterSpacing: "0.04em" }}
              >
                arXiv:{arxivId}
              </span>
            )}
            {!arxivId && (
              <span
                className="px-2.5 py-0.5 bg-surface-inset text-foreground-muted text-[10px] font-bold rounded-lg uppercase"
                style={{ letterSpacing: "0.04em" }}
              >
                External Source
              </span>
            )}
            {resolvedId && (
              <span className="px-2.5 py-0.5 bg-accent/10 text-accent text-[10px] font-bold rounded-lg uppercase flex items-center gap-1">
                <Award className="h-3 w-3" />
                In Library
              </span>
            )}
            {category && (
              <span
                className="px-2.5 py-0.5 bg-surface-inset text-foreground-secondary text-[10px] font-bold rounded-lg uppercase"
                style={{ letterSpacing: "0.04em" }}
              >
                {category}
              </span>
            )}
          </div>

          {/* Title */}
          <h3 className="font-display text-lg md:text-xl font-bold text-foreground mb-2 group-hover:text-accent transition-colors max-w-3xl leading-tight">
            {title || arxivId || "Untitled"}
          </h3>

          {/* Authors */}
          {authors && authors.length > 0 && (
            <p className="text-foreground-secondary text-sm mb-4 line-clamp-1 max-w-2xl">
              {authors.join(", ")}
            </p>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3">
            {resolvedId ? (
              <Link
                href={`/paper/${resolvedId}`}
                className="bg-accent hover:bg-accent-hover text-on-accent px-5 py-2 rounded-xl text-sm font-bold transition-all shadow-warm-sm flex items-center gap-2"
              >
                <BookOpen className="h-4 w-4" />
                Explore Paper
              </Link>
            ) : arxivId ? (
              <a
                href={`https://arxiv.org/abs/${arxivId}`}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-surface-inset hover:bg-surface-card text-foreground px-5 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                View on arXiv
              </a>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
