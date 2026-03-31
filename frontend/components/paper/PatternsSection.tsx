"use client";

import { useState } from "react";
import Link from "next/link";
import { Sparkles, Layers, ChevronDown, ChevronUp } from "lucide-react";
import { PaperPattern } from "@/lib/api";

interface PatternsSectionProps {
  patterns: PaperPattern | null;
}

export default function PatternsSection({ patterns }: PatternsSectionProps) {
  const [showReasoning, setShowReasoning] = useState(false);

  if (!patterns || patterns.patterns.length === 0) return null;

  return (
    <section>
      {/* Section label + count badge + thin warm rule */}
      <div className="flex items-center space-x-3 mb-6">
        <h3 className="uppercase tracking-widest text-[10px] font-bold text-foreground-muted">
          Detected Patterns
        </h3>
        <span className="bg-surface-inset text-foreground-muted text-xs font-mono px-2.5 py-0.5 rounded-full">
          {patterns.patterns.length}
        </span>
        <div className="flex-1 h-px bg-foreground-muted/20" />
      </div>

      {/* Badges row */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {patterns.is_agentic ? (
          <span className="bg-accent/15 text-accent rounded-full px-3 py-1 text-xs font-bold flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5" />
            Agentic System
          </span>
        ) : (
          <span className="bg-surface-inset text-foreground-muted rounded-full px-3 py-1 text-xs font-bold">
            Non-Agentic
          </span>
        )}
        {patterns.primary_pattern_category && (
          <span className="bg-surface-inset text-foreground-secondary rounded-full px-3 py-1 text-xs font-bold">
            {patterns.primary_pattern_category.replace(/_/g, " ")}
          </span>
        )}
        <Link
          href="/patterns"
          className="text-accent hover:text-accent/80 text-xs font-medium flex items-center gap-1 transition-colors"
        >
          <Layers className="h-3 w-3" />
          View Pattern Library
        </Link>
      </div>

      {/* Pattern cards */}
      <div className="space-y-3">
        {patterns.patterns.map((p, idx) => (
          <div
            key={idx}
            className="bg-surface-card rounded-xl p-4 shadow-warm-sm"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-accent font-bold text-sm">
                {p.category}/{p.name}
              </span>
              <span
                className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                  p.confidence >= 0.9
                    ? "bg-accent/15 text-accent"
                    : p.confidence >= 0.8
                      ? "bg-amber-100 text-amber-700"
                      : "bg-surface-inset text-foreground-muted"
                }`}
              >
                {(p.confidence * 100).toFixed(0)}%
              </span>
            </div>

            {/* Confidence bar */}
            <div className="bg-surface-inset rounded-full h-1.5 mb-2">
              <div
                className="bg-accent rounded-full h-1.5 transition-all"
                style={{ width: `${p.confidence * 100}%` }}
              />
            </div>

            {/* Evidence */}
            {p.evidence && (
              <p className="text-xs text-foreground-muted italic mt-1">
                &ldquo;{p.evidence}&rdquo;
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Collapsible CoT reasoning */}
      {patterns.reasoning && (
        <div className="mt-4">
          <button
            onClick={() => setShowReasoning(!showReasoning)}
            className="text-xs font-bold text-foreground-muted hover:text-foreground-secondary flex items-center gap-1 transition-colors"
          >
            {showReasoning ? (
              <ChevronUp className="h-3.5 w-3.5" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5" />
            )}
            Classification Reasoning (CoT)
          </button>
          {showReasoning && (
            <div className="mt-2 bg-surface-inset rounded-xl p-4 font-mono text-xs text-foreground-muted whitespace-pre-wrap">
              {patterns.reasoning}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
