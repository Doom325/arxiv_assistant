"use client"

import { useEffect, useState } from "react"

interface PaperTOCProps {
  sections?: Array<{ id: string; label: string }>
}

const DEFAULT_SECTIONS = [
  { id: "abstract", label: "Abstract" },
  { id: "ai-synthesis", label: "AI Analysis" },
  { id: "references", label: "References" },
  { id: "patterns", label: "Patterns" },
  { id: "recommendations", label: "Recommendations" },
]

export default function PaperTOC({ sections = DEFAULT_SECTIONS }: PaperTOCProps) {
  const [activeSection, setActiveSection] = useState<string>(sections[0]?.id ?? "")

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id)
          }
        })
      },
      { rootMargin: "-20% 0px -70% 0px" }
    )

    sections.forEach(({ id }) => {
      const el = document.getElementById(id)
      if (el) observer.observe(el)
    })

    return () => observer.disconnect()
  }, [sections])

  const handleClick = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" })
    setActiveSection(id)
  }

  return (
    <nav className="hidden xl:block sticky top-24">
      <p className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted mb-4">
        On this page
      </p>
      <ul className="space-y-0.5">
        {sections.map(({ id, label }) => {
          const isActive = activeSection === id
          return (
            <li key={id}>
              <button
                onClick={() => handleClick(id)}
                className={`text-sm py-1.5 block w-full text-left pl-3 border-l-2 transition-colors ${
                  isActive
                    ? "text-accent font-medium border-accent"
                    : "text-foreground-muted border-transparent hover:text-foreground-secondary"
                }`}
              >
                {label}
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
