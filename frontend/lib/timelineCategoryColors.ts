/**
 * Warm-compatible category color map for timeline edges and node accents.
 * These muted, warm tones work well on the parchment (#F5F0E8) and card (#EDE9E1) surfaces.
 */
const warmCategoryColorMap: Record<string, string> = {
    "cs.AI": "#8B7355",   // warm brown
    "cs.LG": "#7B6B8A",   // dusty mauve
    "cs.CL": "#5B7B8A",   // muted teal
    "cs.CV": "#5B7A5B",   // sage green
    "cs.RO": "#B5944A",   // warm gold
    "cs.NE": "#A06B5B",   // clay
    "cs.MA": "#6B8A7B",   // muted sage
    "cs.IR": "#5B8A8A",   // ocean teal
    "cs.SI": "#B5854A",   // amber
    "cs.HC": "#8A6B7B",   // dusty rose
    "cs.CY": "#7B8A5B",   // olive
    "stat.ML": "#8A6B8A", // plum
};

const defaultWarmColor = "#9B9086"; // foreground-muted

export function getWarmCategoryColor(category: string): string {
    return warmCategoryColorMap[category] || defaultWarmColor;
}
