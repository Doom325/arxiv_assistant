const categoryColorMap: Record<string, { bg: string; text: string; border: string; accent: string }> = {
    "cs.AI": { bg: "bg-indigo-500/10", text: "text-indigo-300", border: "border-indigo-500/30", accent: "#6366f1" },
    "cs.LG": { bg: "bg-violet-500/10", text: "text-violet-300", border: "border-violet-500/30", accent: "#8b5cf6" },
    "cs.CL": { bg: "bg-sky-500/10", text: "text-sky-300", border: "border-sky-500/30", accent: "#0ea5e9" },
    "cs.CV": { bg: "bg-emerald-500/10", text: "text-emerald-300", border: "border-emerald-500/30", accent: "#10b981" },
    "cs.RO": { bg: "bg-amber-500/10", text: "text-amber-300", border: "border-amber-500/30", accent: "#f59e0b" },
    "cs.NE": { bg: "bg-rose-500/10", text: "text-rose-300", border: "border-rose-500/30", accent: "#f43f5e" },
    "cs.MA": { bg: "bg-teal-500/10", text: "text-teal-300", border: "border-teal-500/30", accent: "#14b8a6" },
    "cs.IR": { bg: "bg-cyan-500/10", text: "text-cyan-300", border: "border-cyan-500/30", accent: "#06b6d4" },
    "cs.SI": { bg: "bg-orange-500/10", text: "text-orange-300", border: "border-orange-500/30", accent: "#f97316" },
    "cs.HC": { bg: "bg-pink-500/10", text: "text-pink-300", border: "border-pink-500/30", accent: "#ec4899" },
    "cs.CY": { bg: "bg-lime-500/10", text: "text-lime-300", border: "border-lime-500/30", accent: "#84cc16" },
    "stat.ML": { bg: "bg-fuchsia-500/10", text: "text-fuchsia-300", border: "border-fuchsia-500/30", accent: "#d946ef" },
};

const defaultColor = { bg: "bg-zinc-500/10", text: "text-zinc-300", border: "border-zinc-500/30", accent: "#71717a" };

export function getCategoryColor(category: string) {
    return categoryColorMap[category] || defaultColor;
}

/* Warm, muted accent colors per category — used for card accent strips and chips */
export const categoryAccentColors: Record<string, string> = {
    'cs.AI': '#C4614A',   // terracotta (primary accent)
    'cs.CL': '#2A4A1A',   // forest green
    'cs.LG': '#8B6914',   // warm amber/gold
    'cs.CV': '#7A4B8A',   // warm plum
    'cs.RO': '#4A7A8B',   // warm teal
    'cs.NE': '#B85C3A',   // burnt sienna
    'cs.MA': '#5A7A3A',   // olive green
    'cs.IR': '#9B5B5B',   // warm rose
    'cs.SE': '#6B7A3A',   // sage
    'cs.HC': '#7A6B5A',   // warm taupe
    'cs.CY': '#5A6B7A',   // warm slate blue
};

export function getCategoryAccent(category: string): string {
    return categoryAccentColors[category] || '#C4614A';
}

export function estimateReadingTime(text: string | undefined | null): string {
    if (!text) return "";
    const words = text.split(/\s+/).length;
    const minutes = Math.ceil(words / 200);
    return `${minutes} min read`;
}
