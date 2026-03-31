"use client";

import { Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

interface AISynthesisSectionProps {
  summary: string | null | undefined;
  isSummarizing: boolean;
  onGenerate: () => void;
  hasExistingSummary: boolean;
}

export default function AISynthesisSection({
  summary,
  isSummarizing,
  onGenerate,
  hasExistingSummary,
}: AISynthesisSectionProps) {
  const buttonText = isSummarizing
    ? "Generating..."
    : hasExistingSummary
      ? "Regenerate Analysis"
      : "Generate Analysis";

  return (
    <section
      id="ai-synthesis"
      className="bg-surface-card rounded-2xl shadow-warm-sm p-6 md:p-8"
    >
      {/* Header row */}
      <div className="flex items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-accent" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-foreground">
            AI Synthesis
          </span>
        </div>
        <button
          onClick={onGenerate}
          disabled={isSummarizing}
          className="bg-accent text-on-accent rounded-full px-5 py-2 text-sm font-medium transition-colors hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {buttonText}
        </button>
      </div>

      {/* Content area */}
      {summary ? (
        <>
          <div className="prose max-w-none prose-p:text-foreground-secondary prose-p:leading-relaxed prose-headings:text-foreground prose-strong:text-foreground prose-a:text-accent prose-a:no-underline hover:prose-a:underline prose-blockquote:border-accent/30">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {summary}
            </ReactMarkdown>
          </div>
          <p className="text-foreground-muted text-xs mt-6">
            Analysis completed
          </p>
        </>
      ) : isSummarizing ? (
        <div className="flex items-center gap-3 py-4">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
          </span>
          <p
            className="italic text-foreground-muted"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Reasoning through the paper... this may take 30-60 seconds.
          </p>
        </div>
      ) : (
        <p
          className="italic text-foreground-muted py-4"
          style={{ fontFamily: "var(--font-display)" }}
        >
          No AI analysis generated yet. Click Generate Analysis to start.
        </p>
      )}
    </section>
  );
}
