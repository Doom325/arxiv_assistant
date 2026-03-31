"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { tokens } from "@/lib/tokens";

interface CategoryDistChartProps {
  data: Array<{ category: string; count: number }>;
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

export default function CategoryDistChart({ data }: CategoryDistChartProps) {
  const isEmpty = data.length === 0;

  // Sort by count descending and take top 10
  const sorted = [...data].sort((a, b) => b.count - a.count).slice(0, 10);

  return (
    <div className="bg-surface-card rounded-2xl p-6 shadow-warm-sm">
      {/* Header */}
      <div className="mb-6">
        <h2 className="font-display font-bold text-foreground text-lg">
          Category Distribution
        </h2>
        <p className="text-foreground-muted text-xs mt-0.5">
          Last 30 days of research activity
        </p>
      </div>

      {/* Chart */}
      {isEmpty ? (
        <div className="flex items-center justify-center h-48 text-foreground-muted text-sm italic font-display">
          No category data available yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={sorted}
            layout="vertical"
            margin={{ top: 4, right: 12, left: 10, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={tokens.colors.surfaceInset}
              horizontal={false}
            />
            <XAxis
              type="number"
              tick={{ fill: tokens.colors.foregroundMuted, fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <YAxis
              type="category"
              dataKey="category"
              tick={{ fill: tokens.colors.foregroundSecondary, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={60}
            />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar
              dataKey="count"
              fill={tokens.colors.accent}
              radius={[0, 6, 6, 0]}
              barSize={16}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
