'use client'

import { useState } from 'react'
import SidebarRail from './SidebarRail'
import TopBar from './TopBar'
import HamburgerDrawer from './HamburgerDrawer'

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      {/* Icon sidebar rail — fixed left, 64px wide, full viewport height */}
      <div className="fixed left-0 top-0 h-full w-16 bg-surface-card z-40">
        <SidebarRail />
      </div>

      {/* Top app bar — fixed top, offset left by rail width */}
      <TopBar onHamburgerOpen={() => setDrawerOpen(true)} />

      {/* Hamburger drawer — slides in over rail */}
      <HamburgerDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />

      {/* Main scrollable content — offset left by rail, top by bar */}
      <main className="ml-16 pt-[60px] min-h-screen bg-background">
        {children}
      </main>
    </div>
  )
}
