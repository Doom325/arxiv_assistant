"use client"

import { BookOpen, Sparkles } from "lucide-react"

interface PaperTabBarProps {
    activeTab: "full-paper" | "ai-analysis"
    onTabChange: (tab: "full-paper" | "ai-analysis") => void
}

export default function PaperTabBar({ activeTab, onTabChange }: PaperTabBarProps) {
    return (
        <div className="flex items-center gap-1 bg-surface-inset rounded-full p-1 w-fit mb-10">
            <button
                onClick={() => onTabChange("full-paper")}
                className={`inline-flex items-center gap-2 rounded-full px-6 py-2 text-sm transition-all ${
                    activeTab === "full-paper"
                        ? "bg-surface-card text-foreground font-medium shadow-warm-sm"
                        : "text-foreground-muted hover:text-foreground-secondary"
                }`}
            >
                <BookOpen className="h-4 w-4" />
                Full Paper
            </button>
            <button
                onClick={() => onTabChange("ai-analysis")}
                className={`inline-flex items-center gap-2 rounded-full px-6 py-2 text-sm transition-all ${
                    activeTab === "ai-analysis"
                        ? "bg-surface-card text-foreground font-medium shadow-warm-sm"
                        : "text-foreground-muted hover:text-foreground-secondary"
                }`}
            >
                <Sparkles className="h-4 w-4" />
                AI Analysis
            </button>
        </div>
    )
}
