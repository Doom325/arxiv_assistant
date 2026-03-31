'use client'

import { Plus, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { addPaper } from '../lib/api'

export default function AddPaperForm() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      const paper = await addPaper(query)
      setQuery('')
      toast.success(`Added "${paper.title || paper.arxiv_id}"`)
      router.push(`/paper/${paper.arxiv_id}`)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to add paper'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <div className="relative group">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="ArXiv ID or URL..."
          disabled={loading}
          className="w-full bg-surface-inset border border-foreground-muted/20 rounded-lg py-2 px-3 text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-accent transition-all disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="absolute right-1 top-1 p-1.5 bg-surface-card rounded-md text-foreground-muted hover:text-foreground hover:bg-accent hover:text-on-accent transition-all disabled:opacity-30"
        >
          {loading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Plus size={16} />
          )}
        </button>
      </div>
    </form>
  )
}
