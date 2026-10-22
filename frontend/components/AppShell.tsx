'use client'

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import SidebarRail from './SidebarRail'
import TopBar from './TopBar'
import HamburgerDrawer from './HamburgerDrawer'
import ShortcutOverlay from './ShortcutOverlay'
import AddPaperForm from './AddPaperForm'
import { useKeyboardNav } from '../lib/useKeyboardNav'
import { OPEN_ADD_PAPER_EVENT } from '../lib/navigation'

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [addPaperOpen, setAddPaperOpen] = useState(false)
  const { showShortcuts, setShowShortcuts } = useKeyboardNav({
    itemCount: 0,
    enableChords: true,
    enableOverlayShortcut: true,
  })

  useEffect(() => {
    const handleOpenAddPaper = () => setAddPaperOpen(true)
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setAddPaperOpen(false)
      }
    }
    window.addEventListener(OPEN_ADD_PAPER_EVENT, handleOpenAddPaper)
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener(OPEN_ADD_PAPER_EVENT, handleOpenAddPaper)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {/* Icon sidebar rail — fixed left, 64px wide, full viewport height */}
      <div className="fixed left-0 top-0 h-full w-16 bg-surface-card z-40">
        <SidebarRail onOpenShortcuts={() => setShowShortcuts(true)} />
      </div>

      {/* Top app bar — fixed top, offset left by rail width */}
      <TopBar
        onHamburgerOpen={() => setDrawerOpen(true)}
        onAddPaperOpen={() => setAddPaperOpen(true)}
      />

      {/* Hamburger drawer — slides in over rail */}
      <HamburgerDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />

      {/* Main scrollable content — offset left by rail, top by bar */}
      <main className="ml-16 pt-[60px] min-h-screen bg-background">
        {children}
      </main>

      {/* Global Keyboard Shortcuts Overlay */}
      <ShortcutOverlay
        open={showShortcuts}
        onClose={() => setShowShortcuts(false)}
      />

      {/* Global Add Paper Modal */}
      {addPaperOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/20 backdrop-blur-sm"
          onClick={() => setAddPaperOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="app-shell-add-paper-title"
            className="bg-surface-card rounded-2xl shadow-warm-lg p-8 w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h2
                id="app-shell-add-paper-title"
                style={{ fontFamily: 'var(--font-display)' }}
                className="font-bold text-xl text-foreground"
              >
                Add Paper
              </h2>
              <button
                type="button"
                aria-label="Close add paper dialog"
                onClick={() => setAddPaperOpen(false)}
                className="text-foreground-muted hover:text-foreground transition-colors"
              >
                <X size={20} aria-hidden="true" />
              </button>
            </div>
            <AddPaperForm onSuccess={() => setAddPaperOpen(false)} />
          </div>
        </div>
      )}
    </div>
  )
}
