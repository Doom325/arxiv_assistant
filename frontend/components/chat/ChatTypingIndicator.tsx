"use client";

import { motion } from "framer-motion";
import { Bot } from "lucide-react";

export default function ChatTypingIndicator() {
    return (
        <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex justify-start"
        >
            <div className="bg-surface-card rounded-xl p-4 flex items-center space-x-1.5 shadow-warm-sm">
                <Bot className="h-5 w-5 text-accent mr-2" />
                {[0, 1, 2].map((i) => (
                    <motion.div
                        key={i}
                        className="w-2 h-2 bg-accent/60 rounded-full"
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{
                            duration: 1.2,
                            repeat: Infinity,
                            delay: i * 0.2,
                            ease: "easeInOut",
                        }}
                    />
                ))}
            </div>
        </motion.div>
    );
}
