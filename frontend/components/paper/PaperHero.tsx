"use client";

import { Calendar, FileText, Clock, Mail, Check, X, ExternalLink, Loader2 } from "lucide-react";
import { Paper } from "../../lib/api";
import HeroDecoration from "../HeroDecoration";

interface PaperHeroProps {
  paper: Paper;
  emailStatus: "idle" | "sending" | "sent" | "error";
  onEmail: () => void;
}

/**
 * Splits a title so the first two words are rendered in extralight italic
 * and the rest in bold. Returns [first2words, remainder].
 */
function splitTitle(title: string): [string, string] {
  const words = title.trim().split(/\s+/);
  if (words.length <= 2) return [title, ""];
  return [words.slice(0, 2).join(" "), " " + words.slice(2).join(" ")];
}

/** Rough reading-time estimate based on abstract word count (assumes ~200 wpm). */
function estimateReadingTime(paper: Paper): number {
  const wordCount = (paper.summary ?? "").split(/\s+/).filter(Boolean).length;
  // Abstract is typically ~5-10% of paper length; multiply to approximate full paper
  const estimatedTotal = Math.max(wordCount * 10, wordCount);
  return Math.max(1, Math.round(estimatedTotal / 200));
}

import BookmarkButton from "../BookmarkButton";

export default function PaperHero({
  paper,
  emailStatus,
  onEmail,
}: PaperHeroProps) {
  const [titleHead, titleTail] = splitTitle(paper.title);
  const readingMinutes = estimateReadingTime(paper);

  return (
    <section className="relative overflow-hidden bg-surface-featured rounded-2xl p-8 md:p-10">
      <HeroDecoration variant="topographic" />
      {/* Label */}
      <p className="text-[10px] font-bold uppercase tracking-widest text-white/60 mb-4">
        Research Paper
      </p>

      {/* Title — mixed-weight Newsreader */}
      <h1
        className="text-3xl md:text-4xl leading-tight text-white mb-6"
        style={{ fontFamily: "var(--font-display)" }}
      >
        <span className="font-extralight italic">{titleHead}</span>
        <span className="font-bold">{titleTail}</span>
      </h1>

      {/* Metadata row */}
      <div className="flex flex-wrap items-center gap-4 text-white/60 text-sm mb-6">
        {/* Date */}
        <span className="flex items-center gap-1.5">
          <Calendar className="h-4 w-4" />
          <span suppressHydrationWarning>
            {new Date(paper.published_date).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </span>
        </span>

        {/* Arxiv ID */}
        <span className="flex items-center gap-1.5">
          <FileText className="h-4 w-4" />
          <span className="font-mono text-xs">{paper.arxiv_id}</span>
        </span>

        {/* Reading time */}
        <span className="flex items-center gap-1.5 text-xs uppercase tracking-wider">
          <Clock className="h-3.5 w-3.5" />
          {readingMinutes} min read
        </span>

        {/* Category chips */}
        {paper.categories.map((cat) => (
          <span
            key={cat}
            className="bg-white/10 text-white/80 rounded-full px-3 py-0.5 text-xs"
          >
            {cat}
          </span>
        ))}
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-3">
        {/* Email button */}
        <button
          onClick={onEmail}
          disabled={emailStatus === "sending"}
          className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
            emailStatus === "sent"
              ? "bg-green-500 text-white"
              : emailStatus === "error"
                ? "bg-red-500 text-white"
                : "bg-white/10 hover:bg-white/20 text-white"
          }`}
          title={
            emailStatus === "sent"
              ? "Email sent!"
              : emailStatus === "error"
                ? "Email failed"
                : "Email summary"
          }
        >
          {emailStatus === "sending" ? (
            <Loader2 className="h-[18px] w-[18px] animate-spin" />
          ) : emailStatus === "sent" ? (
            <Check className="h-[18px] w-[18px]" />
          ) : emailStatus === "error" ? (
            <X className="h-[18px] w-[18px]" />
          ) : (
            <Mail className="h-[18px] w-[18px]" />
          )}
        </button>

        {/* Bookmark button */}
        <BookmarkButton
          paper={paper}
          className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors text-white"
          iconClassName="h-[18px] w-[18px]"
        />

        {/* Open PDF CTA */}
        <a
          href={paper.pdf_url}
          target="_blank"
          rel="noopener noreferrer"
          className="ml-2 bg-accent text-on-accent rounded-full px-6 py-2.5 text-sm font-medium inline-flex items-center gap-2 hover:bg-accent-hover transition-colors"
        >
          <ExternalLink className="h-4 w-4" />
          Open PDF
        </a>
      </div>
    </section>
  );
}
