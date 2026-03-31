'use client'

import { useState, useRef, useEffect, useCallback } from 'react'

/* ------------------------------------------------------------------ */
/*  Types & defaults                                                   */
/* ------------------------------------------------------------------ */

interface DatePickerProps {
  startDate: string | null   // ISO date string or null
  endDate: string | null
  onDateChange: (start: string | null, end: string | null) => void
  presets?: Array<{ label: string; days: number }>
}

const DEFAULT_PRESETS = [
  { label: 'Last 7 days', days: 7 },
  { label: 'Last 30 days', days: 30 },
  { label: 'Last 90 days', days: 90 },
  { label: 'All time', days: 0 },
]

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

/** Return ISO date string (YYYY-MM-DD) for `daysAgo` days before today */
function daysAgoISO(daysAgo: number): string {
  const d = new Date()
  d.setDate(d.getDate() - daysAgo)
  return d.toISOString().slice(0, 10)
}

function todayISO(): string {
  return new Date().toISOString().slice(0, 10)
}

/** Pretty-print a date range for the trigger button */
function formatRange(
  start: string | null,
  end: string | null,
  presets: Array<{ label: string; days: number }>,
): string {
  if (!start && !end) return 'All time'

  // Check if the range matches a preset
  const today = todayISO()
  for (const p of presets) {
    if (p.days === 0 && !start && !end) return p.label
    if (p.days > 0 && end === today && start === daysAgoISO(p.days)) {
      return p.label
    }
  }

  // Custom range display
  const fmt = (iso: string) => {
    const [, m, d] = iso.split('-')
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    return `${months[parseInt(m, 10) - 1]} ${parseInt(d, 10)}`
  }

  if (start && end) return `${fmt(start)} \u2013 ${fmt(end)}`
  if (start) return `From ${fmt(start)}`
  return `Until ${fmt(end!)}`
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function DatePicker({
  startDate,
  endDate,
  onDateChange,
  presets = DEFAULT_PRESETS,
}: DatePickerProps) {
  const [open, setOpen] = useState(false)
  const [localStart, setLocalStart] = useState(startDate ?? '')
  const [localEnd, setLocalEnd] = useState(endDate ?? '')

  const wrapperRef = useRef<HTMLDivElement>(null)

  // Sync local state when props change externally
  useEffect(() => {
    setLocalStart(startDate ?? '')
    setLocalEnd(endDate ?? '')
  }, [startDate, endDate])

  // Close dropdown on outside click
  useEffect(() => {
    if (!open) return
    function handleClick(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  // Detect which preset (if any) is active
  const activePreset = useCallback(
    (p: { label: string; days: number }) => {
      if (p.days === 0) return !startDate && !endDate
      const today = todayISO()
      return endDate === today && startDate === daysAgoISO(p.days)
    },
    [startDate, endDate],
  )

  function selectPreset(p: { label: string; days: number }) {
    if (p.days === 0) {
      onDateChange(null, null)
      setLocalStart('')
      setLocalEnd('')
    } else {
      const s = daysAgoISO(p.days)
      const e = todayISO()
      onDateChange(s, e)
      setLocalStart(s)
      setLocalEnd(e)
    }
    setOpen(false)
  }

  function handleApply() {
    onDateChange(localStart || null, localEnd || null)
    setOpen(false)
  }

  function handleClear() {
    setLocalStart('')
    setLocalEnd('')
    onDateChange(null, null)
    setOpen(false)
  }

  return (
    <div ref={wrapperRef} className="relative inline-block">
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="bg-surface-inset text-foreground-secondary rounded-full px-4 py-1.5 text-sm
                   hover:bg-surface-card transition-colors cursor-pointer select-none"
      >
        {formatRange(startDate, endDate, presets)}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          className="absolute left-0 top-full mt-2 z-50 w-80
                     bg-surface-card shadow-warm-lg rounded-2xl p-4"
        >
          {/* Preset buttons */}
          <div className="flex flex-wrap gap-2 mb-4">
            {presets.map((p) => (
              <button
                key={p.label}
                type="button"
                onClick={() => selectPreset(p)}
                className={`rounded-full px-3 py-1 text-sm transition-colors cursor-pointer ${
                  activePreset(p)
                    ? 'bg-accent/15 text-accent'
                    : 'text-foreground-muted hover:bg-surface-inset'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Custom range inputs */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="block text-xs text-foreground-muted uppercase tracking-widest mb-1">
                From
              </label>
              <input
                type="date"
                value={localStart}
                onChange={(e) => setLocalStart(e.target.value)}
                className="w-full bg-surface-inset text-foreground rounded-xl px-3 py-2 text-sm
                           focus:ring-2 focus:ring-accent/30 focus:outline-none
                           border-none appearance-none"
                style={{ colorScheme: 'light' }}
              />
            </div>
            <div>
              <label className="block text-xs text-foreground-muted uppercase tracking-widest mb-1">
                To
              </label>
              <input
                type="date"
                value={localEnd}
                onChange={(e) => setLocalEnd(e.target.value)}
                className="w-full bg-surface-inset text-foreground rounded-xl px-3 py-2 text-sm
                           focus:ring-2 focus:ring-accent/30 focus:outline-none
                           border-none appearance-none"
                style={{ colorScheme: 'light' }}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={handleClear}
              className="text-foreground-muted text-xs hover:text-foreground transition-colors cursor-pointer"
            >
              Clear
            </button>
            <button
              type="button"
              onClick={handleApply}
              className="bg-accent text-on-accent rounded-full px-4 py-1.5 text-sm font-medium
                         hover:bg-accent-hover transition-colors cursor-pointer"
            >
              Apply
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
