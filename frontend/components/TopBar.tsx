'use client'

import { Menu, Search, Plus } from 'lucide-react'
import { OPEN_ADD_PAPER_EVENT } from '../lib/navigation'

export interface TopBarProps {
  onHamburgerOpen: () => void
  onAddPaperOpen?: () => void
}

export default function TopBar({
  onHamburgerOpen,
  onAddPaperOpen,
}: TopBarProps) {
  function handleSearchClick() {
    window.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'k', metaKey: true, bubbles: true })
    )
  }

  function handleAddPaperClick() {
    if (onAddPaperOpen) {
      onAddPaperOpen()
      return
    }
    window.dispatchEvent(new CustomEvent(OPEN_ADD_PAPER_EVENT))
  }

  return (
    <header
      className="fixed top-0 left-16 right-0 h-[60px] bg-surface-card shadow-warm-sm z-30 flex items-center px-4 gap-3"
      aria-label="Top application bar"
    >
      {/* Left: hamburger + wordmark */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <button
          type="button"
          onClick={onHamburgerOpen}
          aria-label="Open navigation drawer"
          className="flex items-center justify-center h-8 w-8 rounded-md text-foreground-muted hover:bg-surface-inset hover:text-foreground-secondary transition-colors"
        >
          <Menu size={20} aria-hidden="true" />
        </button>

        {/* Wordmark: "Scholar's" light + "Atelier" black italic */}
        <span
          className="text-lg leading-none select-none"
          style={{ fontFamily: 'var(--font-display)' }}
          aria-label="Scholar's Atelier"
        >
          <span
            className="text-foreground font-light"
            style={{ fontFamily: 'var(--font-display)', fontWeight: 300 }}
          >
            Scholar&apos;s{' '}
          </span>
          <span
            className="text-foreground-secondary italic"
            style={{ fontFamily: 'var(--font-display)', fontWeight: 900 }}
          >
            Atelier
          </span>
        </span>
      </div>

      {/* Center spacer */}
      <div className="flex-1" />

      {/* Right: search + add paper */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          type="button"
          onClick={handleSearchClick}
          aria-label="Search — press ⌘K"
          className="flex items-center gap-2 h-8 px-3 rounded-md bg-surface-inset text-foreground-muted hover:bg-surface-card hover:text-foreground-secondary transition-colors text-sm"
        >
          <Search size={15} aria-hidden="true" />
          <span className="hidden sm:inline">Search</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 text-[10px] text-foreground-muted border border-foreground-muted/30 rounded px-1 py-0.5 font-sans">
            ⌘K
          </kbd>
        </button>

        <button
          type="button"
          onClick={handleAddPaperClick}
          aria-label="Add Paper"
          className="flex items-center gap-1.5 h-8 px-3 rounded-md bg-accent text-on-accent hover:bg-accent-hover transition-colors text-sm font-medium"
        >
          <Plus size={15} aria-hidden="true" />
          <span>+ Add Paper</span>
        </button>
      </div>
    </header>
  )
}
