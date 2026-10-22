export interface NavRouteConfig {
    name: string;
    href: string;
    activeOn: readonly string[];
    showBadge?: boolean;
}

export const CORE_NAV_ROUTES: readonly NavRouteConfig[] = [
    {
        name: "Queue",
        href: "/queue",
        activeOn: ["/", "/queue"],
        showBadge: true,
    },
    {
        name: "Archive",
        href: "/dashboard",
        activeOn: ["/dashboard", "/research"],
    },
    {
        name: "Library",
        href: "/bookmarks",
        activeOn: ["/bookmarks"],
    },
    {
        name: "Chat",
        href: "/chat",
        activeOn: ["/chat"],
    },
    {
        name: "Patterns",
        href: "/patterns",
        activeOn: ["/patterns"],
    },
    {
        name: "Timeline",
        href: "/timeline",
        activeOn: ["/timeline"],
    },
    {
        name: "Analysis",
        href: "/analysis",
        activeOn: ["/analysis"],
    },
];

export const SETTINGS_NAV_ROUTE: NavRouteConfig = {
    name: "Settings",
    href: "/settings",
    activeOn: ["/settings"],
};

export const ALL_NAV_ROUTES: readonly NavRouteConfig[] = [
    ...CORE_NAV_ROUTES,
    SETTINGS_NAV_ROUTE,
];

export const CHORD_MAP: Record<string, string> = {
    q: "/queue",
    d: "/dashboard",
    r: "/dashboard",
    l: "/bookmarks",
    b: "/bookmarks",
    c: "/chat",
    p: "/patterns",
    t: "/timeline",
    a: "/analysis",
    s: "/settings",
};

export interface ShortcutDefinition {
    keys: string[];
    description: string;
}

export const SHORTCUT_DEFINITIONS: ShortcutDefinition[] = [
    { keys: ["⌘", "K"], description: "Command palette" },
    { keys: ["J"], description: "Next paper" },
    { keys: ["K"], description: "Previous paper" },
    { keys: ["Space"], description: "Quick peek paper" },
    { keys: ["B"], description: "Bookmark focused paper" },
    { keys: ["?"], description: "Toggle shortcuts" },
    { keys: ["G", "Q"], description: "Go to Queue" },
    { keys: ["G", "D"], description: "Go to Archive" },
    { keys: ["G", "R"], description: "Go to Archive" },
    { keys: ["G", "L"], description: "Go to Library" },
    { keys: ["G", "B"], description: "Go to Library" },
    { keys: ["G", "C"], description: "Go to Chat" },
    { keys: ["G", "P"], description: "Go to Patterns" },
    { keys: ["G", "T"], description: "Go to Timeline" },
    { keys: ["G", "A"], description: "Go to Analysis" },
    { keys: ["G", "S"], description: "Go to Settings" },
    { keys: ["Esc"], description: "Clear focus / close" },
];

export const OPEN_ADD_PAPER_EVENT = "open-add-paper";

export function normalizePathname(pathname: string): string {
    if (!pathname || pathname === "/") return "/";
    return pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
}

export function isRouteActive(pathname: string, activeOn: readonly string[]): boolean {
    const normalized = normalizePathname(pathname);
    return activeOn.includes(normalized) || activeOn.includes(pathname);
}

export function buildResearchRedirectUrl(
    params?: Record<string, string | string[] | undefined> | URLSearchParams | string | null,
): string {
    if (!params) return "/dashboard";
    if (typeof params === "string") {
        const cleaned = params.replace(/^\?/, "").trim();
        return cleaned ? `/dashboard?${cleaned}` : "/dashboard";
    }
    if (params instanceof URLSearchParams) {
        const qs = params.toString();
        return qs ? `/dashboard?${qs}` : "/dashboard";
    }
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
        if (typeof value === "string") {
            search.set(key, value);
        } else if (Array.isArray(value)) {
            for (const item of value) {
                search.append(key, item);
            }
        }
    }
    const queryString = search.toString();
    return queryString ? `/dashboard?${queryString}` : "/dashboard";
}

