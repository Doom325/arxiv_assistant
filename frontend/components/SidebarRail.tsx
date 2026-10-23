'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  LayoutList,
  BookOpen,
  MessageSquare,
  Layers,
  GitBranch,
  BarChart3,
  Settings,
  Keyboard,
  BookMarked,
  ScanSearch,
} from 'lucide-react'
import ThemeToggle from './ThemeToggle'
import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import {
  CORE_NAV_ROUTES,
  SETTINGS_NAV_ROUTE,
  isRouteActive,
} from '../lib/navigation'
import { toast } from 'sonner'

const CORE_ROUTE_ICONS: Record<string, typeof LayoutList> = {
  Dashboard: LayoutDashboard,
  Queue: LayoutList,
  Library: BookOpen,
  Chat: MessageSquare,
  Patterns: Layers,
  Timeline: GitBranch,
  Analysis: BarChart3,
}

export const navItems = CORE_NAV_ROUTES.map((route) => ({
  ...route,
  icon: CORE_ROUTE_ICONS[route.name] ?? LayoutList,
}))

export interface SidebarRailProps {
  onOpenShortcuts?: () => void
}

export default function SidebarRail({ onOpenShortcuts }: SidebarRailProps = {}) {
  const pathname = usePathname()
  const [unreadCount, setUnreadCount] = useState(0)
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
      .catch(() => {})
  }, [])

  const isSettingsActive = isRouteActive(pathname, SETTINGS_NAV_ROUTE.activeOn)

  return (
    <nav className="flex flex-col h-full w-16 bg-surface-card" aria-label="Primary">
      {/* Logo slot — aligns with 60px top bar height */}
      <div className="h-[60px] flex items-center justify-center flex-shrink-0">
        <Link
          href="/"
          title="Dashboard"
          aria-label="Scholar's Atelier Home"
          className="flex items-center justify-center h-10 w-10 rounded-md hover:bg-surface-inset transition-colors"
        >
          <BookMarked
            size={24}
            className="text-accent"
            aria-hidden="true"
          />
        </Link>
      </div>

      {/* Primary nav items */}
      <div className="flex flex-col gap-1 px-2 flex-1">
        {navItems.map((item) => {
          const isActive = isRouteActive(pathname, item.activeOn)
          const Icon = item.icon
          const showDot = Boolean(item.showBadge && unreadCount > 0)

          return (
            <Link
              key={item.name}
              href={item.href}
              title={item.name}
              aria-label={item.name}
              aria-current={isActive ? 'page' : undefined}
              className={[
                'relative flex items-center justify-center h-10 w-full rounded-md transition-colors',
                isActive
                  ? 'border-l-2 border-accent bg-surface-inset text-accent'
                  : 'text-foreground-muted hover:bg-surface-inset hover:text-foreground-secondary',
              ].join(' ')}
            >
              <Icon size={20} aria-hidden="true" />
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
          href={SETTINGS_NAV_ROUTE.href}
          title={SETTINGS_NAV_ROUTE.name}
          aria-label={SETTINGS_NAV_ROUTE.name}
          aria-current={isSettingsActive ? 'page' : undefined}
          className={[
            'flex items-center justify-center h-10 w-full rounded-md transition-colors',
            isSettingsActive
              ? 'border-l-2 border-accent bg-surface-inset text-accent'
              : 'text-foreground-muted hover:bg-surface-inset hover:text-foreground-secondary',
          ].join(' ')}
        >
          <Settings size={20} aria-hidden="true" />
        </Link>

        <div className="flex items-center justify-center h-10 w-full">
          <ThemeToggle />
        </div>

        <button
          type="button"
          title="Trigger AI Scan"
          aria-label="Trigger AI Scan"
          onClick={handleTriggerScan}
          disabled={scanning}
          className="flex items-center justify-center h-10 w-full rounded-md transition-colors text-foreground-muted hover:bg-surface-inset hover:text-accent disabled:opacity-50"
        >
          <ScanSearch size={20} aria-hidden="true" />
        </button>

        <button
          type="button"
          title="Keyboard shortcuts"
          aria-label="Keyboard shortcuts"
          onClick={() => onOpenShortcuts?.()}
          className="flex items-center justify-center h-10 w-full rounded-md transition-colors text-foreground-muted hover:bg-surface-inset hover:text-foreground-secondary"
        >
          <Keyboard size={20} aria-hidden="true" />
        </button>
      </div>
    </nav>
  )
}
