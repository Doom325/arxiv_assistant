"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
    LayoutDashboard,
    LayoutList,
    BookOpen,
    MessageSquare,
    Layers,
    GitBranch,
    BarChart3,
    Settings,
    FileText,
    Command as CommandIcon,
} from "lucide-react";
import { api, Paper } from "../lib/api";
import { ALL_NAV_ROUTES, triggerOpenAddPaper } from "../lib/navigation";
import { getCategoryColor } from "../lib/categoryColors";

const ROUTE_ICONS: Record<string, typeof LayoutList> = {
    Dashboard: LayoutDashboard,
    Queue: LayoutList,
    Library: BookOpen,
    Chat: MessageSquare,
    Patterns: Layers,
    Timeline: GitBranch,
    Analysis: BarChart3,
    Settings: Settings,
};

export const pages = ALL_NAV_ROUTES.map((route) => ({
    name: route.name,
    href: route.href,
    icon: ROUTE_ICONS[route.name] ?? LayoutList,
}));

export default function CommandPalette() {
    const router = useRouter();
    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<Paper[]>([]);
    const [searching, setSearching] = useState(false);
    const debounceRef = useRef<NodeJS.Timeout | null>(null);

    // Toggle with Cmd+K / Ctrl+K
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "k") {
                e.preventDefault();
                setOpen((prev) => !prev);
            }
            if (e.key === "Escape") {
                setOpen(false);
            }
        };
        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, []);

    // Debounced paper search
    const searchPapers = useCallback(
        (q: string) => {
            if (debounceRef.current) clearTimeout(debounceRef.current);
            if (!q.trim()) {
                setResults([]);
                setSearching(false);
                return;
            }
            setSearching(true);
            debounceRef.current = setTimeout(async () => {
                try {
                    const data = await api.searchPapers(q, 0, 8);
                    const transformed: Paper[] = (data || []).map(
                        (p: Paper & { category?: string }) => ({
                            ...p,
                            id: p.arxiv_id || `paper-${p.id}`,
                            db_id: p.db_id ?? (typeof p.id === "number" ? p.id : undefined),
                            categories: Array.isArray(p.categories)
                                ? p.categories
                                : [p.category || "cs.AI"],
                        }),
                    );
                    setResults(transformed);
                } catch {
                    setResults([]);
                } finally {
                    setSearching(false);
                }
            }, 200);
        },
        [],
    );

    useEffect(() => {
        searchPapers(query);
    }, [query, searchPapers]);

    // Reset on close
    useEffect(() => {
        if (!open) {
            setQuery("");
            setResults([]);
        }
    }, [open]);

    const navigate = (href: string) => {
        setOpen(false);
        router.push(href);
    };

    return (
        <AnimatePresence>
            {open && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        className="fixed inset-0 z-[100] bg-foreground/20 backdrop-blur-sm"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setOpen(false)}
                    />

                    {/* Palette */}
                    <motion.div
                        className="fixed inset-0 z-[101] flex items-start justify-center pt-[20vh]"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 400, damping: 25 }}
                    >
                        <Command
                            className="w-full max-w-xl bg-surface-card shadow-warm-lg rounded-2xl overflow-hidden"
                            loop
                        >
                            <div className="flex items-center px-4 border-b border-surface-inset/50">
                                <CommandIcon className="h-4 w-4 text-foreground-muted mr-2 shrink-0" />
                                <Command.Input
                                    value={query}
                                    onValueChange={setQuery}
                                    placeholder="Search papers, actions, pages..."
                                    className="w-full bg-transparent py-4 text-sm text-foreground placeholder:text-foreground-muted focus:outline-none"
                                />
                                <kbd className="hidden sm:inline-flex px-2 py-0.5 text-[10px] font-mono text-foreground-muted bg-surface-inset rounded border border-surface-inset/50">
                                    ESC
                                </kbd>
                            </div>

                            <Command.List className="max-h-80 overflow-y-auto p-2">
                                <Command.Empty className="py-6 text-center text-sm text-foreground-muted">
                                    {searching ? "Searching..." : "No results found."}
                                </Command.Empty>

                                {/* Pages */}
                                <Command.Group
                                    heading="Pages"
                                    className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-foreground-secondary [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider"
                                >
                                    {pages.map((page) => (
                                        <Command.Item
                                            key={page.href}
                                            value={`page: ${page.name}`}
                                            onSelect={() => navigate(page.href)}
                                            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-foreground-secondary cursor-pointer data-[selected=true]:bg-surface-inset data-[selected=true]:text-accent transition-colors"
                                        >
                                            <page.icon className="h-4 w-4 text-foreground-muted" />
                                            {page.name}
                                        </Command.Item>
                                    ))}
                                </Command.Group>

                                {/* Paper results */}
                                {results.length > 0 && (
                                    <Command.Group
                                        heading="Papers"
                                        className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-foreground-secondary [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider"
                                    >
                                        {results.map((paper) => {
                                            const cc = getCategoryColor(paper.categories?.[0] || "cs.AI");
                                            return (
                                                <Command.Item
                                                    key={paper.id}
                                                    value={paper.title}
                                                    onSelect={() => navigate(`/paper/${paper.db_id || paper.id}`)}
                                                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-foreground-secondary cursor-pointer data-[selected=true]:bg-surface-inset data-[selected=true]:text-accent transition-colors"
                                                >
                                                    <FileText className="h-4 w-4 text-foreground-muted shrink-0" />
                                                    <span className="truncate flex-1">{paper.title}</span>
                                                    <span
                                                        className={`px-2 py-0.5 ${cc.bg} ${cc.text} border ${cc.border} text-[10px] rounded-full shrink-0`}
                                                    >
                                                        {paper.categories?.[0]}
                                                    </span>
                                                </Command.Item>
                                            );
                                        })}
                                    </Command.Group>
                                )}

                                {/* Actions */}
                                <Command.Group
                                    heading="Actions"
                                    className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-foreground-secondary [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider"
                                >
                                    <Command.Item
                                        value="Add paper from arXiv URL"
                                        onSelect={() => {
                                            setOpen(false);
                                            triggerOpenAddPaper();
                                        }}
                                        className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-foreground-secondary cursor-pointer data-[selected=true]:bg-surface-inset data-[selected=true]:text-accent transition-colors"
                                    >
                                        <FileText className="h-4 w-4 text-foreground-muted" />
                                        Add paper from arXiv URL
                                    </Command.Item>
                                </Command.Group>
                            </Command.List>

                            {/* Footer */}
                            <div className="flex items-center justify-between px-4 py-2 border-t border-surface-inset/50 text-[10px] text-foreground-muted">
                                <span>↑↓ Navigate</span>
                                <span>↵ Select</span>
                                <span>⌘K Toggle</span>
                            </div>
                        </Command>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
