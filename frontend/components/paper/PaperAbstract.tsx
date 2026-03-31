"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

interface PaperAbstractProps {
  abstract: string;
}

export default function PaperAbstract({ abstract }: PaperAbstractProps) {
  if (!abstract || abstract.trim().length === 0) {
    return (
      <section id="abstract">
        <h3 className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted">
          Abstract
        </h3>
        <div className="h-px bg-surface-inset mt-2 mb-6" />
        <p
          className="italic text-foreground-muted"
          style={{ fontFamily: "var(--font-display)" }}
        >
          No abstract available.
        </p>
      </section>
    );
  }

  // Strip leading whitespace for drop cap extraction
  const trimmed = abstract.trimStart();
  const firstChar = trimmed.charAt(0);
  const restOfAbstract = trimmed.slice(1);

  return (
    <section id="abstract">
      <h3 className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted">
        Abstract
      </h3>
      <div className="h-px bg-surface-inset mt-2 mb-6" />
      <div className="prose max-w-none prose-p:text-foreground-secondary prose-p:leading-relaxed prose-headings:text-foreground prose-strong:text-foreground prose-a:text-accent prose-a:no-underline hover:prose-a:underline prose-blockquote:border-accent/30">
        <span
          style={{ fontFamily: "var(--font-display)" }}
          className="text-5xl font-bold text-accent float-left mr-3 mt-1 leading-none select-none"
        >
          {firstChar}
        </span>
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex]}
        >
          {restOfAbstract}
        </ReactMarkdown>
      </div>
    </section>
  );
}
