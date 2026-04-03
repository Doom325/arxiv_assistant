'use client'

import { useState, useRef, useEffect } from 'react'
import { Search, LayoutGrid, List, ChevronDown, Check } from 'lucide-react'
import DatePicker from '../DatePicker'

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const SORT_OPTIONS = [
  { id: 'relevance', label: 'Most Relevant' },
  { id: 'newest', label: 'Newest First' },
  { id: 'title', label: 'Title A-Z' },
] as const

const ARXIV_CATEGORIES = [
  'cs.AI',
  'cs.LG',
  'cs.CL',
  'cs.CV',
  'cs.RO',
  'cs.NE',
  'cs.MA',
  'cs.IR',
  'cs.SI',
  'cs.HC',
  'cs.CY',
] as const

/* ------------------------------------------------------------------ */
/*  Props                                                              */
/* ------------------------------------------------------------------ */

interface DashboardFilterBarProps {
  categories: string[]
  selectedCategories: string[]
  onCategoryChange: (categories: string[]) => void
  dateStart: string | null
  dateEnd: string | null
  onDateChange: (start: string | null, end: string | null) => void
  sortBy: string
  onSortChange: (sort: string) => void
  viewMode: 'grid' | 'list'
  onViewModeChange: (mode: 'grid' | 'list') => void
  onReset: () => void
  searchQuery: string
  onSearchChange: (query: string) => void
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function useClickOutside(
  ref: React.RefObject<HTMLElement | null>,
  handler: () => void,
  active: boolean,
) {
  useEffect(() => {
    if (!active) return
    function onMouseDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        handler()
      }
    }
    document.addEventListener('mousedown', onMouseDown)
    return () => document.removeEventListener('mousedown', onMouseDown)
  }, [active, ref, handler])
}

