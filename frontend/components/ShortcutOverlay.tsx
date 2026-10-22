"use client";

import { motion, AnimatePresence } from "framer-motion";
import { SHORTCUT_DEFINITIONS } from "../lib/navigation";

export interface ShortcutOverlayProps {
    open: boolean;
    onClose: () => void;
}

export const shortcuts = SHORTCUT_DEFINITIONS;

export default function ShortcutOverlay({ open, onClose }: ShortcutOverlayProps) {
    return (
        <AnimatePresence>
            {open && (
                <>
                    <motion.div
                        className="fixed inset-0 z-[90] bg-foreground/20 backdrop-blur-sm"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                    />
                    <motion.div
                        className="fixed inset-0 z-[91] flex items-center justify-center"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 400, damping: 25 }}
                    >
                        <div
                            role="dialog"
                            aria-modal="true"
                            aria-labelledby="shortcut-overlay-title"
                            className="bg-surface-card shadow-warm-lg rounded-2xl p-6 max-w-md w-full mx-4"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h2 id="shortcut-overlay-title" className="text-lg font-bold text-foreground">
                                    Keyboard Shortcuts
                                </h2>
                                <button
                                    type="button"
                                    onClick={onClose}
                                    className="text-foreground-muted hover:text-foreground transition-colors"
                                    aria-label="Close shortcuts overlay"
                                >
                                    ✕
                                </button>
                            </div>
                            <p className="text-foreground-muted uppercase tracking-[0.08em] text-xs mb-3">
                                Navigation &amp; Actions
                            </p>
                            <div className="grid grid-cols-2 gap-2">
                                {shortcuts.map((s, i) => (
                                    <div key={i} className="flex items-center gap-3 py-1.5">
                                        <div className="flex gap-1">
                                            {s.keys.map((key, j) => (
                                                <kbd
                                                    key={j}
                                                    className="px-2 py-0.5 text-xs font-mono text-foreground-secondary bg-surface-inset rounded min-w-[24px] text-center"
                                                >
                                                    {key}
                                                </kbd>
                                            ))}
                                        </div>
                                        <span className="text-xs text-foreground-secondary">{s.description}</span>
                                    </div>
                                ))}
                            </div>
                            <p className="text-[10px] text-foreground-muted mt-4 text-center">
                                Press{" "}
                                <kbd className="px-1 py-0.5 bg-surface-inset rounded text-foreground-secondary">
                                    ?
                                </kbd>{" "}
                                or{" "}
                                <kbd className="px-1 py-0.5 bg-surface-inset rounded text-foreground-secondary">
                                    Esc
                                </kbd>{" "}
                                to close
                            </p>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
