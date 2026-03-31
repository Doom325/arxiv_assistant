"use client";

import { Filter } from "lucide-react";

interface CitationFilterBarProps {
  category: string;
  onCategoryChange: (category: string) => void;
  startDate: string;
  onStartDateChange: (date: string) => void;
  endDate: string;
  onEndDateChange: (date: string) => void;
}

export default function CitationFilterBar({
  category,
  onCategoryChange,
  startDate,
  onStartDateChange,
  endDate,
  onEndDateChange,
}: CitationFilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 bg-surface-inset rounded-2xl p-4 shadow-warm-sm">
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-foreground-muted" />
        <select
          value={category}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="bg-surface-card text-foreground px-3 py-2 rounded-xl outline-none min-w-[160px] text-xs font-medium focus:ring-2 focus:ring-accent/30"
        >
          <option value="">All Categories</option>
          <option value="cs.AI">Artificial Intelligence</option>
          <option value="cs.LG">Machine Learning</option>
          <option value="cs.CV">Computer Vision</option>
          <option value="cs.CL">NLP / Computation</option>
          <option value="cs.RO">Robotics</option>
          <option value="cs.NE">Neural &amp; Evolutionary</option>
          <option value="cs.IR">Information Retrieval</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <label
          className="text-[10px] font-bold text-foreground-muted uppercase"
          style={{ letterSpacing: "0.08em" }}
        >
          From
        </label>
        <input
          type="date"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          className="bg-surface-card text-foreground px-3 py-2 rounded-xl outline-none text-xs focus:ring-2 focus:ring-accent/30"
        />
      </div>

      <div className="flex items-center gap-2">
        <label
          className="text-[10px] font-bold text-foreground-muted uppercase"
          style={{ letterSpacing: "0.08em" }}
        >
          To
        </label>
        <input
          type="date"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          className="bg-surface-card text-foreground px-3 py-2 rounded-xl outline-none text-xs focus:ring-2 focus:ring-accent/30"
        />
      </div>
    </div>
  );
}
