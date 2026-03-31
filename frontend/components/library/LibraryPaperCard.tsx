"use client";

import React from "react";
import Link from "next/link";
import { Clock, ListPlus } from "lucide-react";
import BookmarkButton from "@/components/BookmarkButton";
import { Paper } from "@/lib/api";
import { estimateReadingTime, getCategoryAccent } from "@/lib/categoryColors";

interface LibraryPaperCardProps {
  paper: Paper;
  listMemberships: string[];
  onAddToQueue: (paper: Paper) => void;
}

export default function LibraryPaperCard({
  paper,
  listMemberships,
  onAddToQueue,
}: LibraryPaperCardProps) {
  const readingTime = estimateReadingTime(paper.summary || paper.generated_summary);

  return (
    <article className="relative bg-surface-card rounded-2xl p-5 shadow-warm-sm hover:shadow-warm-md transition-shadow card-hover overflow-hidden">
      {/* Subtle "in library" bottom accent bar */}
      <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-accent/25 rounded-b-2xl" />
      {/* Top row: category chips + action buttons */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex flex-wrap gap-1.5">
          {paper.categories?.map((cat) => (
            <span
              key={cat}
              className="rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-wider font-medium"
              style={{ backgroundColor: getCategoryAccent(cat) + '15', color: getCategoryAccent(cat) }}
            >
              {cat}
            </span>
          ))}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onAddToQueue(paper);
            }}
            className="p-1 text-foreground-muted hover:text-accent transition-colors rounded-full"
            title="Add to Queue"
          >
            <ListPlus className="h-5 w-5" />
          </button>
          <BookmarkButton paper={paper} iconClassName="h-5 w-5" />
        </div>
      </div>

      {/* List membership badges */}
      {listMemberships.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {listMemberships.map((list) => (
            <span
              key={list}
              className="bg-accent/10 text-accent rounded-full px-2 py-0.5 text-[10px] font-medium"
            >
              {list}
            </span>
          ))}
        </div>
      )}

      {/* Title */}
      <Link
        href={`/paper/${paper.arxiv_id}`}
        className="block font-medium text-foreground hover:text-accent transition-colors text-base leading-snug line-clamp-2 mb-2"
      >
        {paper.title}
      </Link>

      {/* Abstract snippet */}
      {paper.summary && (
        <p className="text-foreground-secondary text-sm line-clamp-3 leading-relaxed mb-4">
          {paper.summary}
        </p>
      )}

      {/* Footer row */}
      <div className="flex items-center justify-between pt-3 border-t border-foreground/5">
        {readingTime && (
          <span className="text-foreground-muted text-xs flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            {readingTime}
          </span>
        )}
        <Link
          href={`/paper/${paper.arxiv_id}`}
          className="text-accent text-xs font-medium hover:underline ml-auto"
        >
          Full Details &rarr;
        </Link>
      </div>
    </article>
  );
}
