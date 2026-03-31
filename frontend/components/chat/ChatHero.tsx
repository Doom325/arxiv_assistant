"use client";

import { MessageCircle } from "lucide-react";

const suggestedPrompts = [
    "What are the latest advances in RLHF?",
    "Summarize recent papers on vision-language models",
    "Which papers discuss multi-agent systems?",
    "What novel architectures were proposed this week?",
];

interface ChatHeroProps {
    onPromptClick: (prompt: string) => void;
}

export default function ChatHero({ onPromptClick }: ChatHeroProps) {
    return (
        <div className="flex flex-col items-center justify-center h-full px-6">
            {/* Featured hero panel */}
            <div className="bg-surface-featured rounded-2xl px-8 md:px-12 py-12 md:py-16 text-center w-full max-w-2xl mb-10">
                {/* Label */}
                <p
                    className="text-[10px] font-bold uppercase text-on-featured/60 mb-4"
                    style={{ letterSpacing: "var(--tracking-label)" }}
                >
                    Deep Dive
                </p>

                {/* Icon */}
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-white/10 mb-5">
                    <MessageCircle className="h-7 w-7 text-on-featured/80" />
                </div>

                {/* Mixed-weight headline */}
                <h1 className="mb-3" style={{ fontFamily: "var(--font-display)" }}>
                    <span className="text-3xl md:text-4xl font-extralight text-on-featured">
                        Deep{" "}
                    </span>
                    <span className="text-3xl md:text-4xl font-bold italic text-on-featured">
                        Dive
                    </span>
                </h1>

                {/* Subtitle */}
                <p
                    className="text-sm text-on-featured/80 italic max-w-md mx-auto"
                    style={{ fontFamily: "var(--font-display)" }}
                >
                    Ask anything about your paper library. I&apos;ll search through your indexed papers and provide relevant, grounded answers.
                </p>
            </div>

            {/* Suggested prompts */}
            <div className="w-full max-w-2xl">
                <p
                    className="text-[10px] font-bold uppercase text-foreground-muted mb-3 text-center"
                    style={{ letterSpacing: "var(--tracking-label)" }}
                >
                    Try asking
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {suggestedPrompts.map((prompt) => (
                        <button
                            key={prompt}
                            onClick={() => onPromptClick(prompt)}
                            className="text-left px-5 py-4 bg-surface-card rounded-xl text-sm text-foreground-secondary hover:text-foreground hover:bg-surface-inset transition-colors shadow-warm-sm"
                            style={{ fontFamily: "var(--font-body)" }}
                        >
                            {prompt}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
