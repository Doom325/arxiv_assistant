"use client";

import Link from "next/link";
import { FileText } from "lucide-react";

interface ChatSourceCardProps {
    source: string;
}

export default function ChatSourceCard({ source }: ChatSourceCardProps) {
    // Try to extract arxiv ID from source text
    const arxivMatch = source.match(/(\d{4}\.\d{4,5})/);
    const arxivId = arxivMatch?.[1];

    return (
        <div className="flex items-start gap-3 bg-surface-inset rounded-xl p-3 transition-colors">
            <FileText className="h-4 w-4 text-accent mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
                <p className="text-sm text-foreground-secondary truncate">{source}</p>
                {arxivId && (
                    <Link
                        href={`/paper/${arxivId}`}
                        className="text-xs text-accent hover:text-accent-hover mt-1 inline-block transition-colors"
                    >
                        View paper &rarr;
                    </Link>
                )}
            </div>
        </div>
    );
}
