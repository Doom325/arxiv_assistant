"use client";

import Link from "next/link";
import { ExternalLink, User } from "lucide-react";
import { Citation } from "@/lib/api";

interface ReferencesSectionProps {
  citations: Citation[];
}

export default function ReferencesSection({ citations }: ReferencesSectionProps) {
  if (citations.length === 0) return null;

  return (
    <section>
      {/* Section label */}
      <div className="flex items-center mb-4">
        <h3
          className="text-[10px] font-bold uppercase tracking-widest text-foreground-muted"
          style={{ fontFamily: "var(--font-body)" }}
        >
          REFERENCES
        </h3>
        <span className="bg-surface-inset text-foreground-muted rounded-md px-2 py-0.5 text-xs font-mono ml-3">
          {citations.length}
        </span>
      </div>

      {/* Thin warm rule */}
      <div className="h-px bg-foreground-muted/20 mb-6" />

      {/* Citation cards */}
      <div className="space-y-3">
        {citations.map((citation, idx) => (
          <div
            key={idx}
            className="group bg-surface-card rounded-xl p-4 shadow-warm-sm"
          >
            <div className="flex justify-between items-start gap-4">
              <div className="flex-grow min-w-0">
                {/* Title + "Available locally" chip */}
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  {citation.resolved_id ? (
                    <Link
                      href={`/paper/${citation.resolved_id}`}
                      className="text-accent hover:underline font-semibold leading-snug"
                    >
                      {citation.title || "Untitled Reference"}
                    </Link>
                  ) : (
                    <span className="text-foreground font-semibold leading-snug">
                      {citation.title || "Untitled Reference"}
                    </span>
                  )}

                  {citation.resolved_id && (
                    <span className="bg-accent/15 text-accent rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wider font-bold whitespace-nowrap">
                      Available locally
                    </span>
                  )}
                </div>

                {/* Authors */}
                {citation.authors && citation.authors.length > 0 && (
                  <div className="flex items-center text-sm text-foreground-muted italic mb-2">
                    <User className="h-3.5 w-3.5 mr-2 text-foreground-muted flex-shrink-0" />
                    <span className="truncate">
                      {citation.authors.join(", ")}
                    </span>
                  </div>
                )}

                {/* Raw citation */}
                <p className="text-xs text-foreground-muted italic bg-surface-inset p-2 rounded-lg">
                  {citation.raw}
                </p>
              </div>

              {/* External link button */}
              {citation.url && (
                <a
                  href={citation.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-shrink-0 p-2 bg-surface-inset rounded-lg text-foreground-muted hover:text-accent hover:bg-accent/10 transition-all opacity-0 group-hover:opacity-100"
                  aria-label="Open external link"
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
