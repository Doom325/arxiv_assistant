"use client";

import { useCallback, useMemo } from "react";
import {
    ReactFlow,
    MiniMap,
    type Node,
    type Edge,
    useNodesState,
    useEdgesState,
    type NodeMouseHandler,
    useReactFlow,
    ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
    Plus,
    Minus,
    RotateCcw,
    Maximize2,
} from "lucide-react";

import TimelineNodeComponent, {
    type TimelinePaperData,
} from "./TimelineNode";
import { type TimelineResponse } from "../lib/api";
import { getWarmCategoryColor } from "../lib/timelineCategoryColors";

// Layout constants
const CANVAS_WIDTH = 2400;
const NODE_HEIGHT = 100;
const LEFT_PAD = 100;
const RIGHT_PAD = 100;
const TOP_PAD = 160;

/* ── Year Marker Node ── */

function YearMarkerNode({ data }: { data: { year: number } }) {
    return (
        <div
            className="select-none pointer-events-none"
            style={{
                fontFamily: "var(--font-display)",
                fontSize: "8rem",
                fontWeight: 800,
                letterSpacing: "-0.05em",
                opacity: 0.1,
                color: "var(--color-foreground-muted)",
                lineHeight: 1,
            }}
        >
            {data.year}
        </div>
    );
}

const nodeTypes = {
    paper: TimelineNodeComponent,
    yearMarker: YearMarkerNode,
};

/* ── Custom Controls ── */

