"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { tokens } from "@/lib/tokens";

interface CategoryChartProps {
  categoryData: Array<{ category: string; count: number }>;
  dailyData: Array<{ date: string; count: number }>;
}

type TabValue = "category" | "day";

const TOOLTIP_STYLE: React.CSSProperties = {
  background: tokens.colors.surfaceCard,
  border: "none",
  borderRadius: "12px",
  boxShadow: "0 4px 24px rgba(60,40,20,0.08)",
  fontSize: "12px",
  color: tokens.colors.foreground,
  padding: "8px 12px",
};

export default function CategoryChart({
  categoryData,
  dailyData,
}: CategoryChartProps) {
  const [activeTab, setActiveTab] = useState<TabValue>("category");

  const hasCategory = categoryData.length > 0;
  const hasDaily = dailyData.length > 0;
  const isEmpty = !hasCategory && !hasDaily;

  return (
    <div className="bg-surface-card rounded-2xl p-6 shadow-warm-sm">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="font-display font-bold text-foreground text-lg">
            Category Distribution
          </h2>
          <p className="text-foreground-muted text-xs mt-0.5">
            Last 30 days of research activity
          </p>
        </div>

        {/* Tab toggle */}
        <div className="flex bg-surface-inset rounded-full p-0.5">
          <button
            onClick={() => setActiveTab("category")}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              activeTab === "category"
                ? "bg-accent text-on-accent"
                : "text-foreground-muted hover:text-foreground-secondary"
            }`}
          >
            By Category
          </button>
          <button
            onClick={() => setActiveTab("day")}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              activeTab === "day"
                ? "bg-accent text-on-accent"
                : "text-foreground-muted hover:text-foreground-secondary"
            }`}
          >
            By Day
          </button>
        </div>
      </div>

      {/* Chart area */}
      {isEmpty ? (
        <div className="flex items-center justify-center h-[240px] text-foreground-muted text-sm italic">
          No data available
        </div>
      ) : activeTab === "category" ? (
        <CategoryBarChart data={categoryData} />
      ) : (
        <DailyAreaChart data={dailyData} />
      )}
    </div>
  );
}

/* ── By Category: horizontal bar chart ── */

function CategoryBarChart({
  data,
}: {
  data: Array<{ category: string; count: number }>;
}) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[240px] text-foreground-muted text-sm italic">
        No category data available
      </div>
    );
  }

  // Sort descending by count for visual clarity
  const sorted = [...data].sort((a, b) => b.count - a.count);

  return (
    <div className="h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={sorted}
          layout="vertical"
          margin={{ top: 0, right: 16, bottom: 0, left: 0 }}
        >
          <CartesianGrid
            horizontal={false}
            stroke={tokens.colors.surfaceInset}
            strokeDasharray="3 3"
          />
          <XAxis
            type="number"
            tick={{ fontSize: 11, fill: tokens.colors.foregroundMuted }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="category"
            tick={{ fontSize: 11, fill: tokens.colors.foregroundMuted }}
            axisLine={false}
            tickLine={false}
            width={44}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            cursor={{ fill: `${tokens.colors.surfaceInset}80` }}
            formatter={(value: number) => [value, "Papers"]}
          />
          <Bar
            dataKey="count"
            fill={tokens.colors.accent}
            radius={[0, 4, 4, 0]}
            barSize={18}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ── By Day: sparkline area chart ── */

function DailyAreaChart({
  data,
}: {
  data: Array<{ date: string; count: number }>;
}) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[240px] text-foreground-muted text-sm italic">
        No daily data available
      </div>
    );
  }

  return (
    <div className="h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 8, right: 16, bottom: 0, left: 0 }}
        >
          <defs>
            <linearGradient id="dailyGradient" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                stopColor={tokens.colors.accent}
                stopOpacity={0.1}
              />
              <stop
                offset="100%"
                stopColor={tokens.colors.accent}
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <CartesianGrid
            vertical={false}
            stroke={tokens.colors.surfaceInset}
            strokeDasharray="3 3"
          />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: tokens.colors.foregroundMuted }}
            axisLine={false}
            tickLine={false}
            interval={2}
            tickFormatter={(value: string) => {
              const d = new Date(value);
              return d.toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
              });
            }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: tokens.colors.foregroundMuted }}
            axisLine={false}
            tickLine={false}
            width={32}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            cursor={{ stroke: tokens.colors.foregroundMuted, strokeWidth: 1 }}
            labelFormatter={(label: string) => {
              const d = new Date(label);
              return d.toLocaleDateString("en-US", {
                weekday: "short",
                month: "short",
                day: "numeric",
              });
            }}
            formatter={(value: number) => [value, "Papers"]}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke={tokens.colors.accent}
            strokeWidth={2}
            fill="url(#dailyGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
