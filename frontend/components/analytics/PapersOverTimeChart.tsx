"use client";

import { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { tokens } from "@/lib/tokens";

interface PapersOverTimeChartProps {
  data: Array<{ date: string; count: number }>;
  onGranularityChange: (granularity: "day" | "week" | "month") => void;
  granularity: "day" | "week" | "month";
}

const TOOLTIP_STYLE: React.CSSProperties = {
  background: tokens.colors.surfaceCard,
  border: "none",
  borderRadius: "12px",
  boxShadow: "0 4px 24px rgba(60,40,20,0.08)",
  fontSize: "12px",
  color: tokens.colors.foreground,
  padding: "8px 12px",
};

type GranularityValue = "day" | "week" | "month";

export default function PapersOverTimeChart({
  data,
  onGranularityChange,
  granularity,
}: PapersOverTimeChartProps) {
  const isEmpty = data.length === 0;

  const granularityOptions: { value: GranularityValue; label: string }[] = [
    { value: "day", label: "Day" },
    { value: "week", label: "Week" },
    { value: "month", label: "Month" },
  ];

  return (
    <div className="bg-surface-card rounded-2xl p-6 shadow-warm-sm">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="font-display font-bold text-foreground text-lg">
            Papers Over Time
          </h2>
          <p className="text-foreground-muted text-xs mt-0.5">
            Ingestion volume trend
          </p>
        </div>

        {/* Granularity toggle */}
        <div className="flex bg-surface-inset rounded-full p-0.5">
          {granularityOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onGranularityChange(opt.value)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                granularity === opt.value
                  ? "bg-accent text-on-accent"
                  : "text-foreground-muted hover:text-foreground-secondary"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      {isEmpty ? (
        <div className="flex items-center justify-center h-48 text-foreground-muted text-sm italic font-display">
          No data available yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="areaFillAnalytics" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={tokens.colors.accent} stopOpacity={0.25} />
                <stop offset="95%" stopColor={tokens.colors.accent} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={tokens.colors.surfaceInset}
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tick={{ fill: tokens.colors.foregroundMuted, fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: string) => {
                const d = new Date(v);
                return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
              }}
            />
            <YAxis
              tick={{ fill: tokens.colors.foregroundMuted, fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Area
              type="monotone"
              dataKey="count"
              stroke={tokens.colors.accent}
              strokeWidth={2}
              fill="url(#areaFillAnalytics)"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
