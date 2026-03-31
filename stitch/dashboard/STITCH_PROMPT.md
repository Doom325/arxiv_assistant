# Stitch Prompt: Dashboard Page

## Paste this into Stitch:

Design the dashboard page for an AI research paper assistant. This is the researcher's morning briefing -- the first screen they open each day. The emotional tone is calm editorial authority: imagine a beautifully typeset research digest laid out on warm parchment, not a SaaS metrics dashboard. The page should answer three questions at a glance: "What's new?", "How active is my field?", and "What should I read next?" Use a warm cream background with tonal depth (no borders on cards -- depth comes from background shifts). Headlines use a variable-weight serif where context words are light and key phrases are bold/heavy. One single featured element on the page (the lead paper or a "today's briefing" section) may use a deep rich surface (forest green, deep navy, or warm charcoal) to create a strong focal point. All other interactive elements (links, buttons, active states) use one warm accent color (terracotta, amber, or warm red). The layout, information architecture, and interaction patterns are entirely yours to invent -- you are not constrained to any grid or card system. Treat this as a blank canvas. Prioritize generous whitespace, large readable type, and an unhurried reading experience. The page should feel like quality print editorial adapted for screen.

**Must include -- every one of these capabilities must be accessible somewhere on this page:**

1. A prominent featured paper ("lead story") with title, rendered abstract excerpt, publication date, estimated reading time, category tags, and a link to the full detail page
2. A chronological feed of recent papers grouped by publication date, with collapsible date sections and a count of papers per day
3. Each paper in the feed shows title, categories, and publication date; each is clickable to its detail page
4. A search input for free-text search across all indexed papers
5. Filter controls: category selector (cs.AI, cs.LG, cs.CL, cs.CV, cs.RO, cs.NE, cs.MA, cs.IR, cs.SI, cs.HC, cs.CY), date range (start/end), and sort order (relevance, newest, title)
6. A reset-filters action to return to the default view
7. A manual refresh action to pull newly indexed papers
8. A toggle between a spatial/grid layout and a compact/list layout for the paper feed
9. A stat showing total papers in the primary category (cs.AI)
10. A stat showing yesterday's paper count with an up/flat/down trend indicator
11. A sparkline or mini time-series showing papers per day over 14 days
12. A proportional category breakdown (heatmap, tag cloud, or bar -- your choice) showing sub-category distribution over the past 30 days
13. A bookmark action on every paper (including the featured paper) that works without navigating away
14. A quick-peek capability: tapping any paper opens a slide-over or overlay showing title, abstract, AI-generated summary, and reading time, with previous/next navigation
15. A welcoming empty state when no papers exist (inviting, not error-like)
16. A "no results" state for empty searches with a clear-filters option
17. Infinite scroll loading indicator at the bottom of the feed
18. A keyboard shortcut reference overlay accessible from the page

## Design Language Reference (include this after the main prompt):

### Color
- **Page surface:** warm cream in the #F0EAE0 to #FAF6EF range. Never pure white, never cool grey.
- **Card surfaces:** one tonal step warmer/darker than the page. Depth through background shift, never through borders.
- **Nested/inset elements:** one further tonal step.
- **Accent color:** ONE warm accent (terracotta, amber, warm red) used ONLY on interactive elements -- links, buttons, focus rings, active states. Never decorative.
- **Featured surface:** ONE element per page may use a deep rich color (forest green, deep navy, warm charcoal, deep plum). This is the single strong focal point.
- **No** dark backgrounds as primary surface, no cool greys, no multiple accent colors, no gradient backgrounds.

### Typography
- **Headlines:** variable-weight serif (Fraunces, Playfair Display, Cormorant, or similar). Mix weights within a single headline -- light/thin for context words, bold/heavy for the key phrase.
- **Body and UI:** humanist sans-serif (Inter, DM Sans, or similar). Clean, readable.
- **Descriptions/annotations:** italic serif or italic sans for supporting text and helper copy.
- **Metadata labels:** uppercase with generous letter-spacing (+0.06em to +0.10em). Small but authoritative.
- **Scale:** go larger than expected. Headlines command the page. Generous whitespace between type blocks.

### Space
- Between major sections: 48px minimum
- Card internal padding: 24px minimum
- Between cards in a grid: 16-20px
- Body line height: 1.65-1.75
- When in doubt, add more space.

### Surfaces and Depth
- Tonal hierarchy, no structural borders on cards or panels.
- Shadows when used: warm-tinted, very diffuse (e.g., rgba(60, 40, 20, 0.08)).
- Card corners: 16px minimum radius. Floating panels: 20px+. Chips/badges: pill shape.

### Interaction States
- Active/selected: accent color marks the active item. No heavy background fills -- prefer left-border accent or text color change.
- Hover: subtle one-step tonal shift or soft shadow. Never jarring.
- Empty states: intentional and inviting, using the display serif, generous space, and a simple visual motif. "This is ready for me" not "something is missing."
