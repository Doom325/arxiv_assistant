"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Compass, Home, Search, Settings, MessageSquare, BookOpen, Menu, X, Bookmark, BarChart3, Plus, Loader2, Layers, GitBranch } from "lucide-react";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { addPaper, api } from "../lib/api";
import { useRouter } from "next/navigation";

function AddPaperForm() {
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        try {
            const paper = await addPaper(query);
            setQuery("");
            toast.success(`Added "${paper.title || paper.arxiv_id}"`);
            router.push(`/paper/${paper.arxiv_id}`);
        } catch (err: any) {
            toast.error(err.message || "Failed to add paper");
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-2">
            <div className="relative group">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="ArXiv ID or URL..."
                    disabled={loading}
                    className="w-full bg-surface-inset border border-border-default rounded-lg py-2 px-3 text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-accent transition-all disabled:opacity-50"
                />
                <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className="absolute right-1 top-1 p-1.5 bg-surface-card rounded-md text-foreground-secondary hover:text-white hover:bg-accent transition-all disabled:opacity-30"
                >
                    {loading ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
                </button>
            </div>
        </form>
    );
}

const navigation = [
    { name: "Discover", href: "/", icon: Compass },
    { name: "Dashboard", href: "/dashboard", icon: Home },
    { name: "Research", href: "/research", icon: Search },
    { name: "Bookmarks", href: "/bookmarks", icon: Bookmark },
    { name: "Analysis", href: "/analysis", icon: BarChart3 },
    { name: "Timeline", href: "/timeline", icon: GitBranch },
    { name: "Patterns", href: "/patterns", icon: Layers },
    { name: "Deep Dive", href: "/chat", icon: MessageSquare },
    { name: "Settings", href: "/settings", icon: Settings },
];

function LibraryRing({ total, bookmarked }: { total: number; bookmarked: number }) {
    const pct = total > 0 ? bookmarked / total : 0;
    const circumference = 2 * Math.PI * 18;
    const offset = circumference * (1 - pct);

    return (
        <div className="flex items-center gap-3 px-4 py-3">
            <svg width="44" height="44" viewBox="0 0 44 44">
                <circle cx="22" cy="22" r="18" fill="none" stroke="#27272a" strokeWidth="3" />
                <circle
                    cx="22" cy="22" r="18" fill="none"
                    stroke="#6366f1" strokeWidth="3" strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    transform="rotate(-90 22 22)"
                    className="transition-all duration-700"
                />
                <text x="22" y="22" textAnchor="middle" dominantBaseline="central" fill="#a1a1aa" fontSize="10" fontWeight="600">
                    {Math.round(pct * 100)}%
                </text>
            </svg>
            <div>
                <p className="text-xs text-foreground-secondary font-medium">{bookmarked} saved</p>
                <p className="text-[10px] text-foreground-muted">of {total} papers</p>
            </div>
        </div>
    );
}

export default function Sidebar() {
    const pathname = usePathname();
    const [isOpen, setIsOpen] = useState(false);
    const [stats, setStats] = useState<{ total_papers: number; library_count: number } | null>(null);
    const [unreadCount, setUnreadCount] = useState(0);

    useEffect(() => {
        api.getAnalyticsSummaryStats()
            .then((s) => setStats(s))
            .catch(() => {}); // silently fail
        api.getQueueStats()
            .then((qs) => setUnreadCount(qs.total_unread))
            .catch(() => {}); // silently fail
    }, []);

    return (
        <>
            {/* Hamburger Toggle Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="fixed top-4 left-4 z-50 p-2 bg-surface-card/80 backdrop-blur-sm border border-border-default rounded-lg text-foreground hover:bg-surface-inset transition-colors"
            >
                {isOpen ? <X size={20} /> : <Menu size={20} />}
            </button>

            {/* Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40"
                    onClick={() => setIsOpen(false)}
                />
            )}

            {/* Sidebar */}
            <div className={`
                fixed top-0 left-0 z-40 h-screen w-64 flex-col bg-surface-card/70 glass-sidebar text-foreground border-r border-border-default
                transition-transform duration-300 ease-in-out
                ${isOpen ? "translate-x-0" : "-translate-x-full"}
            `}>
                <div className="flex h-16 items-center px-6 border-b border-border-default">
                    <BookOpen className="h-6 w-6 text-accent mr-2" />
                    <span className="text-xl font-bold tracking-tight">arXiv AI</span>
                </div>
                <nav className="flex-1 space-y-1 px-2 py-4">
                    {navigation.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                onClick={() => setIsOpen(false)} // Close on navigate (mobile)
                                className={`group flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors ${isActive
                                    ? "bg-surface-inset text-foreground"
                                    : "text-foreground-secondary hover:bg-surface-inset hover:text-foreground"
                                    }`}
                            >
                                <item.icon
                                    className={`mr-3 h-5 w-5 flex-shrink-0 ${isActive ? "text-accent" : "text-foreground-muted group-hover:text-foreground"
                                        }`}
                                />
                                {item.name}
                                {item.name === "Discover" && unreadCount > 0 && (
                                    <span className="ml-auto inline-flex items-center justify-center rounded-full bg-accent px-2 py-0.5 text-[10px] font-semibold text-white min-w-[20px]">
                                        {unreadCount > 99 ? "99+" : unreadCount}
                                    </span>
                                )}
                            </Link>
                        );
                    })}

                    {stats && (
                        <div className="mt-6 mx-2 rounded-xl bg-surface-inset border border-border-default">
                            <LibraryRing total={stats.total_papers} bookmarked={stats.library_count} />
                        </div>
                    )}

                    <div className="mt-6 px-4">
                        <p className="text-xs font-semibold text-foreground-muted uppercase tracking-wider mb-4">On-Demand Addition</p>
                        <AddPaperForm />
                    </div>
                </nav>
                <div className="p-4 border-t border-border-default">
                    <div className="flex items-center">
                        <div className="h-8 w-8 rounded-full bg-accent flex items-center justify-center text-sm font-medium">
                            U
                        </div>
                        <div className="ml-3">
                            <p className="text-sm font-medium text-foreground">User</p>
                            <p className="text-xs text-foreground-muted">Pro Plan</p>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
