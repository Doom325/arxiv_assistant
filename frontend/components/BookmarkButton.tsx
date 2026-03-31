"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Bookmark, Plus, Check } from "lucide-react";
import { toast } from "sonner";
import { useLibrary } from "./LibraryContext";
import { addBookmark, removeBookmark, Paper } from "../lib/api";

// Global close: only one bookmark menu open at a time
let globalCloseCallback: (() => void) | null = null;

interface BookmarkButtonProps {
    paper: Paper;
    className?: string;
    iconClassName?: string;
}

export default function BookmarkButton({ paper, className = "", iconClassName = "h-5 w-5" }: BookmarkButtonProps) {
    const { bookmarkedMap, lists, addOptimisticBookmark, removeOptimisticBookmark, refreshLibrary } = useLibrary();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [justBookmarked, setJustBookmarked] = useState(false);
    const [menuPos, setMenuPos] = useState<{ top: number | undefined; bottom: number | undefined; left: number }>({ top: 0, bottom: undefined, left: 0 });
    const buttonRef = useRef<HTMLButtonElement>(null);
    const menuRef = useRef<HTMLDivElement>(null);

    const paperLists = paper.db_id ? (bookmarkedMap[paper.db_id] || []) : [];
    const isBookmarked = paperLists.length > 0;

    // Position the portal menu using fixed positioning (viewport-relative)
    const updateMenuPosition = useCallback(() => {
        if (!buttonRef.current) return;
        const rect = buttonRef.current.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const menuHeight = menuRef.current?.offsetHeight || 200;
        const spaceBelow = viewportHeight - rect.bottom - 8;
        const spaceAbove = rect.top - 8;
        const left = Math.max(8, Math.min(rect.right - 200, window.innerWidth - 208));

        if (spaceBelow >= menuHeight) {
            setMenuPos({ top: rect.bottom + 8, bottom: undefined, left });
        } else if (spaceAbove >= menuHeight) {
            setMenuPos({ top: undefined, bottom: viewportHeight - rect.top + 8, left });
        } else {
            const top = Math.max(8, Math.min(rect.bottom + 8, viewportHeight - menuHeight - 8));
            setMenuPos({ top, bottom: undefined, left });
        }
    }, []);

    const closeMenu = useCallback(() => setIsMenuOpen(false), []);

    const openMenu = useCallback(() => {
        // Close any previously open bookmark menu
        if (globalCloseCallback && globalCloseCallback !== closeMenu) {
            globalCloseCallback();
        }
        globalCloseCallback = closeMenu;
        setIsMenuOpen(true);
    }, [closeMenu]);

    // Register/unregister as global close target
    useEffect(() => {
        if (isMenuOpen) {
            globalCloseCallback = closeMenu;
            updateMenuPosition();
            requestAnimationFrame(updateMenuPosition);
            window.addEventListener("scroll", updateMenuPosition, true);
            window.addEventListener("resize", updateMenuPosition);
            return () => {
                window.removeEventListener("scroll", updateMenuPosition, true);
                window.removeEventListener("resize", updateMenuPosition);
                if (globalCloseCallback === closeMenu) {
                    globalCloseCallback = null;
                }
            };
        }
    }, [isMenuOpen, updateMenuPosition, closeMenu]);

    // Close menu when clicking outside
    useEffect(() => {
        if (!isMenuOpen) return;
        const handleClickOutside = (e: MouseEvent) => {
            if (
                menuRef.current && !menuRef.current.contains(e.target as Node) &&
                buttonRef.current && !buttonRef.current.contains(e.target as Node)
            ) {
                setIsMenuOpen(false);
            }
        };
        // Use setTimeout to avoid the current click from immediately closing
        const timer = setTimeout(() => {
            document.addEventListener("mousedown", handleClickOutside);
        }, 0);
        return () => {
            clearTimeout(timer);
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [isMenuOpen]);

    const handleToggleBookmark = async (listName: string = "Bookmarks") => {
        if (!paper.db_id) return;

        const alreadyInThisList = paperLists.includes(listName);

        try {
            if (alreadyInThisList) {
                removeOptimisticBookmark(paper.db_id, listName);
                await removeBookmark(paper.db_id, listName);
                toast.success(`Removed from ${listName}`);
            } else {
                addOptimisticBookmark(paper.db_id, listName);
                await addBookmark(paper.db_id, listName);
                setJustBookmarked(true);
                setTimeout(() => setJustBookmarked(false), 600);
                toast.success(`Added to ${listName}`);
            }
            refreshLibrary();
        } catch (e) {
            console.error(e);
            toast.error("Bookmark action failed");
            refreshLibrary();
        }
    };

    const menuContent = (
        <AnimatePresence>
            {isMenuOpen && (
                <motion.div
                    ref={menuRef}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.12 }}
                    style={{
                        position: "fixed",
                        top: menuPos.top != null ? menuPos.top : undefined,
                        bottom: menuPos.bottom != null ? menuPos.bottom : undefined,
                        left: menuPos.left,
                        zIndex: 9999,
                        maxWidth: "calc(100vw - 16px)",
                    }}
                    onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                    }}
                >
                    <div className="bg-surface-card border border-border-default rounded-lg shadow-2xl p-2 min-w-[200px] max-h-[60vh] flex flex-col">
                        <div className="flex justify-between items-center px-2 mb-2 border-b border-border-default pb-1 shrink-0">
                            <p className="text-[10px] font-bold text-foreground-muted uppercase">Lists</p>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsMenuOpen(false);
                                }}
                                className="text-foreground-muted hover:text-foreground text-[10px]"
                            >
                                Close
                            </button>
                        </div>
                        <div className="overflow-y-auto max-h-[40vh] shrink">
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleToggleBookmark("Bookmarks");
                                    setIsMenuOpen(false);
                                }}
                                className="w-full text-left px-2 py-2 text-xs text-foreground hover:bg-surface-inset rounded flex items-center justify-between transition-colors"
                            >
                                <span className="flex items-center gap-2">
                                    <Bookmark className="h-3 w-3" />
                                    Bookmarks
                                </span>
                                {paperLists.includes("Bookmarks") && <Check className="h-3 w-3 text-accent" />}
                            </button>

                            {lists.filter(l => l !== "Bookmarks").map(list => (
                                <button
                                    key={list}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleToggleBookmark(list);
                                        setIsMenuOpen(false);
                                    }}
                                    className="w-full text-left px-2 py-2 text-xs text-foreground hover:bg-surface-inset rounded flex items-center justify-between transition-colors"
                                >
                                    <span>{list}</span>
                                    {paperLists.includes(list) && <Check className="h-3 w-3 text-accent" />}
                                </button>
                            ))}
                        </div>

                        <div className="mt-2 pt-2 border-t border-border-default shrink-0">
                            <div className="px-2 py-1">
                                <div className="flex items-center gap-2 bg-surface-inset rounded px-2 py-1 border border-transparent focus-within:border-accent transition-all">
                                    <Plus className="h-3 w-3 text-accent" />
                                    <input
                                        type="text"
                                        placeholder="New list..."
                                        className="bg-transparent border-none text-xs text-foreground focus:outline-none w-full"
                                        autoFocus
                                        onClick={(e) => e.stopPropagation()}
                                        onKeyDown={async (e) => {
                                            e.stopPropagation();
                                            if (e.key === 'Enter') {
                                                const name = e.currentTarget.value.trim();
                                                if (name) {
                                                    await handleToggleBookmark(name);
                                                    setIsMenuOpen(false);
                                                }
                                            }
                                        }}
                                    />
                                </div>
                                <p className="text-[9px] text-foreground-muted mt-1 px-1">Press Enter to create</p>
                            </div>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );

    return (
        <div className="relative">
            <motion.button
                ref={buttonRef}
                onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (isMenuOpen) {
                        setIsMenuOpen(false);
                    } else {
                        openMenu();
                    }
                }}
                animate={justBookmarked ? {
                    scale: [1, 1.3, 1],
                    transition: { duration: 0.3, ease: "easeOut" }
                } : {}}
                whileTap={{ scale: 0.9 }}
                className={`p-1 rounded-full hover:bg-surface-inset transition-colors ${isBookmarked ? "text-accent" : "text-foreground-muted"} ${className}`}
                title="Manage Lists"
            >
                <Bookmark className={`${iconClassName} ${isBookmarked ? "fill-current" : ""} transition-all duration-200`} />
            </motion.button>

            {/* Particle burst on bookmark */}
            <AnimatePresence>
                {justBookmarked && (
                    <>
                        {[0, 72, 144, 216, 288].map((angle) => (
                            <motion.div
                                key={angle}
                                initial={{ opacity: 1, scale: 0, x: 0, y: 0 }}
                                animate={{
                                    opacity: 0,
                                    scale: 1,
                                    x: Math.cos((angle * Math.PI) / 180) * 16,
                                    y: Math.sin((angle * Math.PI) / 180) * 16,
                                }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.4, ease: "easeOut" }}
                                className="absolute top-1/2 left-1/2 w-1.5 h-1.5 rounded-full bg-accent pointer-events-none"
                            />
                        ))}
                    </>
                )}
            </AnimatePresence>

            {/* List Selector Menu — rendered via portal to escape stacking contexts */}
            {typeof document !== "undefined" && createPortal(menuContent, document.body)}
        </div>
    );
}
