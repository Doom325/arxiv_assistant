"use client";

import { useState, useEffect } from "react";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { QueueItem } from "../../lib/api";
import { useSummarize } from "../../lib/useSummarize";

interface QuickPreviewPanelProps {
  paper: QueueItem | null;
  isOpen: boolean;
  onClose: () => void;
  onPrev: () => void;
  onNext: () => void;
  hasPrev: boolean;
  hasNext: boolean;
  onBeginReading: (paper: QueueItem) => void;
  currentIndex?: number;
  totalCount?: number;
}

export default function QuickPreviewPanel({
  paper,
  isOpen,
  onClose,
  onPrev,
  onNext,
  hasPrev,
  hasNext,
  onBeginReading,
  currentIndex,
  totalCount,
}: QuickPreviewPanelProps) {
  // 3.8.4 — Narrow viewport fallback: render nothing below 1024px
  const [isWide, setIsWide] = useState(false);
  useEffect(() => {
    const check = () => setIsWide(window.innerWidth >= 1024);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // 3.8.2 — Wire useSummarize (same pattern as QuickPeekSheet)
  const { summarizing, updatedSummary, error, triggerSummarize } = useSummarize(
    paper?.paper_id ?? null
  );

  if (!isWide) return null;

  // Derive display values
  const displaySummary = updatedSummary || paper?.generated_summary || null;
  const isRegenerate = !!displaySummary;

  const authorDisplay = (() => {
    if (!paper?.authors) return null;
    if (Array.isArray(paper.authors) && paper.authors.length > 0) {
      const first = paper.authors[0];
      const rest = paper.authors.length > 1 ? ` et al.` : "";
      return `${first}${rest}`;
    }
    return null;
  })();

  const yearDisplay = (() => {
    if (!paper?.published_date) return null;
    const d = new Date(paper.published_date);
    if (isNaN(d.getTime())) return null;
    return d.getFullYear().toString();
  })();

  const authorYearLine = [authorDisplay, yearDisplay].filter(Boolean).join(", ");

  // Parse takeaways from the generated_summary markdown — look for numbered list items
  const parseTakeaways = (text: string): string[] => {
    const lines = text.split("\n");
    const items: string[] = [];
    for (const line of lines) {
      const match = line.match(/^\s*\d+[\.\)]\s+(.+)/);
      if (match) {
        items.push(match[1].trim());
      }
    }
    return items;
  };

  const takeaways = displaySummary ? parseTakeaways(displaySummary) : [];

  return (
    <div
      className={`fixed top-[60px] right-0 bottom-0 w-[400px] z-20
        border-l border-white/40
        transition-transform duration-300 ease-in-out
        flex flex-col
        ${isOpen ? "translate-x-0" : "translate-x-full"}`}
      style={{
        backgroundColor: "var(--color-surface-overlay)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
      }}
    >
      {/* ── Header row ──────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 pt-5 pb-4 shrink-0">
        <span
          className="text-xs font-medium uppercase tracking-[0.12em] text-foreground-muted"
        >
          Quick Preview
        </span>
        <button
          onClick={onClose}
          aria-label="Close preview panel"
          className="text-foreground-muted hover:text-foreground transition-colors p-1 -mr-1 rounded"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* ── Scrollable body ─────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-6 pb-4">
        {!paper ? (
          <p className="text-foreground-muted text-sm italic mt-4">
            Select a paper to preview.
          </p>
        ) : (
          <>
            {/* Paper title */}
            <h2
              className="font-display font-bold text-xl text-foreground leading-snug mb-2"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {paper.title}
            </h2>

            {/* Author + year */}
            {authorYearLine && (
              <p className="text-foreground-secondary text-sm italic mb-5">
                {authorYearLine}
              </p>
            )}

            {/* ── Abstract ────────────────────────────────── */}
            <section className="mb-6">
              <p
                className="text-xs font-medium uppercase tracking-[0.08em] text-foreground-muted mb-2"
              >
                Abstract
              </p>
              <p className="text-foreground text-sm leading-relaxed">
                {paper.summary || "No abstract available."}
              </p>
            </section>

            {/* ── AI Key Takeaways ─────────────────────────── */}
            <section className="mb-6">
              <p
                className="text-xs font-medium uppercase tracking-[0.08em] text-foreground-muted mb-3"
              >
                AI Key Takeaways
              </p>

              {error && (
                <p className="text-sm text-red-600 mb-2">{error}</p>
              )}

              {summarizing && !displaySummary ? (
                <p className="text-foreground-secondary text-sm italic">
                  Generating key takeaways...
                </p>
              ) : takeaways.length > 0 ? (
                <ol className="space-y-2">
                  {takeaways.map((item, idx) => (
                    <li key={idx} className="flex gap-2 items-start">
                      <span
                        className="text-accent font-medium text-sm tabular-nums shrink-0 mt-0.5"
                        style={{ color: "var(--color-accent)" }}
                      >
                        {idx + 1}.
                      </span>
                      <span className="text-foreground-secondary italic text-sm leading-snug">
                        {item}
                      </span>
                    </li>
                  ))}
                </ol>
              ) : displaySummary && takeaways.length === 0 ? (
                // Summary exists but no numbered list — show raw summary prose
                <p className="text-foreground-secondary italic text-sm leading-relaxed">
                  {displaySummary}
                </p>
              ) : (
                // No summary yet
                <div className="flex flex-col gap-2">
                  <p className="text-foreground-muted text-sm italic">
                    No key takeaways yet.
                  </p>
                  <button
                    onClick={() => triggerSummarize(false)}
                    disabled={summarizing}
                    className="self-start text-sm px-3 py-1.5 rounded-lg
                      bg-surface-inset text-foreground-secondary
                      hover:text-foreground hover:bg-surface-card
                      transition-colors disabled:opacity-50"
                  >
                    Generate Summary
                  </button>
                </div>
              )}

              {/* Regenerate button when summary already exists */}
              {displaySummary && !summarizing && (
                <button
                  onClick={() => triggerSummarize(true)}
                  className="mt-3 text-xs text-foreground-muted hover:text-foreground-secondary transition-colors underline underline-offset-2"
                >
                  Regenerate
                </button>
              )}
            </section>
          </>
        )}
      </div>

      {/* ── Footer: Begin Reading Session + Prev/Next ──── */}
      <div className="shrink-0 px-6 py-4 border-t border-white/20 space-y-3">
        {/* 3.8.3 — "Begin Reading Session" full-width CTA */}
        <button
          onClick={() => paper && onBeginReading(paper)}
          disabled={!paper}
          className="w-full py-3 rounded-2xl font-medium text-sm transition-colors disabled:opacity-40"
          style={{
            backgroundColor: paper ? "var(--color-accent)" : undefined,
            color: paper ? "var(--color-on-accent)" : undefined,
          }}
        >
          Begin Reading Session
        </button>

        {/* Prev / Next navigation with count indicator */}
        <div className="flex items-center justify-between">
          <button
            onClick={onPrev}
            disabled={!hasPrev}
            aria-label="Previous paper"
            className="p-1.5 rounded-lg text-foreground-muted hover:text-foreground
              disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>

          {currentIndex !== undefined && totalCount !== undefined ? (
            <span className="text-xs text-foreground-muted tabular-nums">
              {currentIndex + 1} of {totalCount}
            </span>
          ) : (
            <span />
          )}

          <button
            onClick={onNext}
            disabled={!hasNext}
            aria-label="Next paper"
            className="p-1.5 rounded-lg text-foreground-muted hover:text-foreground
              disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
