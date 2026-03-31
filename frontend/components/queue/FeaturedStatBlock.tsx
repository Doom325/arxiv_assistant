"use client";

import { useRouter } from "next/navigation";
import { QueueItem, QueueStats } from "../../lib/api";
import HeroDecoration from "../HeroDecoration";

interface FeaturedStatBlockProps {
    featuredPaper: QueueItem | null;
    stats: QueueStats | null;
    onStartReading: (paper: QueueItem) => void;
}

// Derive a qualitative velocity label from avg_priority
function velocityLabel(avgPriority: number): string {
    if (avgPriority >= 7.5) return "High";
    if (avgPriority >= 5) return "Medium";
    return "Low";
}

// Derive completion percentage from stat totals
function completionPercent(stats: QueueStats): string {
    const total =
        stats.total_unread +
        stats.total_reading +
        stats.total_read +
        stats.total_skipped;
    if (total === 0) return "—";
    const pct = Math.round(((stats.total_read + stats.total_skipped) / total) * 100);
    return `${pct}%`;
}

// Format estimated reading time: prefer minutes field if present, fall back to hours
function readingTimeLabel(stats: QueueStats): string {
    if (stats.estimated_reading_time_minutes !== undefined) {
        const m = stats.estimated_reading_time_minutes;
        if (m < 60) return `${m} min`;
        const h = Math.round(m / 60);
        return `${h} hr`;
    }
    if (stats.estimated_reading_hours !== undefined) {
        const h = stats.estimated_reading_hours;
        if (h < 1) return `${Math.round(h * 60)} min`;
        return `${h.toFixed(1)} hr`;
    }
    return "—";
}

// Format author list from QueueItem (authors may be string[] or null)
function formatAuthors(authors: string[] | null | undefined): string {
    if (!authors || authors.length === 0) return "";
    if (authors.length <= 2) return authors.join(", ");
    return `${authors[0]} et al.`;
}

// Format published date to a short readable string
function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return "";
    return d.toLocaleDateString("en-US", { year: "numeric", month: "short" });
}

interface StatTile {
    label: string;
    value: string | number;
}

export default function FeaturedStatBlock({
    featuredPaper,
    stats,
    onStartReading,
}: FeaturedStatBlockProps) {
    const router = useRouter();

    // Build the six stat tiles
    const tiles: StatTile[] = stats
        ? [
              {
                  label: "AI Discovered",
                  value: stats.discovery_unread,
              },
              {
                  label: "Manual Adds",
                  value: stats.bookmark_unread,
              },
              {
                  label: "Completion",
                  value: completionPercent(stats),
              },
              {
                  label: "Current Velocity",
                  value: velocityLabel(stats.avg_priority),
              },
              {
                  label: "High Priority",
                  value:
                      stats.high_priority_count !== undefined
                          ? stats.high_priority_count
                          : "—",
              },
              {
                  label: "Est. Reading Time",
                  value: readingTimeLabel(stats),
              },
          ]
        : Array.from({ length: 6 }, (_, i) => ({
              label: [
                  "AI Discovered",
                  "Manual Adds",
                  "Completion",
                  "Current Velocity",
                  "High Priority",
                  "Est. Reading Time",
              ][i],
              value: "—",
          }));

    return (
        <div className="relative overflow-hidden rounded-2xl p-8 bg-[#2A4A1A] text-white">
            <HeroDecoration variant="topographic" />
            {/* Top section: featured paper */}
            <div className="mb-8">
                {/* Label */}
                <p
                    className="text-xs font-medium uppercase tracking-[0.08em] text-white/60 mb-3"
                    aria-label="Focus mode section label"
                >
                    Focus Mode · Recommended Next
                </p>

                {featuredPaper ? (
                    <>
                        {/* Paper title */}
                        <h2
                            className="font-bold text-xl text-white mb-3 line-clamp-2"
                            style={{ fontFamily: "var(--font-display)" }}
                        >
                            {featuredPaper.title}
                        </h2>

                        {/* Relevance score + reading time row */}
                        <div className="flex items-center gap-3 mb-3">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-white/20 text-white text-xs font-medium">
                                Relevance {featuredPaper.priority_score.toFixed(1)}
                            </span>
                            {featuredPaper.interest_similarity > 0 && (
                                <span className="text-white/60 text-xs">
                                    ~{Math.round(featuredPaper.interest_similarity * 15 + 5)} min read
                                </span>
                            )}
                        </div>

                        {/* Author / category / date */}
                        <p className="italic text-white/70 text-sm mb-5">
                            {[
                                formatAuthors(featuredPaper.authors),
                                featuredPaper.category,
                                formatDate(featuredPaper.published_date),
                            ]
                                .filter(Boolean)
                                .join(" · ")}
                        </p>

                        {/* Start Reading CTA */}
                        <button
                            onClick={() => {
                                onStartReading(featuredPaper);
                                router.push(`/paper/${featuredPaper.arxiv_id}`);
                            }}
                            className="inline-flex items-center gap-1.5 px-6 py-2 rounded-full bg-accent text-white text-sm font-medium hover:opacity-90 transition-opacity"
                        >
                            Start Reading →
                        </button>
                    </>
                ) : (
                    <p className="text-white/60 text-sm italic mt-2">
                        No papers in queue yet.
                    </p>
                )}
            </div>

            {/* Divider */}
            <div className="border-t border-white/10 mb-6" />

            {/* Bottom section: 2×3 stat tile grid */}
            <div className="grid grid-cols-3 gap-x-6 gap-y-5">
                {tiles.map((tile) => (
                    <div key={tile.label}>
                        <p className="text-xs font-medium uppercase tracking-[0.08em] text-white/60 mb-0.5">
                            {tile.label}
                        </p>
                        <p className="text-xl font-bold text-white leading-tight">
                            {tile.value}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
}
