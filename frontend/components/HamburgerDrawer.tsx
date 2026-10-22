'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutList,
  Archive,
  BookOpen,
  MessageSquare,
  Layers,
  GitBranch,
  BarChart3,
  Settings,
} from 'lucide-react'
import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { isRouteActive } from '../lib/navigation'
import AddPaperForm from './AddPaperForm'

function LibraryRing({
  total,
  bookmarked,
}: {
  total: number
  bookmarked: number
}) {
  const pct = total > 0 ? bookmarked / total : 0
  const circumference = 2 * Math.PI * 18
  const offset = circumference * (1 - pct)

  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <svg width="44" height="44" viewBox="0 0 44 44" aria-hidden="true">
        <circle
          cx="22"
          cy="22"
          r="18"
          fill="none"
          stroke="var(--color-surface-inset)"
          strokeWidth="3"
        />
        <circle
          cx="22"
          cy="22"
          r="18"
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 22 22)"
          className="transition-all duration-700"
        />
        <text
          x="22"
          y="22"
          textAnchor="middle"
          dominantBaseline="central"
          fill="var(--color-foreground-secondary)"
          fontSize="10"
          fontWeight="600"
        >
          {Math.round(pct * 100)}%
        </text>
      </svg>
      <div>
        <p className="text-xs text-foreground-secondary font-medium">
          {bookmarked} saved
        </p>
        <p className="text-[10px] text-foreground-muted">of {total} papers</p>
      </div>
    </div>
  )
}

export const navigation = [
  {
    name: 'Queue',
    href: '/queue',
    activeOn: ['/', '/queue'],
    showBadge: true,
    icon: LayoutList,
  },
  {
    name: 'Archive',
    href: '/dashboard',
    activeOn: ['/dashboard', '/research'],
    icon: Archive,
  },
  {
    name: 'Library',
    href: '/bookmarks',
    activeOn: ['/bookmarks'],
    icon: BookOpen,
  },
  {
    name: 'Chat',
    href: '/chat',
    activeOn: ['/chat'],
    icon: MessageSquare,
  },
  {
    name: 'Patterns',
    href: '/patterns',
    activeOn: ['/patterns'],
    icon: Layers,
  },
  {
    name: 'Timeline',
    href: '/timeline',
    activeOn: ['/timeline'],
    icon: GitBranch,
  },
  {
    name: 'Analysis',
    href: '/analysis',
    activeOn: ['/analysis'],
    icon: BarChart3,
  },
  {
    name: 'Settings',
    href: '/settings',
    activeOn: ['/settings'],
    icon: Settings,
  },
]

export interface HamburgerDrawerProps {
  isOpen: boolean
  onClose: () => void
}

export default function HamburgerDrawer({
  isOpen,
  onClose,
}: HamburgerDrawerProps) {
  const pathname = usePathname()
  const [stats, setStats] = useState<{
    total_papers: number
    library_count: number
  } | null>(null)
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    api
      .getAnalyticsSummaryStats()
      .then((s) => setStats(s))
      .catch(() => {})
    api
      .getQueueStats()
      .then((qs) => setUnreadCount(qs.total_unread))
      .catch(() => {})
  }, [])

  return (
    <>
      {/* Backdrop — covers content area but not the rail (left-16) */}
      {isOpen && (
        <div
          className="fixed inset-0 left-16 bg-foreground/10 backdrop-blur-[2px] z-40"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Drawer panel — slides in from the left, over the rail */}
      <div
        className={[
          'fixed top-0 left-0 z-50 h-screen w-[280px] flex flex-col',
          'bg-surface-card shadow-warm-lg',
          'transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        ].join(' ')}
        aria-modal="true"
        role="dialog"
        aria-label="Navigation drawer"
      >
        {/* Drawer header — aligns with 60px top bar */}
        <div className="h-[60px] flex items-center px-5 flex-shrink-0">
          <BookOpen className="h-5 w-5 text-accent mr-2.5" aria-hidden="true" />
          <span
            className="text-base leading-none select-none"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            <span
              className="text-foreground font-light"
              style={{ fontWeight: 300 }}
            >
              Scholar&apos;s{' '}
            </span>
            <span
              className="text-foreground-secondary italic"
              style={{ fontWeight: 900 }}
            >
              Atelier
            </span>
          </span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5" aria-label="Drawer">
          {navigation.map((item) => {
            const isActive = isRouteActive(pathname, item.activeOn)
            const Icon = item.icon
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                aria-current={isActive ? 'page' : undefined}
                className={[
                  'group flex items-center px-3 py-2.5 rounded-md text-sm transition-colors',
                  isActive
                    ? 'border-l-2 border-accent text-accent pl-[10px] bg-surface-inset'
                    : 'text-foreground-secondary hover:bg-surface-inset hover:text-foreground',
                ].join(' ')}
              >
                <Icon
                  aria-hidden="true"
                  className={[
                    'mr-3 h-4 w-4 flex-shrink-0 transition-colors',
                    isActive
                      ? 'text-accent'
                      : 'text-foreground-muted group-hover:text-foreground-secondary',
                  ].join(' ')}
                />
                {item.name}
                {item.showBadge && unreadCount > 0 && (
                  <span className="ml-auto inline-flex items-center justify-center rounded-full bg-accent text-on-accent px-2 py-0.5 text-[10px] font-semibold min-w-[20px]">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </Link>
            )
          })}

          {/* LibraryRing widget */}
          {stats && (
            <div className="mt-4 mx-1 rounded-xl bg-surface-inset border border-foreground-muted/10">
              <LibraryRing
                total={stats.total_papers}
                bookmarked={stats.library_count}
              />
            </div>
          )}

          {/* AddPaperForm widget */}
          <div className="mt-4 px-3">
            <p className="text-xs font-semibold text-foreground-muted uppercase tracking-[0.08em] mb-3">
              On-Demand Addition
            </p>
            <AddPaperForm onSuccess={onClose} />
          </div>
        </nav>
      </div>
    </>
  )
}
