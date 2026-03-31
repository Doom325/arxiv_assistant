"use client"

interface ReadingProgressBarProps {
    progress: number
}

export default function ReadingProgressBar({ progress }: ReadingProgressBarProps) {
    if (progress <= 0) return null

    return (
        <div className="fixed top-0 left-0 right-0 z-50 h-[3px]">
            <div
                className="h-full bg-accent transition-[width] duration-150"
                style={{ width: `${progress * 100}%` }}
            />
        </div>
    )
}
