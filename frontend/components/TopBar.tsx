'use client'

import { usePathname } from 'next/navigation'
import { Menu, Bell, UserCircle, Search } from 'lucide-react'
import ThemeToggle from './ThemeToggle'

const STATUS_TABS = ['Unread', 'Reading', 'Read', 'Skipped'] as const
type StatusTab = (typeof STATUS_TABS)[number]

const QUEUE_ROUTES = ['/', '/queue']

interface TopBarProps {
  onHamburgerOpen: () => void
  statusFilter?: string
  onStatusChange?: (status: string) => void
}

export default function TopBar({
  onHamburgerOpen,
  statusFilter = 'Unread',
  onStatusChange,
}: TopBarProps) {
  const pathname = usePathname()
  const showStatusTabs = QUEUE_ROUTES.includes(pathname)

  function handleSearchClick() {
    // CommandPalette is purely keyboard-driven (no programmatic open API).
    // Dispatch a synthetic Cmd+K to trigger its existing keydown listener.
    window.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'k', metaKey: true, bubbles: true })
    )
  }

  return (
    <header
      className="fixed top-0 left-16 right-0 h-[60px] bg-surface-card shadow-warm-sm z-30 flex items-center px-4 gap-3"
      aria-label="Top application bar"
    >
      {/* Left: hamburger + wordmark */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <button
          onClick={onHamburgerOpen}
          aria-label="Open navigation drawer"
          className="flex items-center justify-center h-8 w-8 rounded-md text-foreground-muted hover:bg-surface-inset hover:text-foreground-secondary transition-colors"
        >
          <Menu size={20} />
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

      {/* Center: status tabs (queue routes only) */}
      {showStatusTabs && (
        <nav
          className="flex-1 flex items-center justify-center"
          aria-label="Reading status filter"
        >
          <div className="flex items-center gap-0.5 bg-surface-inset rounded-full px-1 py-1">
            {STATUS_TABS.map((tab) => {
              const isActive = statusFilter === tab
              return (
                <button
                  key={tab}
                  onClick={() => onStatusChange?.(tab)}
                  className={[
                    'px-3 py-1 rounded-full text-sm transition-colors',
                    isActive
                      ? 'bg-accent text-on-accent font-medium'
                      : 'text-foreground-secondary hover:text-foreground hover:bg-surface-card',
                  ].join(' ')}
                  aria-pressed={isActive}
                >
                  {tab}
                </button>
              )
            })}
          </div>
        </nav>
      )}

      {/* Spacer when tabs are not shown */}
      {!showStatusTabs && <div className="flex-1" />}

      {/* Right: search + notifications + avatar */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Search input — click triggers CommandPalette */}
        <button
          onClick={handleSearchClick}
          aria-label="Search — press ⌘K"
          className="flex items-center gap-2 h-8 px-3 rounded-md bg-surface-inset text-foreground-muted hover:bg-surface-card hover:text-foreground-secondary transition-colors text-sm"
        >
          <Search size={15} />
          <span className="hidden sm:inline">Search</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 text-[10px] text-foreground-muted border border-foreground-muted/30 rounded px-1 py-0.5 font-sans">
            ⌘K
          </kbd>
        </button>

        {/* Theme toggle */}
        <ThemeToggle />

        {/* Notification bell — placeholder */}
        <button
          aria-label="Notifications"
          className="flex items-center justify-center h-8 w-8 rounded-md text-foreground-muted hover:bg-surface-inset hover:text-foreground-secondary transition-colors"
        >
          <Bell size={18} />
        </button>

        {/* User avatar — placeholder */}
        <button
          aria-label="User account"
          className="flex items-center justify-center h-8 w-8 rounded-md text-foreground-muted hover:bg-surface-inset hover:text-foreground-secondary transition-colors"
        >
          <UserCircle size={20} />
        </button>
      </div>
    </header>
  )
}
