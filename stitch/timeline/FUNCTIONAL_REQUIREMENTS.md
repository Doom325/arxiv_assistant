# Timeline Page — Functional Requirements

## REQ-062: Citation-Graph Timeline (Paper-Based)
- Given a paper ID, render a directed acyclic graph of papers connected by citation edges
- Nodes represent papers; edges represent citation relationships
- Time flows left-to-right; x-position corresponds to publication date
- Seminal papers are visually prominent (larger node, distinct border)
- Ghost nodes (papers not yet imported) are shown with dashed borders
- Clicking a node opens the detail panel (REQ-067)
- Must use @xyflow/react (React Flow v12) for interactive pan/zoom/drag

## REQ-063: Topic-Based Timeline Search
- User enters a keyword, topic, or paper title in a search bar
- System calls `GET /timeline/topic?q=<query>&limit=50`
- Results render as a timeline graph identical in structure to REQ-062
- Library-only toggle filters results to papers in the user's library

## REQ-064: Empty State / Hero
- Before any search, show an inviting hero section with:
  - An icon or illustration representing timeline/graph exploration
  - Headline describing the feature
  - Subtitle with guidance
  - 3 suggestion cards (pre-seeded topics the user can click to search)
  - A "Powered by citation graph analysis" footer note

## REQ-065: Loading State
- While the API call is in flight, show a centered spinner with "Building timeline..." message

## REQ-066: Error / No-Results States
- On API error: show an error message with a red-toned icon
- On zero results: show a "No papers found" message with guidance to try a different query

## REQ-067: Node Selection Detail Panel
- When a user clicks a graph node, a detail panel appears below the graph
- Panel shows: title, abstract/summary, category badge, citation count, seminal badge, authors
- Action buttons: "Full Details" link to `/paper/<id>`, "arXiv" external link, bookmark button
- For ghost nodes: show "Import Paper" button instead of "Full Details"

## REQ-068: Graph Controls
- Zoom in, zoom out, reset view, fit view buttons in a floating toolbar
- MiniMap for navigation of large graphs

## REQ-069: Stats Pill
- Floating pill showing total node count and total citation count

## REQ-070: Year Markers
- Large, semi-transparent year watermarks positioned along the timeline axis to give temporal context

## REQ-071: Warm Design Language Compliance
- All surfaces use warm tokens: background #F5F0E8, card #EDE9E1, inset #E5E0D5
- Featured surface #2A4A1A used for hero section
- Accent #C4614A for interactive elements
- Typography: Newsreader for display headings, Inter for body
- No dark theme remnants (no bg-zinc-*, bg-black, text-white on backgrounds)
- Edges and graph chrome use warm-toned colors
