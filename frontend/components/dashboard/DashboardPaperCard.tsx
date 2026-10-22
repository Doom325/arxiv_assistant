"use client";

import React from "react";
import Link from "next/link";
import { Eye, ArrowUpRight } from "lucide-react";
import { Paper } from "../../lib/api";
import { estimateReadingTime, getCategoryAccent } from "../../lib/categoryColors";

import { useLibrary } from "../LibraryContext";
import BookmarkButton from "../BookmarkButton";

interface DashboardPaperCardProps {
  paper: Paper;
  variant: "large" | "compact";
  onPreview: (paper: Paper) => void;
  isFocused?: boolean;
}

/* ── helpers ────────────────────────────────────────── */

function formatDate(dateStr: string | undefined | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function primaryCategory(paper: Paper): string {
  if (paper.categories && paper.categories.length > 0) return paper.categories[0];
  return "cs.AI";
}

function paperDetailHref(paper: Paper): string {
  return `/paper/${paper.db_id || paper.arxiv_id || paper.id}`;
}

/* ── Large Variant ──────────────────────────────────── */

function LargeCard({ paper, onPreview, isFocused }: DashboardPaperCardProps) {
  const { bookmarkedMap } = useLibrary();
  const isBookmarked = paper.db_id ? (bookmarkedMap[paper.db_id] ?? []).length > 0 : false;
  const readingTime = estimateReadingTime(paper.summary || paper.generated_summary);
  const category = primaryCategory(paper);
  const pubDate = formatDate(paper.published_date);

  return (
    <article
      onClick={() => onPreview(paper)}
      className={`
        relative bg-surface-card rounded-2xl p-6 shadow-warm-sm overflow-hidden
        group cursor-pointer card-hover flex flex-col
        hover:shadow-warm transition-shadow duration-200
        ${isFocused ? "focus-ring" : ""}
      `}
    >
      {/* Bookmark — top-right corner */}
      <div className="absolute top-5 right-5 z-10">
        <BookmarkButton
          paper={paper}
          className=""
          iconClassName="h-5 w-5 hover:text-accent"
        />
      </div>

      {/* Bookmarked reading indicator */}
      {isBookmarked && (
        <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-accent/25 rounded-b-2xl" />
      )}

      {/* Category chip */}
      <span
        className="inline-block self-start rounded-full px-3 py-0.5 text-xs uppercase tracking-wider mb-4 font-medium"
        style={{ backgroundColor: getCategoryAccent(category) + "15", color: getCategoryAccent(category) }}
      >
        {category}
      </span>

      {/* Title — clicking opens Quick Peek preview */}
      <h3 className="font-medium text-foreground text-lg leading-snug line-clamp-2 group-hover:text-accent transition-colors mb-3 pr-8">
        {paper.title}
      </h3>

      {/* Abstract snippet */}
      {(paper.summary || paper.generated_summary) && (
        <p className="text-foreground-secondary text-sm line-clamp-2 leading-relaxed mb-4">
          {paper.summary || paper.generated_summary}
        </p>
      )}

      {/* Metadata row */}
      <div className="flex items-center justify-between pt-3 mt-auto border-t border-surface-inset/40">
        <div className="flex items-center gap-3 text-foreground-muted text-xs italic min-w-0">
          {pubDate && <span>{pubDate}</span>}
          {readingTime && (
            <>
              <span aria-hidden="true" className="text-foreground-muted/40">&middot;</span>
              <span className="uppercase tracking-wider text-[10px] not-italic font-medium">
                {readingTime}
              </span>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Link
            href={paperDetailHref(paper)}
            onClick={(e) => e.stopPropagation()}
            className="
              inline-flex items-center gap-1
              text-foreground-muted hover:text-foreground rounded-full
              px-2.5 py-1 text-xs font-medium
              hover:bg-surface-inset/60 transition-colors
            "
          >
            Full
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>

          {/* Preview pill button */}
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onPreview(paper);
            }}
            className="
              inline-flex items-center gap-1.5
              border border-accent/40 text-accent rounded-full
              px-3 py-1 text-xs font-medium
              hover:bg-accent/10 transition-colors
              shrink-0
            "
          >
            <Eye className="h-3.5 w-3.5" />
            Preview
          </button>
        </div>
      </div>
    </article>
  );
}

/* ── Compact Variant ────────────────────────────────── */

function CompactCard({ paper, onPreview, isFocused }: DashboardPaperCardProps) {
  const { bookmarkedMap } = useLibrary();
  const isBookmarked = paper.db_id ? (bookmarkedMap[paper.db_id] ?? []).length > 0 : false;
  const category = primaryCategory(paper);
  const pubDate = formatDate(paper.published_date);

  return (
    <article
      onClick={() => onPreview(paper)}
      className={`
        relative bg-surface-card rounded-2xl p-4 shadow-warm-sm overflow-hidden
        group cursor-pointer card-hover flex flex-col
        hover:shadow-warm transition-shadow duration-200
        ${isFocused ? "focus-ring" : ""}
      `}
    >
      {/* Bookmarked reading indicator */}
      {isBookmarked && (
        <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-accent/25 rounded-b-2xl" />
      )}

      {/* Category + date header */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <span
          className="text-xs uppercase tracking-wider font-medium"
          style={{ color: getCategoryAccent(category) }}
        >
          {category}
        </span>
        {pubDate && (
          <span className="text-[11px] text-foreground-muted italic">
            {pubDate}
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="font-medium text-foreground text-sm leading-snug line-clamp-2 group-hover:text-accent transition-colors pr-6 mb-3">
        {paper.title}
      </h3>

      {/* Bottom row: status badge + actions */}
      <div className="flex items-center justify-between mt-auto pt-3">
        {paper.generated_summary ? (
          <span className="text-[10px] font-medium uppercase tracking-wider text-accent">
            Analysis Ready
          </span>
        ) : (
          <span className="text-[10px] font-medium uppercase tracking-wider text-foreground-muted">
            {estimateReadingTime(paper.summary) || "New"}
          </span>
        )}

        <div className="flex items-center gap-2">
          <Link
            href={paperDetailHref(paper)}
            onClick={(e) => e.stopPropagation()}
            className="text-[11px] text-foreground-muted hover:text-foreground inline-flex items-center gap-0.5 px-2 py-0.5 rounded hover:bg-surface-inset/60 transition-colors"
          >
            Full
            <ArrowUpRight className="h-3 w-3" />
          </Link>
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onPreview(paper);
            }}
            className="inline-flex items-center gap-1 border border-accent/40 text-accent rounded-full px-2.5 py-0.5 text-[11px] font-medium hover:bg-accent/10 transition-colors"
          >
            <Eye className="h-3 w-3" />
            Preview
          </button>
          <BookmarkButton
            paper={paper}
            className=""
            iconClassName="h-4 w-4 hover:text-accent"
          />
        </div>
      </div>
    </article>
  );
}

/* ── Exported component ─────────────────────────────── */

export default function DashboardPaperCard(props: DashboardPaperCardProps) {
  if (props.variant === "large") {
    return <LargeCard {...props} />;
  }
  return <CompactCard {...props} />;
}
