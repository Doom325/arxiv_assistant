"use client";

import { useState, useEffect } from "react";
import {
  X,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Check,
} from "lucide-react";
import { Paper } from "../../lib/api";
import { useSummarize } from "../../lib/useSummarize";

interface DashboardQuickPeekProps {
  paper: Paper | null;
  isOpen: boolean;
  onClose: () => void;
  onPrev: () => void;
  onNext: () => void;
  hasPrev: boolean;
  hasNext: boolean;
  onReadFull: (paper: Paper) => void;
  prevTitle?: string;
  nextTitle?: string;
}

/**
 * Dashboard-specific quick-peek panel.
 * Differs from the queue's QuickPreviewPanel by featuring:
 *  - "DEEP WORK PEEK" branded header
 *  - Drop cap abstract
 *  - AI Synthesis Findings (deep green card)
 *  - Metadata detail grid
 *  - Prev/next footer with paper titles
 *
 * Returns null on viewports < 1024px (fall back to QuickPeekSheet).
 */
export default function DashboardQuickPeek({
  paper,
  isOpen,
  onClose,
  onPrev,
  onNext,
  hasPrev,
  hasNext,
  onReadFull,
  prevTitle,
  nextTitle,
}: DashboardQuickPeekProps) {
  // Narrow viewport fallback
  const [isWide, setIsWide] = useState(false);
  useEffect(() => {
    const check = () => setIsWide(window.innerWidth >= 1024);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // AI summary hook — useSummarize expects numeric db_id
  const { summarizing, updatedSummary, error, triggerSummarize } =
    useSummarize(paper?.db_id ?? null);

  if (!isWide) return null;

  // ── Derived display values ───────────────────────────
  const displaySummary =
    updatedSummary || paper?.generated_summary || null;

  const authorDisplay = (() => {
    if (!paper?.sources) return null;
    // Paper type doesn't have authors directly — try sources or fallback
    return null;
  })();

  const dateDisplay = (() => {
    if (!paper?.published_date) return null;
    const d = new Date(paper.published_date);
    if (isNaN(d.getTime())) return null;
    return d.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  })();

  // Estimate reading time from abstract length
  const readingTime = (() => {
    const words = (paper?.summary || "").split(/\s+/).length;
    const mins = Math.max(1, Math.ceil(words / 200));
    return `${mins} min read`;
  })();

  // Parse bullet-point findings from generated_summary
  const parseSynthesisFindings = (
    text: string
  ): { title: string; detail: string }[] => {
    const lines = text.split("\n");
    const items: { title: string; detail: string }[] = [];
    for (const line of lines) {
      const match = line.match(/^\s*\d+[\.\)]\s+(.+)/);
      if (match) {
        // Try to split on first colon or period for title/detail
        const colonIdx = match[1].indexOf(":");
        if (colonIdx > 0 && colonIdx < 60) {
          items.push({
            title: match[1].slice(0, colonIdx).trim(),
            detail: match[1].slice(colonIdx + 1).trim(),
          });
        } else {
          items.push({ title: match[1].trim(), detail: "" });
        }
      }
    }
    return items;
  };

  const findings = displaySummary
    ? parseSynthesisFindings(displaySummary)
    : [];

  // Split title for mixed-weight headline
  const titleWords = (paper?.title || "").split(/\s+/);
  const italicPart = titleWords.slice(0, 2).join(" ");
  const boldPart = titleWords.slice(2).join(" ");

  return (
    <div
      className={`fixed top-[60px] right-0 bottom-0 w-[420px] z-20
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
      {/* ── Header ──────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 pt-5 pb-4 shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles
            className="h-4 w-4"
            style={{ color: "var(--color-accent)" }}
          />
          <span
            className="text-[10px] font-bold uppercase tracking-[0.2em]"
            style={{ color: "var(--color-accent)" }}
          >
            Deep Work Peek
          </span>
        </div>
        <button
          onClick={onClose}
          aria-label="Close peek panel"
          className="text-foreground-muted hover:text-foreground transition-colors p-1 -mr-1 rounded"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* ── Scrollable body ─────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-6 pb-6">
        {!paper ? (
          <p className="text-foreground-muted text-sm italic mt-4">
            Select a paper to preview.
          </p>
        ) : (
          <>
            {/* Category chips */}
            {paper.categories && paper.categories.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {paper.categories.map((cat) => (
                  <span
                    key={cat}
                    className="px-3 py-1 rounded-full bg-surface-inset text-[11px] font-bold tracking-wider uppercase text-foreground-muted"
                  >
                    {cat}
                  </span>
                ))}
              </div>
            )}

            {/* Mixed-weight headline */}
            <h2 className="leading-tight mb-3" style={{ fontFamily: "var(--font-display)" }}>
              {italicPart && (
                <span className="block text-lg font-extralight italic text-foreground-secondary mb-0.5">
                  {italicPart}
                </span>
              )}
              {boldPart && (
                <span className="text-2xl font-bold tracking-tight text-foreground">
                  {boldPart}
                </span>
              )}
              {/* Fallback for very short titles */}
              {!boldPart && !italicPart && (
                <span className="text-2xl font-bold tracking-tight text-foreground">
                  {paper.title}
                </span>
              )}
            </h2>

            {/* Metadata: date + reading time */}
            <div className="flex items-center gap-6 text-[11px] font-medium uppercase tracking-widest text-foreground-muted mb-8">
              {dateDisplay && <span>{dateDisplay}</span>}
              <span style={{ color: "var(--color-accent)" }} className="font-bold">
                {readingTime}
              </span>
            </div>

            {/* ── Abstract with drop cap ───────────────────── */}
            <section className="mb-8">
              <h3
                className="text-lg font-semibold mb-4 text-foreground"
                style={{ fontFamily: "var(--font-display)" }}
              >
                Abstract
              </h3>
              {paper.summary ? (
                <p className="text-sm leading-relaxed text-foreground-secondary">
                  {/* Drop cap: first letter */}
                  <span
                    className="text-5xl font-bold float-left mr-2 leading-none"
                    style={{
                      fontFamily: "var(--font-display)",
                      color: "var(--color-accent)",
                    }}
                  >
                    {paper.summary.charAt(0)}
                  </span>
                  {paper.summary.slice(1)}
                </p>
              ) : (
                <p className="text-sm text-foreground-muted italic">
                  No abstract available.
                </p>
              )}
            </section>

            {/* ── AI Synthesis Findings ─────────────────────── */}
            <section
              className="rounded-xl p-5 mb-8 relative overflow-hidden"
              style={{ backgroundColor: "var(--color-surface-featured)" }}
            >
              {/* Decorative sparkle */}
              <div className="absolute top-0 right-0 p-3 opacity-10">
                <Sparkles className="h-12 w-12 text-white" />
              </div>

              <div className="relative z-10">
                <h3
                  className="text-lg font-bold mb-4 flex items-center gap-2"
                  style={{
                    fontFamily: "var(--font-display)",
                    color: "var(--color-on-featured)",
                  }}
                >
                  Synthesis Findings
                </h3>

                {error && (
                  <p className="text-sm text-red-300 mb-3">{error}</p>
                )}

                {summarizing && !displaySummary ? (
                  <p
                    className="text-sm italic"
                    style={{ color: "var(--color-on-featured)", opacity: 0.7 }}
                  >
                    Generating synthesis...
                  </p>
                ) : findings.length > 0 ? (
                  <ul className="space-y-4">
                    {findings.map((f, idx) => (
                      <li key={idx} className="flex gap-3 items-start">
                        <span
                          className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5"
                          style={{ backgroundColor: "var(--color-accent)" }}
                        >
                          <Check className="h-3 w-3 text-white" />
                        </span>
                        <div className="space-y-0.5">
                          <p
                            className="font-semibold text-sm leading-snug"
                            style={{ color: "var(--color-on-featured)" }}
                          >
                            {f.title}
                          </p>
                          {f.detail && (
                            <p
                              className="text-xs leading-relaxed"
                              style={{
                                color: "var(--color-on-featured)",
                                opacity: 0.75,
                              }}
                            >
                              {f.detail}
                            </p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : displaySummary ? (
                  <p
                    className="text-sm italic leading-relaxed"
                    style={{ color: "var(--color-on-featured)", opacity: 0.8 }}
                  >
                    {displaySummary}
                  </p>
                ) : (
                  <p
                    className="text-sm italic"
                    style={{ color: "var(--color-on-featured)", opacity: 0.6 }}
                  >
                    No synthesis yet.
                  </p>
                )}

                {/* CTA */}
                <button
                  onClick={() => triggerSummarize(!displaySummary ? false : true)}
                  disabled={summarizing}
                  className="mt-5 w-full py-3 rounded-lg font-bold tracking-widest text-[11px] uppercase transition-all active:scale-[0.98] disabled:opacity-50"
                  style={{
                    backgroundColor: "var(--color-accent)",
                    color: "var(--color-on-accent)",
                  }}
                >
                  {summarizing
                    ? "Generating..."
                    : displaySummary
                    ? "Regenerate Analysis"
                    : "Generate Full Deep Analysis"}
                </button>
              </div>
            </section>

            {/* ── Metadata detail grid ──────────────────────── */}
            <section className="grid grid-cols-2 gap-px bg-surface-inset/30 rounded-xl overflow-hidden mb-8">
              <MetadataCell label="Author" value={authorDisplay || "N/A"} />
              <MetadataCell label="Institution" value="N/A" />
              <MetadataCell label="Citations" value={paper.citations?.length?.toString() || "N/A"} />
              <MetadataCell label="Peer Review" value="N/A" />
            </section>
          </>
        )}
      </div>

      {/* ── Footer: Prev/Next paper navigation ──────────── */}
      <div className="shrink-0 border-t border-white/20 flex items-center justify-between px-5 py-4">
        <button
          onClick={onPrev}
          disabled={!hasPrev}
          className="flex items-center gap-3 group disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-foreground-muted hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" />
          <div className="text-left">
            <span className="block text-[10px] font-bold uppercase tracking-wider opacity-60">
              Previous Paper
            </span>
            {prevTitle && (
              <span
                className="text-xs font-medium leading-none line-clamp-1"
                style={{ fontFamily: "var(--font-display)" }}
              >
                {prevTitle}
              </span>
            )}
          </div>
        </button>

        <div className="h-6 w-px bg-surface-inset" />

        <button
          onClick={onNext}
          disabled={!hasNext}
          className="flex items-center gap-3 group disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-foreground-muted hover:text-foreground text-right"
        >
          <div className="text-right">
            <span className="block text-[10px] font-bold uppercase tracking-wider opacity-60">
              Next Paper
            </span>
            {nextTitle && (
              <span
                className="text-xs font-medium leading-none line-clamp-1"
                style={{ fontFamily: "var(--font-display)" }}
              >
                {nextTitle}
              </span>
            )}
          </div>
          <ChevronRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
}

/* ── Metadata cell sub-component ──────────────────────── */

function MetadataCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface-card p-4">
      <span className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted block mb-1">
        {label}
      </span>
      <p
        className="text-base font-medium text-foreground"
        style={{ fontFamily: "var(--font-display)" }}
      >
        {value}
      </p>
    </div>
  );
}
