"use client"

import React from "react"
import { PaperSection } from "@/lib/api"

interface SectionRendererProps {
    section: PaperSection
    isFirst: boolean
    /** Optional: section title used to pick a themed drop cap color */
    dropCapColor?: string
}

/** Maps a section title to a themed drop cap color class */
function getDropCapColor(title: string): string {
    const lower = title.toLowerCase()
    if (lower.includes('abstract') || lower.includes('introduction')) return 'text-accent'
    if (lower.includes('method') || lower.includes('approach') || lower.includes('proposed')) return 'text-[#2A4A1A]'
    if (lower.includes('result') || lower.includes('experiment') || lower.includes('evaluation')) return 'text-[#8B6914]'
    if (lower.includes('conclusion') || lower.includes('discussion') || lower.includes('future')) return 'text-[#7A4B8A]'
    return 'text-accent'
}

function SectionRendererInner({ section, isFirst, dropCapColor }: SectionRendererProps) {
    const paragraphs = section.content.split("\n\n").filter((p) => p.trim().length > 0)

    // Apply drop cap to the first paragraph of every level-1 section
    const shouldDropCap = section.level === 1 || isFirst
    const capColor = dropCapColor || getDropCapColor(section.title)

    return (
        <div id={`section-${section.order}`}>
            {/* Section header */}
            {section.level === 1 ? (
                <div className="mb-6">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted">
                        Section {section.order}
                    </p>
                    <div className="h-px bg-surface-inset mt-2 mb-4" />
                    <h2
                        className="text-xl font-bold text-foreground"
                        style={{ fontFamily: "var(--font-display)" }}
                    >
                        {section.title}
                    </h2>
                </div>
            ) : (
                <h3 className="text-base font-semibold text-foreground mb-4">
                    {section.title}
                </h3>
            )}

            {/* Content paragraphs */}
            <div>
                {paragraphs.map((paragraph, i) => {
                    if (shouldDropCap && i === 0 && paragraph.length > 0) {
                        const firstChar = paragraph.trimStart().charAt(0)
                        const rest = paragraph.trimStart().slice(1)
                        return (
                            <p
                                key={i}
                                className="text-foreground-secondary text-[15px] leading-[1.9] mb-4"
                            >
                                <span
                                    style={{ fontFamily: "var(--font-display)" }}
                                    className={`text-5xl font-bold ${capColor} float-left mr-3 mt-1 leading-none select-none`}
                                >
                                    {firstChar}
                                </span>
                                {rest}
                            </p>
                        )
                    }
                    return (
                        <p
                            key={i}
                            className="text-foreground-secondary text-[15px] leading-[1.9] mb-4"
                        >
                            {paragraph}
                        </p>
                    )
                })}
            </div>
        </div>
    )
}

const SectionRenderer = React.memo(SectionRendererInner)
export default SectionRenderer
