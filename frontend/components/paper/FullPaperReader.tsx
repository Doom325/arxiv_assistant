"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import { getFullText, PaperFullText, PaperImage } from "@/lib/api"
import ReadingProgressBar from "./ReadingProgressBar"
import SectionRenderer from "./SectionRenderer"
import PaperImageGallery from "./PaperImageGallery"

/** Extract a pull quote — the first sentence between 40-120 chars */
function extractPullQuote(content: string): string | null {
    const sentences = content.split(/[.!?]/).filter(s => s.trim().length > 40 && s.trim().length < 120)
    return sentences[0]?.trim() || null
}

/** Maps section title to a themed drop cap color */
function getDropCapColor(title: string): string {
    const lower = title.toLowerCase()
    if (lower.includes('abstract') || lower.includes('introduction')) return 'text-accent'
    if (lower.includes('method') || lower.includes('approach') || lower.includes('proposed')) return 'text-[#2A4A1A]'
    if (lower.includes('result') || lower.includes('experiment') || lower.includes('evaluation')) return 'text-[#8B6914]'
    if (lower.includes('conclusion') || lower.includes('discussion') || lower.includes('future')) return 'text-[#7A4B8A]'
    return 'text-accent'
}

interface FullPaperReaderProps {
    paperId: string
    pdfUrl: string
}

export default function FullPaperReader({ paperId, pdfUrl }: FullPaperReaderProps) {
    const [data, setData] = useState<PaperFullText | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)
    const [scrollProgress, setScrollProgress] = useState(0)

    useEffect(() => {
        let cancelled = false
        setLoading(true)
        setError(false)

        getFullText(paperId)
            .then((result) => {
                if (!cancelled) setData(result)
            })
            .catch(() => {
                if (!cancelled) setError(true)
            })
            .finally(() => {
                if (!cancelled) setLoading(false)
            })

        return () => {
            cancelled = true
        }
    }, [paperId])

    // Scroll progress tracking
    const handleScroll = useCallback(() => {
        const scrollY = window.scrollY
        const docHeight = document.documentElement.scrollHeight - window.innerHeight
        if (docHeight > 0) {
            setScrollProgress(Math.min(scrollY / docHeight, 1))
        }
    }, [])

    useEffect(() => {
        window.addEventListener("scroll", handleScroll, { passive: true })
        return () => window.removeEventListener("scroll", handleScroll)
    }, [handleScroll])

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-16">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent mb-4"></div>
                <p
                    className="text-foreground-muted italic"
                    style={{ fontFamily: "var(--font-display)" }}
                >
                    Extracting paper text...
                </p>
                <p className="text-foreground-muted/60 text-xs mt-2">
                    This may take a moment for first-time extraction
                </p>
            </div>
        )
    }

    if (error || !data) {
        return (
            <div className="text-center py-16">
                <p className="text-foreground-secondary mb-4">
                    Could not extract paper text.
                </p>
                <a
                    href={pdfUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent hover:text-accent-hover font-medium"
                >
                    Open PDF on arXiv &rarr;
                </a>
            </div>
        )
    }

    // Distribute images across sections based on page numbers.
    // Each image is placed after the section that most likely corresponds to
    // its page. We estimate by dividing pages evenly among sections.
    const sectionImages = useMemo(() => {
        const images = data?.images ?? []
        if (images.length === 0 || !data) return new Map<number, PaperImage[]>()

        const totalSections = data.sections.length
        const maxPage = Math.max(...images.map((img) => img.page), 1)
        const pagesPerSection = maxPage / totalSections

        const map = new Map<number, PaperImage[]>()
        for (const img of images) {
            // Which section index does this page fall into?
            const sectionIdx = Math.min(
                Math.floor((img.page - 1) / pagesPerSection),
                totalSections - 1
            )
            const existing = map.get(sectionIdx) ?? []
            existing.push(img)
            map.set(sectionIdx, existing)
        }
        return map
    }, [data])

    return (
        <div>
            <ReadingProgressBar progress={scrollProgress} />

            {/* Reading metadata */}
            <div className="flex items-center gap-4 mb-8 text-foreground-muted text-xs uppercase tracking-wider">
                <span>{data.word_count.toLocaleString()} words</span>
                <span>&middot;</span>
                <span>{data.estimated_reading_minutes} min read</span>
                <span>&middot;</span>
                <span>{data.sections.length} sections</span>
                {data.images.length > 0 && (
                    <>
                        <span>&middot;</span>
                        <span>{data.images.length} figure{data.images.length !== 1 ? "s" : ""}</span>
                    </>
                )}
            </div>

            {/* Sections with inline images and pull quotes */}
            <div className="space-y-12">
                {data.sections.map((section, i) => {
                    const imgs = sectionImages.get(i)

                    // Track level-1 sections for pull quote insertion
                    const level1Index = data.sections.slice(0, i + 1).filter(s => s.level === 1).length
                    const shouldInsertPullQuote = section.level === 1 && level1Index > 0 && level1Index % 3 === 0
                    const pullQuote = shouldInsertPullQuote ? extractPullQuote(section.content) : null

                    return (
                        <div key={section.order} id={`section-${section.order}`}>
                            <SectionRenderer
                                section={section}
                                isFirst={i === 0}
                                dropCapColor={section.level === 1 ? getDropCapColor(section.title) : undefined}
                            />
                            {imgs && imgs.length > 0 && (
                                <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {imgs.map((img) => (
                                        <div
                                            key={img.filename}
                                            className="bg-surface-card rounded-xl shadow-warm-sm overflow-hidden"
                                        >
                                            <div className="bg-white flex items-center justify-center p-3">
                                                <img
                                                    src={`/api/papers/${data.arxiv_id}/images/${img.filename}`}
                                                    alt={`Figure from page ${img.page}`}
                                                    className="max-w-full max-h-[260px] object-contain"
                                                    loading="lazy"
                                                />
                                            </div>
                                            <div className="px-3 py-2">
                                                <span className="text-foreground-muted text-xs italic">
                                                    Figure from page {img.page}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {/* Pull quote after every 3rd level-1 section */}
                            {pullQuote && (
                                <blockquote className="my-12 px-8 py-6 border-l-4 border-accent/30">
                                    <p
                                        style={{ fontFamily: 'var(--font-display)' }}
                                        className="text-2xl font-light italic text-foreground/70 leading-relaxed"
                                    >
                                        &ldquo;{pullQuote}&rdquo;
                                    </p>
                                </blockquote>
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Full image gallery at the end */}
            {data.images.length > 0 && (
                <PaperImageGallery arxivId={data.arxiv_id} images={data.images} />
            )}
        </div>
    )
}