export async function executeResearchRedirect(
    searchParams:
        | Promise<Record<string, string | string[] | undefined>>
        | Record<string, string | string[] | undefined>
        | undefined,
    redirectFn: (url: string) => never,
): Promise<never> {
    const resolvedParams = searchParams ? await searchParams : undefined;
    return redirectFn(buildResearchRedirectUrl(resolvedParams));
}

export interface DashboardFilterState {
    selectedCategories: string[];
    dateStart: string | null;
    dateEnd: string | null;
    searchQuery: string;
    sortBy: string;
}

export interface SearchParamsReader {
    get(name: string): string | null;
    toString(): string;
}

export function parseCategoriesParam(categoryParam: string | null): string[] {
    if (!categoryParam) return [];
    return categoryParam
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
}

export function parseDashboardSearchParams(params: SearchParamsReader): DashboardFilterState {
    return {
        selectedCategories: parseCategoriesParam(params.get("category")),
        dateStart: params.get("start") || null,
        dateEnd: params.get("end") || null,
        searchQuery: params.get("q") || "",
        sortBy: params.get("sort") || "relevance",
    };
}

export function serializeDashboardSearchParams(state: DashboardFilterState): string {
    const params = new URLSearchParams();
    if (state.selectedCategories.length > 0) {
        params.set("category", state.selectedCategories.join(","));
    }
    if (state.dateStart) params.set("start", state.dateStart);
    if (state.dateEnd) params.set("end", state.dateEnd);
    const trimmedQuery = state.searchQuery.trim();
    if (trimmedQuery) params.set("q", trimmedQuery);
    if (state.sortBy !== "relevance") params.set("sort", state.sortBy);
    return params.toString();
}

export function shouldUseDashboardSearchApi(searchQuery: string): boolean {
    return searchQuery.trim().length > 0;
}

export function hasActiveDashboardFilters(state: DashboardFilterState): boolean {
    return (
        state.selectedCategories.length > 0 ||
        Boolean(state.dateStart) ||
        Boolean(state.dateEnd) ||
        shouldUseDashboardSearchApi(state.searchQuery) ||
        state.sortBy !== "relevance"
    );
}

export function shouldCacheDashboardPapers(state: DashboardFilterState): boolean {
    return !hasActiveDashboardFilters(state);
}

export interface StorageLike {
    getItem(key: string): string | null;
    setItem(key: string, value: string): void;
    clear(): void;
}

export function writeDashboardCacheIfEligible(
    storage: Pick<StorageLike, "setItem"> | null | undefined,
    state: DashboardFilterState,
    papers: unknown[],
    pageNum: number,
    hasMore: boolean,
    now: number = Date.now(),
): boolean {
    if (!storage || !shouldCacheDashboardPapers(state)) {
        return false;
    }
    try {
        storage.setItem("dashboard_papers", JSON.stringify(papers));
        storage.setItem("dashboard_page", pageNum.toString());
        storage.setItem("dashboard_has_more", hasMore.toString());
        storage.setItem("dashboard_cached_at", now.toString());
        return true;
    } catch {
        return false;
    }
}

const MODIFIER_KEYS = new Set(["Shift", "Control", "Alt", "Meta", "CapsLock"]);

export interface KeyboardNavEventInput {
    key: string;
    metaKey?: boolean;
    ctrlKey?: boolean;
    altKey?: boolean;
}

export interface KeyboardNavStateInput {
    chordPending: boolean;
    focusedIndex: number;
    itemCount: number;
    isInputFocused: boolean;
    enableChords: boolean;
    enableOverlayShortcut: boolean;
    hasPeek: boolean;
    hasBookmark: boolean;
}

export type KeyboardNavAction =
    | { type: "none"; clearChord?: boolean }
    | { type: "start-chord" }
    | { type: "navigate"; href: string; preventDefault: true; clearChord: true }
    | { type: "focus"; nextIndex: number; preventDefault: true; clearChord?: boolean }
    | {
          type: "peek";
          index: number;
          nextFocusedIndex: number;
          preventDefault: true;
          clearChord?: boolean;
      }
    | { type: "bookmark"; index: number; preventDefault: true }
    | { type: "toggle-shortcuts"; preventDefault: true; clearChord?: boolean }
    | { type: "escape"; closeShortcuts: boolean; clearChord?: boolean };

