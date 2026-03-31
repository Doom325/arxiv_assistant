"use client";

import { motion } from "framer-motion";
import { Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import ChatSourceCard from "./ChatSourceCard";

export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    sources?: string[];
}

interface ChatMessageBubbleProps {
    message: ChatMessage;
}

export default function ChatMessageBubble({ message }: ChatMessageBubbleProps) {
    const isUser = message.role === "user";

    return (
        <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className={`flex ${isUser ? "justify-end" : "justify-start"}`}
        >
            <div
                className={`flex max-w-[80%] rounded-xl p-5 ${
                    isUser
                        ? "bg-surface-inset text-foreground"
                        : "bg-surface-card text-foreground shadow-warm-sm"
                }`}
            >
                {/* Icon */}
                <div className="mr-3 mt-1 flex-shrink-0">
                    {isUser ? (
                        <User className="h-5 w-5 text-foreground-muted" />
                    ) : (
                        <Bot className="h-5 w-5 text-accent" />
                    )}
                </div>

                {/* Content */}
                <div className="min-w-0 flex-1">
                    {isUser ? (
                        <p className="text-sm leading-relaxed">{message.content}</p>
                    ) : (
                        <div className="prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground prose-p:my-1 prose-strong:text-foreground prose-a:text-accent prose-a:no-underline hover:prose-a:underline prose-code:text-foreground-secondary prose-code:bg-surface-inset prose-code:rounded prose-code:px-1 prose-code:py-0.5 prose-pre:bg-surface-inset prose-pre:rounded-xl prose-li:text-foreground prose-ul:text-foreground">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm, remarkMath]}
                                rehypePlugins={[rehypeKatex]}
                            >
                                {message.content}
                            </ReactMarkdown>
                        </div>
                    )}

                    {/* Source citations */}
                    {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-foreground/5 space-y-2">
                            <p
                                className="text-[10px] font-bold uppercase text-foreground-muted"
                                style={{ letterSpacing: "var(--tracking-label)" }}
                            >
                                Sources
                            </p>
                            {message.sources.map((source, i) => (
                                <ChatSourceCard key={i} source={source} />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}
