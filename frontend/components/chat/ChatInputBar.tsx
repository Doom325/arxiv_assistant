"use client";

import { Send } from "lucide-react";
import RippleButton from "../RippleButton";

interface ChatInputBarProps {
    input: string;
    setInput: (value: string) => void;
    onSubmit: (e?: React.FormEvent) => void;
    isLoading: boolean;
}

export default function ChatInputBar({ input, setInput, onSubmit, isLoading }: ChatInputBarProps) {
    return (
        <form onSubmit={onSubmit} className="relative">
            <div className="bg-surface-card rounded-xl shadow-warm p-1">
                <div className="relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask a question about your research..."
                        className="w-full bg-transparent rounded-xl pl-5 pr-14 py-4 text-foreground placeholder:text-foreground-muted focus:outline-none text-base"
                        style={{ fontFamily: "var(--font-body)" }}
                    />
                    <RippleButton
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-accent hover:bg-accent-hover text-on-accent rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        <Send className="h-5 w-5" />
                    </RippleButton>
                </div>
            </div>
        </form>
    );
}
