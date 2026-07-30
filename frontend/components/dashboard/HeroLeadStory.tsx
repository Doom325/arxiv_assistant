"use client";

import Link from "next/link";
import { Clock } from "lucide-react";
import { Paper } from "../../lib/api";
import HeroDecoration from "../HeroDecoration";

import BookmarkButton from "../BookmarkButton";

interface HeroLeadStoryProps {
  paper: Paper | null;
  onReadFull: (paper: Paper) => void;
}

function estimateReadTime(text: string | undefined | null): string {
  if (!text) return "5 min read";
  const words = text.split(/\s+/).length;
  const minutes = Math.max(1, Math.ceil(words / 200));
  return `${minutes} min read`;
}

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return "";
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export default function HeroLeadStory({
  paper,
  onReadFull,
}: HeroLeadStoryProps) {
  if (!paper) {
    return (
      <section className="rounded-2xl bg-[#1B3022] p-10 min-h-[320px] flex items-center justify-center">
        <div className="text-center space-y-3">
          <p className="text-white/60 font-display text-xl italic">
            No lead story available
          </p>
          <p className="text-white/40 text-sm">
            Run an AI scan to discover papers.
          </p>
        </div>
      </section>
    );
  }

  const readTime = estimateReadTime(paper.summary);
  const pubDate = formatDate(paper.published_date);

  // Split title for mixed-weight headline — use first few words as light context
  const titleWords = paper.title.split(" ");
  const contextPhrase = titleWords.length > 3 ? titleWords.slice(0, 2).join(" ") : "";
  const mainPhrase = contextPhrase
    ? titleWords.slice(2).join(" ")
    : paper.title;

  return (
    <section className="relative overflow-hidden rounded-2xl bg-[#1B3022] p-8 md:p-10 min-h-[400px] flex flex-col justify-end">
      <HeroDecoration variant="dots" />
      {/* Top label */}
      <div className="mb-auto">
        <span className="text-[10px] font-bold uppercase tracking-widest text-white/60">
          Lead Story
        </span>
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-2xl space-y-5">
        {/* Mixed-weight serif headline */}
        <h2 className="font-display text-3xl md:text-4xl lg:text-5xl leading-tight text-white">
          {contextPhrase && (
            <>
              <span className="font-light italic">{contextPhrase}</span>{" "}
            </>
          )}
          <span className="font-bold">{mainPhrase}</span>
        </h2>

        {/* Abstract excerpt */}
        <p className="text-white/80 text-sm leading-relaxed line-clamp-3">
          {paper.summary || "No abstract available."}
        </p>

        {/* Metadata row */}
        <div className="flex items-center gap-3 flex-wrap">
          <span className="flex items-center gap-1.5 text-white/60 text-xs uppercase tracking-widest font-bold">
            <Clock className="h-3.5 w-3.5" />
            {readTime}
          </span>
          {pubDate && (
            <>
              <span className="text-white/30">·</span>
              <span className="text-white/60 text-xs">{pubDate}</span>
            </>
          )}
          {paper.categories?.slice(0, 3).map((cat) => (
            <span
              key={cat}
              className="bg-white/10 border border-white/10 text-white/80 rounded-full px-3 py-0.5 text-xs uppercase font-semibold tracking-wide"
            >
              {cat}
            </span>
          ))}
        </div>

        {/* CTAs */}
        <div className="flex items-center gap-4 pt-2">
          <Link
            href={`/paper/${paper.db_id || paper.id}`}
            onClick={(e) => {
              e.preventDefault();
              onReadFull(paper);
            }}
            className="bg-accent text-white rounded-full px-6 py-2.5 text-sm font-semibold hover:bg-accent-hover transition-colors"
          >
            Read Full Analysis
          </Link>

          <BookmarkButton
            paper={paper}
            className="w-10 h-10 rounded-full border border-white/20 flex items-center justify-center text-white hover:bg-white/10 transition-colors"
            iconClassName="h-5 w-5"
          />
        </div>
      </div>
    </section>
  );
}
