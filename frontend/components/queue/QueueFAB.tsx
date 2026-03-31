'use client'

import { Plus } from 'lucide-react'

interface QueueFABProps {
  onOpen: () => void
}

export default function QueueFAB({ onOpen }: QueueFABProps) {
  return (
    <button
      onClick={onOpen}
      className="fixed bottom-8 left-1/2 -translate-x-1/2 z-30 flex items-center gap-2 px-6 py-3 bg-[#2A4A1A] text-white rounded-full shadow-warm-lg font-medium text-sm hover:bg-[#1E3A0F] transition-colors"
      aria-label="Add new research item"
    >
      <Plus size={18} className="text-white" />
      Add New Research Item
    </button>
  )
}
