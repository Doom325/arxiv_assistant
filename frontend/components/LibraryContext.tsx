"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getBookmarkedIds, getLibraryLists } from "../lib/api";

interface LibraryContextType {
    bookmarkedMap: Record<number, string[]>;
    lists: string[];
    refreshLibrary: () => Promise<void>;
    createList: (name: string) => Promise<void>;
    addOptimisticBookmark: (id: number, list: string) => void;
    removeOptimisticBookmark: (id: number, list: string) => void;
}

const LibraryContext = createContext<LibraryContextType | undefined>(undefined);

export function LibraryProvider({ children }: { children: React.ReactNode }) {
    const [bookmarkedMap, setBookmarkedMap] = useState<Record<number, string[]>>({});
    const [lists, setLists] = useState<string[]>([]);

    const refreshLibrary = useCallback(async () => {
        try {
            const apiBase = "/api";
            // Get all items in library to see which papers are in which lists
            const [libRes, listNames] = await Promise.all([
                fetch(`${apiBase}/library`).then(r => r.json()),
                fetch(`${apiBase}/library/lists`).then(r => r.json())
            ]);

            const newMap: Record<number, string[]> = {};
            (libRes as any[]).forEach(item => {
                if (item.id) {
                    if (!newMap[item.id]) newMap[item.id] = [];
                    if (item.list_name) newMap[item.id].push(item.list_name);
                }
            });

            setBookmarkedMap(newMap);
            setLists(listNames);
        } catch (e) {
            console.error("Failed to refresh library context", e);
        }
    }, []);

    useEffect(() => {
        refreshLibrary();
    }, [refreshLibrary]);

    const addOptimisticBookmark = (id: number, list: string) => {
        setBookmarkedMap(prev => {
            const current = prev[id] || [];
            if (current.includes(list)) return prev;
            return { ...prev, [id]: [...current, list] };
        });
    };

    const removeOptimisticBookmark = (id: number, list: string) => {
        setBookmarkedMap(prev => {
            const current = prev[id] || [];
            const next = current.filter(l => l !== list);
            if (next.length === 0) {
                const { [id]: _, ...rest } = prev;
                return rest;
            }
            return { ...prev, [id]: next };
        });
    };

    const createListAction = async (name: string) => {
        const { createList } = await import("../lib/api");
        await createList(name);
        await refreshLibrary();
    };

    return (
        <LibraryContext.Provider value={{ bookmarkedMap, lists, refreshLibrary, createList: createListAction, addOptimisticBookmark, removeOptimisticBookmark }}>
            {children}
        </LibraryContext.Provider>
    );
}

export function useLibrary() {
    const context = useContext(LibraryContext);
    if (context === undefined) {
        throw new Error("useLibrary must be used within a LibraryProvider");
    }
    return context;
}