export function resolveKeyboardNavAction(
    event: KeyboardNavEventInput,
    state: KeyboardNavStateInput,
): KeyboardNavAction {
    if (state.isInputFocused || event.metaKey || event.ctrlKey || event.altKey) {
        return { type: "none" };
    }

    if (MODIFIER_KEYS.has(event.key)) {
        return { type: "none" };
    }

    let clearedPendingChord = false;
    if (state.chordPending) {
        const chordDest = CHORD_MAP[event.key.toLowerCase()];
        if (chordDest) {
            if (state.enableChords) {
                return {
                    type: "navigate",
                    href: chordDest,
                    preventDefault: true,
                    clearChord: true,
                };
            }
            // In item mode (enableChords: false), consume recognized g+<chord> keys
            // (such as g+b) so they never trigger single-key item actions.
            return { type: "none", clearChord: true };
        }
        // Unrecognized second key after 'g': clear pending chord and fall through
        // so non-colliding item keys (j, k, Space, Escape) still execute.
        clearedPendingChord = true;
    }

    const chordSuffix = clearedPendingChord ? { clearChord: true as const } : {};

    switch (event.key) {
        case "j":
            if (state.itemCount <= 0) return { type: "none", ...chordSuffix };
            return {
                type: "focus",
                nextIndex: Math.min(state.focusedIndex + 1, state.itemCount - 1),
                preventDefault: true,
                ...chordSuffix,
            };
        case "k":
            if (state.itemCount <= 0) return { type: "none", ...chordSuffix };
            return {
                type: "focus",
                nextIndex: Math.max(state.focusedIndex - 1, 0),
                preventDefault: true,
                ...chordSuffix,
            };
        case " ":
            if (!state.hasPeek || state.itemCount <= 0) return { type: "none", ...chordSuffix };
            {
                const index = state.focusedIndex >= 0 ? state.focusedIndex : 0;
                return {
                    type: "peek",
                    index,
                    nextFocusedIndex: index,
                    preventDefault: true,
                    ...chordSuffix,
                };
            }
        case "b":
            if (state.focusedIndex < 0 || !state.hasBookmark) {
                return { type: "none", ...chordSuffix };
            }
            return {
                type: "bookmark",
                index: state.focusedIndex,
                preventDefault: true,
            };
        case "g":
            return { type: "start-chord" };
        case "?":
            if (!state.enableOverlayShortcut) return { type: "none", ...chordSuffix };
            return { type: "toggle-shortcuts", preventDefault: true, ...chordSuffix };
        case "Escape":
            return {
                type: "escape",
                closeShortcuts: state.enableOverlayShortcut,
                ...chordSuffix,
            };
        default:
            return { type: "none", ...chordSuffix };
    }
}

export function triggerOpenAddPaper(
    onAddPaperOpen?: () => void,
    eventTarget?: Pick<EventTarget, "dispatchEvent"> | null,
): void {
    if (onAddPaperOpen) {
        onAddPaperOpen();
        return;
    }
    const target = eventTarget ?? (typeof window !== "undefined" ? window : null);
    target?.dispatchEvent(new CustomEvent(OPEN_ADD_PAPER_EVENT));
}

export interface SubmitAddPaperDeps<TPaper extends { title?: string; arxiv_id: string }> {
    addPaperFn: (query: string) => Promise<TPaper>;
    onResetQuery: () => void;
    onSuccessToast: (message: string) => void;
    onErrorToast: (message: string) => void;
    onSuccess?: () => void;
    onNavigate: (href: string) => void;
}

export async function submitAddPaperRequest<
    TPaper extends { title?: string; arxiv_id: string },
>(query: string, deps: SubmitAddPaperDeps<TPaper>): Promise<boolean> {
    if (!query.trim()) return false;
    try {
        const paper = await deps.addPaperFn(query);
        deps.onResetQuery();
        deps.onSuccessToast(`Added "${paper.title || paper.arxiv_id}"`);
        deps.onSuccess?.();
        deps.onNavigate(`/paper/${paper.arxiv_id}`);
        return true;
    } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to add paper";
        deps.onErrorToast(message);
        return false;
    }
}
