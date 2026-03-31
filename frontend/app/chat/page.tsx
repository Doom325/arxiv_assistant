"use client";

import { useState, useRef, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import { api } from "../../lib/api";
import ChatHero from "../../components/chat/ChatHero";
import ChatMessageBubble, { ChatMessage } from "../../components/chat/ChatMessageBubble";
import ChatTypingIndicator from "../../components/chat/ChatTypingIndicator";
import ChatInputBar from "../../components/chat/ChatInputBar";

export default function ChatPage() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    const handleSubmit = async (e?: React.FormEvent, promptOverride?: string) => {
        if (e) e.preventDefault();
        const query = promptOverride || input;
        if (!query.trim()) return;

        const userMessage: ChatMessage = {
            id: Date.now().toString(),
            role: "user",
            content: query,
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const data = await api.chat(query);

            const aiMessage: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: data.response,
                sources: data.sources,
            };
            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            console.error(error);
            const errorMessage: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: "Sorry, I encountered an error while processing your request.",
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)]">
            {/* Message area */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 md:px-8 lg:px-12 pb-4">
                {messages.length === 0 && !isLoading ? (
                    <ChatHero onPromptClick={(prompt) => handleSubmit(undefined, prompt)} />
                ) : (
                    <div className="max-w-3xl mx-auto space-y-5 py-6">
                        <AnimatePresence>
                            {messages.map((message) => (
                                <ChatMessageBubble key={message.id} message={message} />
                            ))}
                        </AnimatePresence>

                        <AnimatePresence>
                            {isLoading && <ChatTypingIndicator />}
                        </AnimatePresence>
                    </div>
                )}
            </div>

            {/* Input bar */}
            <div className="px-4 md:px-8 lg:px-12 pb-4 pt-2">
                <div className="max-w-3xl mx-auto">
                    <ChatInputBar
                        input={input}
                        setInput={setInput}
                        onSubmit={handleSubmit}
                        isLoading={isLoading}
                    />
                </div>
            </div>
        </div>
    );
}
