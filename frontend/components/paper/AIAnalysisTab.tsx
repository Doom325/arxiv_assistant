"use client"

import { Paper, PaperPattern } from "@/lib/api"
import PaperAbstract from "./PaperAbstract"
import AISynthesisSection from "./AISynthesisSection"
import ReferencesSection from "./ReferencesSection"
import PatternsSection from "./PatternsSection"

interface AIAnalysisTabProps {
    paper: Paper
    paperPatterns: PaperPattern | null
    summarizing: boolean
    onGenerate: (
        model?: string,
        temperature?: number,
        provider?: string,
        endpoint?: string
    ) => void
}

export default function AIAnalysisTab({
    paper,
    paperPatterns,
    summarizing,
    onGenerate,
}: AIAnalysisTabProps) {
    return (
        <div className="space-y-16">
            <section id="abstract">
                <PaperAbstract abstract={paper.summary || ""} />
            </section>
            <section id="ai-synthesis">
                <AISynthesisSection
                    summary={paper.generated_summary}
                    isSummarizing={summarizing}
                    onGenerate={onGenerate}
                    hasExistingSummary={!!paper.generated_summary}
                />
            </section>
            <section id="references">
                <ReferencesSection citations={paper.citations || []} />
            </section>
            <section id="patterns">
                <PatternsSection patterns={paperPatterns} />
            </section>
        </div>
    )
}