function CustomControls() {
    const { zoomIn, zoomOut, fitView } = useReactFlow();

    const resetView = useCallback(() => {
        fitView({ padding: 0.3, maxZoom: 1.2, duration: 300 });
    }, [fitView]);

    const buttons = [
        {
            icon: <Plus className="w-4 h-4" />,
            action: () => zoomIn({ duration: 200 }),
            label: "Zoom in",
        },
        {
            icon: <Minus className="w-4 h-4" />,
            action: () => zoomOut({ duration: 200 }),
            label: "Zoom out",
        },
        null, // divider
        {
            icon: <RotateCcw className="w-4 h-4" />,
            action: resetView,
            label: "Reset view",
        },
        {
            icon: <Maximize2 className="w-4 h-4" />,
            action: () => fitView({ duration: 300 }),
            label: "Fit view",
        },
    ];

    return (
        <div
            className="absolute bottom-6 left-6 z-10
                flex items-center gap-1.5 p-1.5
                bg-[var(--color-surface-card)]/90 backdrop-blur rounded-xl
                border border-[#D5CFC4] shadow-warm"
        >
            {buttons.map((btn, i) => {
                if (btn === null) {
                    return (
                        <div
                            key={`div-${i}`}
                            className="w-px h-4 bg-[#D5CFC4] mx-0.5"
                        />
                    );
                }
                return (
                    <button
                        key={btn.label}
                        onClick={btn.action}
                        title={btn.label}
                        className="w-10 h-10 flex items-center
                            justify-center hover:bg-[var(--color-surface-inset)]
                            rounded-lg transition-colors
                            text-[var(--color-foreground-secondary)]"
                    >
                        {btn.icon}
                    </button>
                );
            })}
        </div>
    );
}

/* ── Stats Pill ── */

function StatsPill(
    { nodeCount, citationCount }: {
        nodeCount: number;
        citationCount: number;
    },
) {
    return (
        <div
            className="absolute top-4 right-4 z-10
                px-4 py-2 bg-[var(--color-background)]/80 backdrop-blur
                border border-[#D5CFC4] rounded-full
                flex items-center gap-3"
        >
            <span
                className="text-[10px] font-bold text-[var(--color-foreground-muted)]
                    tracking-widest uppercase"
            >
                Nodes: {nodeCount}
            </span>
            <div className="w-px h-3 bg-[#D5CFC4]" />
            <span
                className="text-[10px] font-bold text-[var(--color-foreground-muted)]
                    tracking-widest uppercase"
            >
                Citations: {citationCount}
            </span>
        </div>
    );
}

/* ── Layout computation ── */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function computeLayout(data: TimelineResponse): { paperNodes: any[]; yearNodes: any[] } {
    const nodes = data.nodes;
    if (nodes.length === 0) return { paperNodes: [], yearNodes: [] };

    // Parse dates and sort by date
    const withDates = nodes.map((n, i) => ({
        node: n,
        index: i,
        date: n.published_date ? new Date(n.published_date) : null,
        year: n.published_date ? new Date(n.published_date).getFullYear() : null,
    }));

    // Get date range
    const validDates = withDates.filter((w) => w.date !== null);
    if (validDates.length === 0) {
        // No dates — just lay out in a grid
        const paperNodes = nodes.map((n, i) => ({
            id: n.paper_id != null ? String(n.paper_id) : `ghost-${n.arxiv_id}-${i}`,
            type: "paper" as const,
            position: { x: (i % 5) * 350 + LEFT_PAD, y: Math.floor(i / 5) * (NODE_HEIGHT + 30) + TOP_PAD },
            data: nodeToData(n),
        }));
        return { paperNodes, yearNodes: [] };
    }

    const minDate = Math.min(...validDates.map((w) => w.date!.getTime()));
    const maxDate = Math.max(...validDates.map((w) => w.date!.getTime()));
    const dateRange = maxDate - minDate || 1;

    // Sort nodes by date for row assignment
    const sorted = [...withDates].sort((a, b) => {
        const ta = a.date?.getTime() ?? minDate;
        const tb = b.date?.getTime() ?? minDate;
        return ta - tb;
    });

    // Compute x from date, y using staggered rows to avoid overlap
    const usableWidth = CANVAS_WIDTH - LEFT_PAD - RIGHT_PAD;
    const positions: { x: number; y: number }[] = new Array(nodes.length);

    // Track occupied y-ranges per x-region to avoid overlap
    const occupiedSlots: { x: number; y: number }[] = [];
    const NODE_W = 260;
    const NODE_H = NODE_HEIGHT;

    for (const item of sorted) {
        const t = item.date ? item.date.getTime() : minDate;
        const xFrac = (t - minDate) / dateRange;
        const x = LEFT_PAD + xFrac * usableWidth;

        // Find a y position that doesn't collide with existing nodes nearby
        let y = TOP_PAD;
        let placed = false;
        for (let attempt = 0; attempt < 20; attempt++) {
            const candidateY = TOP_PAD + attempt * (NODE_H + 20);
            const collides = occupiedSlots.some(
                (slot) =>
                    Math.abs(slot.x - x) < NODE_W &&
                    Math.abs(slot.y - candidateY) < NODE_H,
            );
            if (!collides) {
                y = candidateY;
                placed = true;
                break;
            }
        }
        if (!placed) {
            y = TOP_PAD + occupiedSlots.length * (NODE_H + 20);
        }

        occupiedSlots.push({ x, y });
        positions[item.index] = { x, y };
    }

    // Build paper nodes
    const paperNodes = nodes.map((n, i) => ({
        id: n.paper_id != null ? String(n.paper_id) : `ghost-${n.arxiv_id}-${i}`,
        type: "paper" as const,
        position: positions[i],
        data: nodeToData(n),
    }));

    // Build year watermark nodes — only unique years, spaced across the timeline
    const minYear = Math.min(...validDates.map((w) => w.year!));
    const maxYear = Math.max(...validDates.map((w) => w.year!));

    // Pick representative years (skip some if range is large)
    const yearSpan = maxYear - minYear;
    let step = 1;
    if (yearSpan > 10) step = 3;
    else if (yearSpan > 5) step = 2;

    const yearNodes: Node[] = [];
    for (let yr = minYear; yr <= maxYear; yr += step) {
        const yearFrac = (yr - minYear) / (maxYear - minYear || 1);
        const x = LEFT_PAD + yearFrac * usableWidth;

        yearNodes.push({
            id: `year-${yr}`,
            type: "yearMarker",
            position: { x: x - 40, y: -20 },
            data: { year: yr },
            selectable: false,
            draggable: false,
            connectable: false,
        });
    }

    // Always include the max year if not already included
    if ((maxYear - minYear) % step !== 0) {
        const x = LEFT_PAD + usableWidth;
        yearNodes.push({
            id: `year-${maxYear}`,
            type: "yearMarker",
            position: { x: x - 40, y: -20 },
            data: { year: maxYear },
            selectable: false,
            draggable: false,
            connectable: false,
        });
    }

    return { paperNodes, yearNodes };
}

function nodeToData(n: TimelineResponse["nodes"][0]): TimelinePaperData {
    return {
        title: n.title,
        arxiv_id: n.arxiv_id,
        published_date: n.published_date,
        category: n.category,
        citation_count: n.citation_count,
        is_seminal: n.is_seminal,
        is_in_library: n.is_in_library,
        is_ghost: n.is_ghost,
    };
}

/* ── Main Graph (inner) ── */

interface TimelineGraphProps {
    data: TimelineResponse;
    onNodeSelect?: (paperId: number) => void;
}

function TimelineGraphInner(
    { data, onNodeSelect }: TimelineGraphProps,
) {
    const { paperNodes, yearNodes } = useMemo(
        () => computeLayout(data),
        [data],
    );

    const initialNodes: Node[] = useMemo(
        () => [...yearNodes, ...paperNodes],
        [paperNodes, yearNodes],
    );

    // Edges
    const initialEdges: Edge[] = useMemo(() => {
        const categoryMap = new Map<string, string>();
        data.nodes.forEach((n) => {
            categoryMap.set(
                String(n.paper_id),
                n.category || "cs.AI",
            );
        });

        return data.edges.map((e, i) => {
            const sourceCategory =
                categoryMap.get(String(e.source_paper_id))
                || "cs.AI";
            const catColor = getWarmCategoryColor(sourceCategory);
            const isRelated = e.edge_type === "related";

            return {
                id: `e-${e.source_paper_id}-`
                    + `${e.target_paper_id}-${i}`,
                source: String(e.target_paper_id),
                target: String(e.source_paper_id),
                type: "default",
                animated: isRelated,
                style: {
                    stroke: catColor,
                    strokeWidth: isRelated ? 1 : 1.5,
                    opacity: isRelated ? 0.4 : 0.6,
                    strokeDasharray: isRelated
                        ? "5 5"
                        : undefined,
                },
                markerEnd: {
                    type: "arrowclosed" as const,
                    color: catColor,
                    width: 12,
                    height: 12,
                },
            };
        });
    }, [data.edges, data.nodes]);

    const [nodes, , onNodesChange] = useNodesState(
        initialNodes,
    );
    const [edges, , onEdgesChange] = useEdgesState(
        initialEdges,
    );

    const handleNodeClick: NodeMouseHandler = useCallback(
        (_event, node) => {
            onNodeSelect?.(Number(node.id));
        },
        [onNodeSelect],
    );

    // Minimap node color
    const minimapNodeColor = useCallback((node: Node) => {
        if (node.type === "yearMarker") return "transparent";
        const category =
            (node.data as unknown as TimelinePaperData)
                ?.category || "cs.AI";
        return getWarmCategoryColor(category);
    }, []);

    // Stats
    const totalCitations = useMemo(
        () =>
            data.nodes.reduce(
                (sum, n) => sum + (n.citation_count || 0),
                0,
            ),
        [data.nodes],
    );

    if (data.nodes.length === 0) {
        return null;
    }

    return (
        <div
            className="relative w-full h-[650px] bg-[var(--color-surface-card)]
                rounded-2xl overflow-hidden shadow-warm border border-[#D5CFC4]"
        >
            {/* Stats pill */}
            <StatsPill
                nodeCount={data.nodes.length}
                citationCount={totalCitations}
            />

            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={handleNodeClick}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{
                    padding: 0.3,
                    maxZoom: 1.2,
                }}
                minZoom={0.2}
                maxZoom={2.5}
                proOptions={{ hideAttribution: true }}
                style={{
                    backgroundImage:
                        "radial-gradient("
                        + "#D5CFC4 1px, transparent 0)",
                    backgroundSize: "40px 40px",
                }}
            >
                {/* Minimap */}
                <MiniMap
                    nodeColor={minimapNodeColor}
                    maskColor="rgba(245, 240, 232, 0.6)"
                    style={{
                        backgroundColor: "#E5E0D5",
                        border: "1px solid #D5CFC4",
                        borderRadius: "0.75rem",
                    }}
                    pannable
                    zoomable
                />

                {/* Custom controls */}
                <CustomControls />
            </ReactFlow>
        </div>
    );
}

/* ── Exported wrapper with ReactFlowProvider ── */

export default function TimelineGraph(
    props: TimelineGraphProps,
) {
    return (
        <ReactFlowProvider>
            <TimelineGraphInner {...props} />
        </ReactFlowProvider>
    );
}
