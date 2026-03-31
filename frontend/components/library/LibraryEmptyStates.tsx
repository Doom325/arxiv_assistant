"use client";

import { Bookmark } from "lucide-react";

export function LibraryEmptyState({ onBrowse }: { onBrowse: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <h2 style={{ fontFamily: 'var(--font-display)' }} className="font-extralight text-3xl text-foreground mb-2">Your library</h2>
      <h2 style={{ fontFamily: 'var(--font-display)' }} className="font-black italic text-4xl text-foreground mb-6">awaits.</h2>
      <p className="text-foreground-secondary text-sm mb-8 max-w-sm italic" style={{ fontFamily: 'var(--font-display)' }}>
        Save papers from the dashboard or queue to build your personal collection.
      </p>
      <button onClick={onBrowse} className="flex items-center gap-2 px-6 py-3 bg-accent text-on-accent rounded-2xl font-medium shadow-warm-sm hover:bg-accent-hover transition-colors">
        <Bookmark size={16} />
        Browse Papers
      </button>
    </div>
  )
}

export function LibraryEmptyList({ listName }: { listName: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <h3 style={{ fontFamily: 'var(--font-display)' }} className="font-bold text-xl text-foreground mb-3">No papers in &ldquo;{listName}&rdquo;</h3>
      <p className="text-foreground-secondary text-sm">Add papers from the dashboard or paper detail page.</p>
    </div>
  )
}
