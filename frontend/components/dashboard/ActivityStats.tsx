"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface ActivityStatsProps {
  totalPapers: number;
  weeklyDelta: number;
  weeklyTrend: "up" | "down" | "flat";
  pulseScore: number;
}

function formatNumber(n: number): string {
  if (n == null || isNaN(n)) return "\u2014";
  return n.toLocaleString("en-US");
}

function TrendIcon({ trend }: { trend: "up" | "down" | "flat" }) {
  const cls = "h-4 w-4";
  switch (trend) {
    case "up":
      return <TrendingUp className={`${cls} text-emerald-600`} />;
    case "down":
      return <TrendingDown className={`${cls} text-red-600`} />;
    case "flat":
      return <Minus className={`${cls} text-foreground-muted`} />;
  }
}

function trendColor(trend: "up" | "down" | "flat") {
  switch (trend) {
    case "up":
      return "text-emerald-600";
    case "down":
      return "text-red-600";
    case "flat":
      return "text-foreground-muted";
  }
}

export default function ActivityStats({
  totalPapers,
  weeklyDelta,
  weeklyTrend,
  pulseScore,
}: ActivityStatsProps) {
  const hasTotalPapers = totalPapers != null && totalPapers > 0;
  const hasPulseScore = pulseScore != null && pulseScore > 0;

  // SVG ring dimensions
  const ringSize = 64;
  const strokeWidth = 4;
  const radius = (ringSize - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const scoreNormalized = hasPulseScore ? Math.min(pulseScore, 10) / 10 : 0;
  const dashOffset = circumference * (1 - scoreNormalized);

  return (
    <div className="space-y-6">
      {/* Card 1 — Total in Library */}
      <div className="bg-surface-card rounded-2xl p-6 shadow-warm-sm">
        <p className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted mb-1">
          Total in Library
        </p>
        <h3
          className="text-3xl font-bold text-foreground"
          style={{ fontFamily: "var(--font-display)" }}
        >
          {hasTotalPapers ? formatNumber(totalPapers) : "\u2014"}
        </h3>
        {hasTotalPapers && (
          <div className="mt-4 flex items-center gap-1.5 text-sm font-medium">
            <TrendIcon trend={weeklyTrend} />
            <span className={trendColor(weeklyTrend)}>
              {weeklyDelta >= 0 ? "+" : ""}
              {formatNumber(Math.abs(weeklyDelta))} vs last week
            </span>
          </div>
        )}
        {hasTotalPapers && (
          <div className="mt-3">
            <span className="inline-block text-[10px] font-bold uppercase tracking-widest bg-surface-inset text-foreground-secondary rounded-full px-3 py-1">
              cs.AI
            </span>
          </div>
        )}
      </div>

      {/* Card 2 — Pulse Score */}
      <div className="bg-surface-card rounded-2xl p-6 shadow-warm-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted mb-1">
              Pulse Score
            </p>
            <h3
              className="text-3xl font-bold text-accent"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {hasPulseScore ? pulseScore.toFixed(1) : "\u2014"}
            </h3>
          </div>

          {/* Circular progress ring */}
          <div className="relative" title="Research activity pulse — higher means more active discovery">
            <svg
              width={ringSize}
              height={ringSize}
              viewBox={`0 0 ${ringSize} ${ringSize}`}
              className="-rotate-90"
            >
              {/* Background ring */}
              <circle
                cx={ringSize / 2}
                cy={ringSize / 2}
                r={radius}
                fill="none"
                stroke="var(--color-surface-inset)"
                strokeWidth={strokeWidth}
              />
              {/* Filled ring */}
              <circle
                cx={ringSize / 2}
                cy={ringSize / 2}
                r={radius}
                fill="none"
                stroke="var(--color-accent)"
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
                className="transition-all duration-700 ease-out"
              />
            </svg>
            {/* Center label */}
            <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-accent">
              {hasPulseScore ? pulseScore.toFixed(1) : "\u2014"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
