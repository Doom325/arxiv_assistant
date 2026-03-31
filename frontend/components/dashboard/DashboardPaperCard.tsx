"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bookmark, Eye } from "lucide-react";
import { Paper } from "../../lib/api";
import { estimateReadingTime, getCategoryAccent } from "../../lib/categoryColors";

interface DashboardPaperCardProps {
  paper: Paper;
  variant: "large" | "compact";
  onPreview: (paper: Paper) => void;
  onBookmark: (paper: Paper) => void;
  isBookmarked: boolean;
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

function extractAuthors(paper: Paper): string {
  // Paper interface doesn't expose authors directly; fall back to summary metadata
  // If the paper has a list_name that looks like an author, show it; otherwise show a generic label
  return "";
}

/* ── Large Variant ──────────────────────────────────── */

function LargeCard({ paper, onPreview, onBookmark, isBookmarked, isFocused }: DashboardPaperCardProps) {
  const router = useRouter();
  const readingTime = estimateReadingTime(paper.summary || paper.generated_summary);
  const category = primaryCategory(paper);
  const pubDate = formatDate(paper.published_date);

  return (
    <article
      onClick={() => router.push(`/paper/${paper.arxiv_id}`)}
      className={`
        relative bg-surface-card rounded-2xl p-6 shadow-warm-sm overflow-hidden
        group cursor-pointer card-hover
        hover:shadow-warm transition-shadow duration-200
        ${isFocused ? "focus-ring" : ""}
      `}
    >
      {/* Bookmark — top-right corner */}
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onBookmark(paper);
        }}
        className="absolute top-5 right-5 z-10"
        aria-label={isBookmarked ? "Remove bookmark" : "Add bookmark"}
      >
        <Bookmark
          className={`h-5 w-5 transition-colors ${
            isBookmarked
              ? "fill-accent text-accent"
              : "text-foreground-muted hover:text-accent"
          }`}
        />
      </button>

      {/* Bookmarked reading indicator */}
      {isBookmarked && (
        <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-accent/25 rounded-b-2xl" />
      )}

      {/* Category chip */}
      <span
        className="inline-block rounded-full px-3 py-0.5 text-xs uppercase tracking-wider mb-4 font-medium"
        style={{ backgroundColor: getCategoryAccent(category) + '15', color: getCategoryAccent(category) }}
      >
        {category}
      </span>

      {/* Title — clicking navigates to detail page */}
      <Link href={`/paper/${paper.arxiv_id}`} className="block">
        <h3 className="font-medium text-foreground text-lg leading-snug line-clamp-2 hover:text-accent transition-colors mb-3 pr-8">
          {paper.title}
        </h3>
      </Link>

      {/* Abstract snippet */}
      {(paper.summary || paper.generated_summary) && (
        <p className="text-foreground-secondary text-sm line-clamp-2 leading-relaxed mb-4">
          {paper.summary || paper.generated_summary}
        </p>
      )}

      {/* Metadata row */}
      <div className="flex items-center justify-between pt-3 border-t border-surface-inset/40">
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

        {/* Preview pill button */}
        <button
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
    </article>
  );
}

/* ── Compact Variant ────────────────────────────────── */

function CompactCard({ paper, onPreview, onBookmark, isBookmarked, isFocused }: DashboardPaperCardProps) {
  const router = useRouter();
  const category = primaryCategory(paper);

  return (
    <article
      onClick={() => router.push(`/paper/${paper.arxiv_id}`)}
      className={`
        relative bg-surface-card rounded-2xl p-4 shadow-warm-sm overflow-hidden
        group cursor-pointer card-hover
        hover:shadow-warm transition-shadow duration-200
        ${isFocused ? "focus-ring" : ""}
      `}
    >
      {/* Bookmarked reading indicator */}
      {isBookmarked && (
        <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-accent/25 rounded-b-2xl" />
      )}

      {/* Category + topic label */}
      <span
        className="block text-xs uppercase tracking-wider font-medium mb-3"
        style={{ color: getCategoryAccent(category) }}
      >
        {category}
      </span>

      {/* Title */}
      <h3 className="font-medium text-foreground text-sm leading-snug line-clamp-2 group-hover:text-accent transition-colors pr-6 mb-3">
        {paper.title}
      </h3>

      {/* Bottom row: status badge + bookmark */}
      <div className="flex items-center justify-between mt-auto pt-3">
        {/* Status badge (reading time or generic) */}
        {paper.generated_summary ? (
          <span className="text-[10px] font-medium uppercase tracking-wider text-accent">
            Analysis Ready
          </span>
        ) : (
          <span className="text-[10px] font-medium uppercase tracking-wider text-foreground-muted">
            {estimateReadingTime(paper.summary) || "New"}
          </span>
        )}

        {/* Bookmark — smaller */}
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onBookmark(paper);
          }}
          aria-label={isBookmarked ? "Remove bookmark" : "Add bookmark"}
        >
          <Bookmark
            className={`h-4 w-4 transition-colors ${
              isBookmarked
                ? "fill-accent text-accent"
                : "text-foreground-muted/40 hover:text-accent"
            }`}
          />
        </button>
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