/** True when any filter deviates from the default "no filter" state */
function isFiltered(props: DashboardFilterBarProps): boolean {
  return (
    props.selectedCategories.length > 0 ||
    props.dateStart !== null ||
    props.dateEnd !== null ||
    props.sortBy !== 'relevance' ||
    props.searchQuery.length > 0
  )
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function DashboardFilterBar(props: DashboardFilterBarProps) {
  const {
    categories,
    selectedCategories,
    onCategoryChange,
    dateStart,
    dateEnd,
    onDateChange,
    sortBy,
    onSortChange,
    viewMode,
    onViewModeChange,
    onReset,
    searchQuery,
    onSearchChange,
  } = props

  /* ---- Category dropdown state ---- */
  const [catOpen, setCatOpen] = useState(false)
  const catRef = useRef<HTMLDivElement>(null)
  useClickOutside(catRef, () => setCatOpen(false), catOpen)

  function toggleCategory(cat: string) {
    if (selectedCategories.includes(cat)) {
      onCategoryChange(selectedCategories.filter((c) => c !== cat))
    } else {
      onCategoryChange([...selectedCategories, cat])
    }
  }

  const categoryLabel =
    selectedCategories.length === 0
      ? 'All Categories'
      : `${selectedCategories.length} selected`

  /* ---- Sort dropdown state ---- */
  const [sortOpen, setSortOpen] = useState(false)
  const sortRef = useRef<HTMLDivElement>(null)
  useClickOutside(sortRef, () => setSortOpen(false), sortOpen)

  const currentSortLabel =
    SORT_OPTIONS.find((o) => o.id === sortBy)?.label ?? 'Most Relevant'

  /* ---- Render ---- */
  return (
    <div className="bg-surface-card rounded-2xl shadow-warm-sm p-4">
      <div className="flex items-center gap-3 flex-wrap">
        {/* ── Search input ── */}
        <div className="relative flex-1 min-w-[180px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search papers..."
            className="w-full bg-surface-inset rounded-full pl-10 pr-4 py-2 text-sm text-foreground
                       placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-accent/30"
          />
        </div>

        {/* ── Category dropdown (multi-select) ── */}
        <div ref={catRef} className="relative">
          <button
            type="button"
            onClick={() => setCatOpen((v) => !v)}
            className="flex items-center gap-1.5 bg-surface-inset rounded-full px-4 py-2 text-sm
                       text-foreground-secondary hover:bg-surface-card transition-colors cursor-pointer select-none"
          >
            {categoryLabel}
            <ChevronDown
              className={`h-3.5 w-3.5 text-foreground-muted transition-transform ${catOpen ? 'rotate-180' : ''}`}
            />
          </button>

          {catOpen && (
            <div className="absolute left-0 top-full mt-2 z-50 w-56 bg-surface-card shadow-warm-lg rounded-xl p-3">
              <div className="space-y-0.5 max-h-64 overflow-y-auto">
                {(categories.length > 0 ? categories : [...ARXIV_CATEGORIES]).map(
                  (cat) => {
                    const checked = selectedCategories.includes(cat)
                    return (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => toggleCategory(cat)}
                        className="w-full flex items-center justify-start gap-2.5 px-2 py-1.5 rounded-lg cursor-pointer
                                   hover:bg-surface-inset transition-colors text-sm text-left"
                      >
                        <span
                          className={`flex items-center justify-center min-w-4 min-h-4 h-4 w-4 rounded
                            ${checked ? 'bg-accent text-on-accent' : 'bg-surface-inset'}`}
                        >
                          {checked && <Check className="h-3 w-3" />}
                        </span>
                        <span className="text-foreground-secondary">{cat}</span>
                      </button>
                    )
                  },
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── Date picker ── */}
        <DatePicker
          startDate={dateStart}
          endDate={dateEnd}
          onDateChange={onDateChange}
        />

        {/* ── Sort selector ── */}
        <div ref={sortRef} className="relative">
          <button
            type="button"
            onClick={() => setSortOpen((v) => !v)}
            className="flex items-center gap-1.5 text-sm cursor-pointer select-none"
          >
            <span className="text-foreground-muted">Sort by:</span>
            <span className="text-accent font-medium">{currentSortLabel}</span>
            <ChevronDown
              className={`h-3.5 w-3.5 text-foreground-muted transition-transform ${sortOpen ? 'rotate-180' : ''}`}
            />
          </button>

          {sortOpen && (
            <div className="absolute left-0 top-full mt-2 z-50 w-44 bg-surface-card shadow-warm-lg rounded-xl p-2">
              {SORT_OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => {
                    onSortChange(opt.id)
                    setSortOpen(false)
                  }}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors cursor-pointer ${
                    sortBy === opt.id
                      ? 'bg-accent/10 text-accent font-medium'
                      : 'text-foreground-secondary hover:bg-surface-inset'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ── Reset button (visible only when filters are active) ── */}
        {isFiltered(props) && (
          <button
            type="button"
            onClick={onReset}
            className="text-accent hover:text-accent-hover text-sm font-medium transition-colors cursor-pointer"
          >
            Reset
          </button>
        )}

        {/* ── Spacer ── */}
        <div className="flex-1" />

        {/* ── Grid / List toggle ── */}
        <div className="flex gap-1">
          <button
            type="button"
            onClick={() => onViewModeChange('grid')}
            className={`p-2 rounded-lg transition-colors cursor-pointer ${
              viewMode === 'grid'
                ? 'bg-accent text-on-accent'
                : 'text-foreground-muted bg-surface-inset hover:text-foreground-secondary'
            }`}
            title="Grid view"
          >
            <LayoutGrid className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => onViewModeChange('list')}
            className={`p-2 rounded-lg transition-colors cursor-pointer ${
              viewMode === 'list'
                ? 'bg-accent text-on-accent'
                : 'text-foreground-muted bg-surface-inset hover:text-foreground-secondary'
            }`}
            title="List view"
          >
            <List className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
