"use client";

import { ChevronDown, ChevronUp } from "lucide-react";

interface DashboardDateGroupProps {
  label: string; // "Today March 25" or "Yesterday March 24"
  itemCount: number;
  isCollapsed: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  badge?: string; // e.g. "24 NEW PAPERS"
}

export default function DashboardDateGroup({
  label,
  itemCount,
  isCollapsed,
  onToggle,
  children,
  badge,
}: DashboardDateGroupProps) {
  return (
    <section>
      {/* ── Header row ──────────────────────────────────── */}
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center gap-3 group cursor-pointer py-2"
        aria-expanded={!isCollapsed}
      >
        {/* Left warm rule */}
        <span className="h-px flex-1 bg-surface-inset" aria-hidden="true" />

        {/* Date label */}
        <span className="text-xs uppercase tracking-[0.2em] text-foreground-muted font-medium whitespace-nowrap">
          {label}
        </span>

        {/* Item count */}
        <span className="text-xs uppercase tracking-[0.2em] text-foreground-muted/60 whitespace-nowrap">
          {itemCount} {itemCount === 1 ? "paper" : "papers"}
        </span>

        {/* Optional badge */}
        {badge && (
          <span className="bg-accent/15 text-accent rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-wider font-bold whitespace-nowrap">
            {badge}
          </span>
        )}

        {/* Collapse toggle */}
        {isCollapsed ? (
          <ChevronDown className="h-3.5 w-3.5 text-foreground-muted group-hover:text-foreground transition-colors shrink-0" />
        ) : (
          <ChevronUp className="h-3.5 w-3.5 text-foreground-muted group-hover:text-foreground transition-colors shrink-0" />
        )}

        {/* Right warm rule */}
        <span className="h-px flex-1 bg-surface-inset" aria-hidden="true" />
      </button>

      {/* ── Collapsible children ─────────────────────────── */}
      <div
        className="overflow-hidden transition-all duration-300 ease-in-out"
        style={{
          maxHeight: isCollapsed ? 0 : "9999px",
          opacity: isCollapsed ? 0 : 1,
        }}
      >
        <div className="pt-4">{children}</div>
      </div>
    </section>
  );
}
