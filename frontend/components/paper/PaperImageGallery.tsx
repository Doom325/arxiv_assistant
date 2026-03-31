"use client"

import React, { useState, useCallback } from "react"
import { PaperImage } from "@/lib/api"

interface PaperImageGalleryProps {
    arxivId: string
    images: PaperImage[]
}

/**
 * Renders extracted PDF figures in a responsive grid.
 * Clicking an image opens it in a lightbox overlay.
 */
function PaperImageGalleryInner({ arxivId, images }: PaperImageGalleryProps) {
    const [lightboxIdx, setLightboxIdx] = useState<number | null>(null)

    const openLightbox = useCallback((idx: number) => setLightboxIdx(idx), [])
    const closeLightbox = useCallback(() => setLightboxIdx(null), [])

    const goNext = useCallback(() => {
        setLightboxIdx((prev) => (prev !== null && prev < images.length - 1 ? prev + 1 : prev))
    }, [images.length])

    const goPrev = useCallback(() => {
        setLightboxIdx((prev) => (prev !== null && prev > 0 ? prev - 1 : prev))
    }, [])

    if (!images || images.length === 0) return null

    return (
        <>
            {/* Gallery section */}
            <div className="mt-12 mb-8">
                <div className="mb-6">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted">
                        Extracted Figures
                    </p>
                    <div className="h-px bg-surface-inset mt-2 mb-4" />
                    <h2
                        className="text-xl font-bold text-foreground"
                        style={{ fontFamily: "var(--font-display)" }}
                    >
                        Figures &amp; Charts
                    </h2>
                    <p className="text-foreground-muted text-xs mt-1">
                        {images.length} figure{images.length !== 1 ? "s" : ""} extracted from the PDF
                    </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {images.map((img, idx) => (
                        <button
                            key={img.filename}
                            onClick={() => openLightbox(idx)}
                            className="bg-surface-card rounded-xl shadow-warm-sm overflow-hidden
                                       hover:shadow-warm transition-shadow text-left group cursor-pointer"
                        >
                            <div className="relative bg-white flex items-center justify-center p-3 min-h-[120px]">
                                <img
                                    src={`/api/papers/${arxivId}/images/${img.filename}`}
                                    alt={`Figure from page ${img.page}`}
                                    className="max-w-full max-h-[300px] object-contain"
                                    loading="lazy"
                                />
                                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors rounded-t-xl" />
                            </div>
                            <div className="px-4 py-2.5 flex items-center justify-between">
                                <span className="text-foreground-muted text-xs italic">
                                    Figure from page {img.page}
                                </span>
                                <span className="text-foreground-muted/50 text-[10px]">
                                    {img.width} x {img.height}
                                </span>
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Lightbox overlay */}
            {lightboxIdx !== null && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
                    onClick={closeLightbox}
                >
                    {/* Close button */}
                    <button
                        onClick={closeLightbox}
                        className="absolute top-4 right-4 text-white/80 hover:text-white
                                   bg-white/10 hover:bg-white/20 rounded-full w-10 h-10
                                   flex items-center justify-center transition-colors"
                        aria-label="Close lightbox"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18 6L6 18M6 6l12 12" />
                        </svg>
                    </button>

                    {/* Navigation arrows */}
                    {lightboxIdx > 0 && (
                        <button
                            onClick={(e) => { e.stopPropagation(); goPrev() }}
                            className="absolute left-4 text-white/80 hover:text-white
                                       bg-white/10 hover:bg-white/20 rounded-full w-10 h-10
                                       flex items-center justify-center transition-colors"
                            aria-label="Previous image"
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M15 18l-6-6 6-6" />
                            </svg>
                        </button>
                    )}
                    {lightboxIdx < images.length - 1 && (
                        <button
                            onClick={(e) => { e.stopPropagation(); goNext() }}
                            className="absolute right-4 text-white/80 hover:text-white
                                       bg-white/10 hover:bg-white/20 rounded-full w-10 h-10
                                       flex items-center justify-center transition-colors"
                            aria-label="Next image"
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M9 18l6-6-6-6" />
                            </svg>
                        </button>
                    )}

                    {/* Image */}
                    <div
                        className="max-w-[90vw] max-h-[85vh] flex flex-col items-center"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <img
                            src={`/api/papers/${arxivId}/images/${images[lightboxIdx].filename}`}
                            alt={`Figure from page ${images[lightboxIdx].page}`}
                            className="max-w-full max-h-[80vh] object-contain rounded-lg shadow-2xl bg-white"
                        />
                        <p className="text-white/70 text-sm mt-3 italic">
                            Figure from page {images[lightboxIdx].page}
                            <span className="mx-2 text-white/30">|</span>
                            {lightboxIdx + 1} of {images.length}
                        </p>
                    </div>
                </div>
            )}
        </>
    )
}

const PaperImageGallery = React.memo(PaperImageGalleryInner)
export default PaperImageGallery
