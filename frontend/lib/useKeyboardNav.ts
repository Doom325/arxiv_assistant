"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { CHORD_MAP, resolveKeyboardNavAction } from "./navigation";

export const chordMap: Record<string, string> = CHORD_MAP;

export interface UseKeyboardNavOptions {
    itemCount?: number;
    onPeek?: (index: number) => void;
    onBookmark?: (index: number) => void;
    enableChords?: boolean;
    enableOverlayShortcut?: boolean;
}

export function useKeyboardNav({
    itemCount = 0,
    onPeek,
    onBookmark,
    enableChords = true,
    enableOverlayShortcut = true,
}: UseKeyboardNavOptions = {}) {
    const router = useRouter();
    const [focusedIndex, setFocusedIndex] = useState(-1);
    const [showShortcuts, setShowShortcuts] = useState(false);
    const chordBufferRef = useRef<string | null>(null);
    const chordTimerRef = useRef<NodeJS.Timeout | null>(null);
    const onPeekRef = useRef(onPeek);
    const onBookmarkRef = useRef(onBookmark);
    const hasPeek = Boolean(onPeek);
    const hasBookmark = Boolean(onBookmark);

    useEffect(() => {
        onPeekRef.current = onPeek;
        onBookmarkRef.current = onBookmark;
    }, [onPeek, onBookmark]);

    const isInputFocused = useCallback(() => {
        const el = document.activeElement as HTMLElement | null;
        const tag = el?.tagName?.toLowerCase();
        return (
            tag === "input" ||
            tag === "textarea" ||
            tag === "select" ||
            Boolean(el?.isContentEditable)
        );
    }, []);

    useEffect(() => {
        const clearPendingChord = () => {
            chordBufferRef.current = null;
            if (chordTimerRef.current) clearTimeout(chordTimerRef.current);
        };

        const handleKeyDown = (e: KeyboardEvent) => {
            const action = resolveKeyboardNavAction(e, {
                chordPending: chordBufferRef.current === "g",
                focusedIndex,
                itemCount,
                isInputFocused: isInputFocused(),
                enableChords,
                enableOverlayShortcut,
                hasPeek,
                hasBookmark,
            });

            if ("clearChord" in action && action.clearChord) {
                clearPendingChord();
            }
            if ("preventDefault" in action && action.preventDefault) {
                e.preventDefault();
            }

            switch (action.type) {
                case "start-chord":
                    chordBufferRef.current = "g";
                    if (chordTimerRef.current) clearTimeout(chordTimerRef.current);
                    chordTimerRef.current = setTimeout(() => {
                        chordBufferRef.current = null;
                    }, 500);
                    break;
                case "navigate":
                    router.push(action.href);
                    break;
                case "focus":
                    setFocusedIndex(action.nextIndex);
                    break;
                case "peek":
                    setFocusedIndex(action.nextFocusedIndex);
                    onPeekRef.current?.(action.index);
                    break;
                case "bookmark":
                    onBookmarkRef.current?.(action.index);
                    break;
                case "toggle-shortcuts":
                    setShowShortcuts((prev) => !prev);
                    break;
                case "escape":
                    setFocusedIndex(-1);
                    if (action.closeShortcuts) setShowShortcuts(false);
                    break;
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => {
            document.removeEventListener("keydown", handleKeyDown);
            if (chordTimerRef.current) clearTimeout(chordTimerRef.current);
        };
    }, [
        itemCount,
        focusedIndex,
        hasPeek,
        hasBookmark,
        enableChords,
        enableOverlayShortcut,
        isInputFocused,
        router,
    ]);

    return { focusedIndex, setFocusedIndex, showShortcuts, setShowShortcuts };
}
