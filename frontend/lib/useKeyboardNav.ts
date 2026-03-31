"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";

interface UseKeyboardNavOptions {
    itemCount: number;
    onPeek?: (index: number) => void;
    onBookmark?: (index: number) => void;
}

const chordMap: Record<string, string> = {
    d: "/dashboard",
    r: "/research",
    c: "/chat",
    b: "/bookmarks",
    a: "/analysis",
    p: "/patterns",
    s: "/settings",
    q: "/queue",
    l: "/bookmarks",
};

export function useKeyboardNav({ itemCount, onPeek, onBookmark }: UseKeyboardNavOptions) {
    const router = useRouter();
    const [focusedIndex, setFocusedIndex] = useState(-1);
    const [showShortcuts, setShowShortcuts] = useState(false);
    const chordBufferRef = useRef<string | null>(null);
    const chordTimerRef = useRef<NodeJS.Timeout | null>(null);

    const isInputFocused = useCallback(() => {
        const tag = document.activeElement?.tagName?.toLowerCase();
        return tag === "input" || tag === "textarea" || tag === "select";
    }, []);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (isInputFocused()) return;
            if (e.metaKey || e.ctrlKey || e.altKey) return;

            // Chord handling: g + <letter>
            if (chordBufferRef.current === "g") {
                chordBufferRef.current = null;
                if (chordTimerRef.current) clearTimeout(chordTimerRef.current);
                const dest = chordMap[e.key];
                if (dest) {
                    e.preventDefault();
                    router.push(dest);
                }
                return;
            }

            switch (e.key) {
                case "j":
                    e.preventDefault();
                    setFocusedIndex((prev) => Math.min(prev + 1, itemCount - 1));
                    break;
                case "k":
                    e.preventDefault();
                    setFocusedIndex((prev) => Math.max(prev - 1, 0));
                    break;
                case " ":
                    e.preventDefault();
                    if (onPeek) {
                        if (focusedIndex >= 0) {
                            onPeek(focusedIndex);
                        } else if (itemCount > 0) {
                            setFocusedIndex(0);
                            onPeek(0);
                        }
                    }
                    break;
                case "b":
                    if (focusedIndex >= 0 && onBookmark) {
                        e.preventDefault();
                        onBookmark(focusedIndex);
                    }
                    break;
                case "g":
                    chordBufferRef.current = "g";
                    chordTimerRef.current = setTimeout(() => {
                        chordBufferRef.current = null;
                    }, 500);
                    break;
                case "?":
                    e.preventDefault();
                    setShowShortcuts((prev) => !prev);
                    break;
                case "Escape":
                    setFocusedIndex(-1);
                    setShowShortcuts(false);
                    break;
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [itemCount, focusedIndex, onPeek, onBookmark, isInputFocused, router]);

    return { focusedIndex, setFocusedIndex, showShortcuts, setShowShortcuts };
}
