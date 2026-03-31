"use client";

interface AnalyticsHeroProps {
  totalPapers: number;
  todayCount: number;
  yesterdayCount: number;
  libraryCount: number;
  categoryCount: number;
}

function formatNumber(n: number): string {
  if (n == null || isNaN(n)) return "\u2014";
  return n.toLocaleString("en-US");
}

function StatBlock({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center px-6 py-4">
      <p className="font-display text-3xl md:text-4xl font-bold text-on-featured leading-none">
        {value}
      </p>
      <p
        className="text-on-featured/70 text-[10px] font-bold uppercase mt-2"
        style={{ letterSpacing: "0.08em" }}
      >
        {label}
      </p>
    </div>
  );
}

export default function AnalyticsHero({
  totalPapers,
  todayCount,
  yesterdayCount,
  libraryCount,
  categoryCount,
}: AnalyticsHeroProps) {
  return (
    <div className="bg-surface-featured rounded-2xl p-8 md:p-10 shadow-warm">
      {/* Page title */}
      <h1 className="font-display text-on-featured mb-8">
        <span className="text-3xl md:text-4xl font-light">Research</span>{" "}
        <span className="text-3xl md:text-4xl font-bold italic">Analytics</span>
      </h1>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatBlock value={formatNumber(totalPapers)} label="Total Papers" />
        <StatBlock value={formatNumber(todayCount)} label="Today" />
        <StatBlock value={formatNumber(yesterdayCount)} label="Yesterday" />
        <StatBlock value={formatNumber(libraryCount)} label="In Library" />
        <StatBlock value={formatNumber(categoryCount)} label="Categories" />
      </div>
    </div>
  );
}
