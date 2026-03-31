'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { BookOpen, LayoutList, FolderOpen, Archive, Settings, Keyboard, BookMarked, ScanSearch } from 'lucide-react'
import ThemeToggle from './ThemeToggle'
import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import ShortcutOverlay from './ShortcutOverlay'
import { toast } from 'sonner'

const navItems = [
  {
    name: 'Library',
    href: '/bookmarks',
    icon: BookOpen,
    activeOn: ['/bookmarks'],
  },
  {
    name: 'Queue',
    href: '/queue',
    icon: LayoutList,
    activeOn: ['/queue', '/'],
    showBadge: true,
  },
  {
    name: 'Collections',
    href: '/bookmarks',
    icon: FolderOpen,
    activeOn: [] as string[], // placeholder — no unique route yet
  },
  {
    name: 'Archive',
    href: '/research',
    icon: Archive,
    activeOn: ['/research'],
  },
]

export default function SidebarRail() {
  const pathname = usePathname()
  const [unreadCount, setUnreadCount] = useState(0)
  const [shortcutsOpen, setShortcutsOpen] = useState(false)
  const [scanning, setScanning] = useState(false)

  const handleTriggerScan = async () => {
    if (scanning) return
    setScanning(true)
    try {
      const result = await api.discoverQueue(7)
      toast.success(`Found ${result.added} new papers`)
    } catch {
      toast.error('Scan failed')
    } finally {
      setScanning(false)
    }
  }

  useEffect(() => {
    api
      .getQueueStats()
      .then((qs) => setUnreadCount(qs.total_unread))
      .catch(() => {}) // silently fail
  }, [])

  return (
    <>
      <nav className="flex flex-col h-full w-16 bg-surface-card">
        {/* Logo slot — aligns with 60px top bar height */}
        <div className="h-[60px] flex items-center justify-center flex-shrink-0">
          <BookMarked
            size={24}
            className="text-accent"
            aria-label="Scholar's Atelier"
          />
        </div>

        {/* Primary nav items */}
        <div className="flex flex-col gap-1 px-2 flex-1">
          {navItems.map((item) => {
            const isActive = item.activeOn.includes(pathname)
            const Icon = item.icon
            const showDot =
              item.showBadge && unreadCount > 0

            return (
              <Link
                key={item.name}
                href={item.href}
                title={item.name}
                className={[
                  'relative flex items-center justify-center h-10 w-full rounded-md transition-colors',
                  isActive
                    ? 'border-l-2 border-accent bg-surface-inset text-accent'
                    : 'text-foreground-muted hover:bg-surface-inset hover:text-foreground-secondary',
                ].join(' ')}
              >
                <Icon size={20} />
                {showDot && (
                  <span
                    className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-accent"
                    aria-label={`${unreadCount} unread`}
                  />
                )}
              </Link>
            )
          })}
        </div>

        {/* Footer slot */}
        <div className="flex flex-col gap-1 px-2 pb-4">
          <Link
            href="/settings"
            title="Settings"
            className={[
              'flex items-center justify-center h-10 w-full rounded-md transition-colors',
              pathname === '/settings'
                ? 'border-l-2 border-accent bg-surface-inset text-accent'
                : 'text-foreground-muted hover:bg-surface-inset hover:text-foreground-secondary',
            ].join(' ')}
          >
            <Settings size={20} />
          </Link>

          <div className="flex items-center justify-center h-10 w-full">
            <ThemeToggle />
          </div>

          <button
            title="Trigger AI Scan"
            onClick={handleTriggerScan}
            disabled={scanning}
            className="flex items-center justify-center h-10 w-full rounded-md transition-colors text-foreground-muted hover:bg-surface-inset hover:text-accent disabled:opacity-50"
          >
            <ScanSearch size={20} />
          </button>

          <button
            title="Keyboard shortcuts"
            onClick={() => setShortcutsOpen(true)}
            className="flex items-center justify-center h-10 w-full rounded-md transition-colors text-foreground-muted hover:bg-surface-inset hover:text-foreground-secondary"
          >
            <Keyboard size={20} />
          </button>
        </div>
      </nav>

      <ShortcutOverlay open={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />
    </>
  )
}
