import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
    CORE_NAV_ROUTES,
    ALL_NAV_ROUTES,
    CHORD_MAP,
    SHORTCUT_DEFINITIONS,
    OPEN_ADD_PAPER_EVENT,
    isRouteActive,
    normalizePathname,
    buildResearchRedirectUrl,
    parseDashboardSearchParams,
    serializeDashboardSearchParams,
    hasActiveDashboardFilters,
    shouldCacheDashboardPapers,
    resolveKeyboardNavAction,
} from "../lib/navigation.ts";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_ROOT = path.resolve(__dirname, "..");

function readFrontendFile(relPath: string): string {
    return fs.readFileSync(path.join(FRONTEND_ROOT, relPath), "utf8");
}

describe("Unified Navigation Routes & Active Highlighting", () => {
    it("defines all 7 core routes in the canonical order plus Settings", () => {
        assert.deepEqual(
            CORE_NAV_ROUTES.map((r) => ({ name: r.name, href: r.href })),
            [
                { name: "Queue", href: "/queue" },
                { name: "Archive", href: "/dashboard" },
                { name: "Library", href: "/bookmarks" },
                { name: "Chat", href: "/chat" },
                { name: "Patterns", href: "/patterns" },
                { name: "Timeline", href: "/timeline" },
                { name: "Analysis", href: "/analysis" },
            ],
        );

        assert.equal(ALL_NAV_ROUTES.length, 8);
        assert.deepEqual(ALL_NAV_ROUTES[7], {
            name: "Settings",
            href: "/settings",
            activeOn: ["/settings"],
        });
    });

    it("highlights Queue on both / and /queue (including trailing slash)", () => {
        const queueRoute = CORE_NAV_ROUTES[0];
        assert.equal(queueRoute.name, "Queue");
        assert.equal(queueRoute.showBadge, true);
        assert.equal(isRouteActive("/", queueRoute.activeOn), true);
        assert.equal(isRouteActive("/queue", queueRoute.activeOn), true);
        assert.equal(isRouteActive("/queue/", queueRoute.activeOn), true);
        assert.equal(isRouteActive("/dashboard", queueRoute.activeOn), false);
    });

    it("highlights Archive on both /dashboard and /research (including trailing slash)", () => {
        const archiveRoute = CORE_NAV_ROUTES[1];
        assert.equal(archiveRoute.name, "Archive");
        assert.equal(isRouteActive("/dashboard", archiveRoute.activeOn), true);
        assert.equal(isRouteActive("/dashboard/", archiveRoute.activeOn), true);
        assert.equal(isRouteActive("/research", archiveRoute.activeOn), true);
        assert.equal(isRouteActive("/research/", archiveRoute.activeOn), true);
        assert.equal(isRouteActive("/bookmarks", archiveRoute.activeOn), false);
    });

    it("normalizes trailing slashes consistently", () => {
        assert.equal(normalizePathname("/"), "/");
        assert.equal(normalizePathname(""), "/");
        assert.equal(normalizePathname("/timeline/"), "/timeline");
        assert.equal(normalizePathname("/timeline"), "/timeline");
    });
});

describe("Global Keyboard Chords & Shortcut Definitions", () => {
    it("maps all required g+<key> chords to unified routes", () => {
        assert.deepEqual(CHORD_MAP, {
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
        });
    });

    it("lists unified route chords including G Q and G T in ShortcutOverlay definitions", () => {
        const chordTextMap = new Map(
            SHORTCUT_DEFINITIONS.map((item) => [item.keys.join("+"), item.description]),
        );
        assert.equal(chordTextMap.get("G+Q"), "Go to Queue");
        assert.equal(chordTextMap.get("G+D"), "Go to Archive");
        assert.equal(chordTextMap.get("G+R"), "Go to Archive");
        assert.equal(chordTextMap.get("G+L"), "Go to Library");
        assert.equal(chordTextMap.get("G+B"), "Go to Library");
        assert.equal(chordTextMap.get("G+C"), "Go to Chat");
        assert.equal(chordTextMap.get("G+P"), "Go to Patterns");
        assert.equal(chordTextMap.get("G+T"), "Go to Timeline");
        assert.equal(chordTextMap.get("G+A"), "Go to Analysis");
        assert.equal(chordTextMap.get("G+S"), "Go to Settings");
        assert.equal(chordTextMap.get("?"), "Toggle shortcuts");
    });

    it("resolves global g+<key> chords and ? in AppShell mode without hijacking Space scrolling", () => {
        const appShellState = {
            chordPending: false,
            focusedIndex: -1,
            itemCount: 0,
            isInputFocused: false,
            enableChords: true,
            enableOverlayShortcut: true,
            hasPeek: false,
            hasBookmark: false,
        };

        assert.deepEqual(
            resolveKeyboardNavAction({ key: "g" }, appShellState),
            { type: "start-chord" },
        );

        for (const [key, href] of Object.entries(CHORD_MAP)) {
            assert.deepEqual(
                resolveKeyboardNavAction({ key }, { ...appShellState, chordPending: true }),
                {
                    type: "navigate",
                    href,
                    preventDefault: true,
                    clearChord: true,
                },
            );
        }

        assert.deepEqual(
            resolveKeyboardNavAction({ key: "?" }, appShellState),
            { type: "toggle-shortcuts", preventDefault: true },
        );

        // Space in AppShell (itemCount: 0) must not preventDefault so page scrolling works
        assert.deepEqual(
            resolveKeyboardNavAction({ key: " " }, appShellState),
            { type: "none" },
        );
    });

    it("resolves j/k/Space/b in DashboardContent item mode without duplicating chords or ? overlay", () => {
        const itemState = {
            chordPending: false,
            focusedIndex: 0,
            itemCount: 5,
            isInputFocused: false,
            enableChords: false,
            enableOverlayShortcut: false,
            hasPeek: true,
            hasBookmark: true,
        };

        assert.deepEqual(
            resolveKeyboardNavAction({ key: "j" }, itemState),
            { type: "focus", nextIndex: 1, preventDefault: true },
        );
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "k" }, { ...itemState, focusedIndex: 2 }),
            { type: "focus", nextIndex: 1, preventDefault: true },
        );
        assert.deepEqual(
            resolveKeyboardNavAction({ key: " " }, itemState),
            { type: "peek", index: 0, nextFocusedIndex: 0, preventDefault: true },
        );
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "b" }, itemState),
            { type: "bookmark", index: 0, preventDefault: true },
        );
        // g+b in DashboardContent must consume the chord and NOT fire bookmark
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "b" }, { ...itemState, chordPending: true }),
            { type: "none", clearChord: true },
        );
        // ? in DashboardContent must not toggle a second overlay
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "?" }, itemState),
            { type: "none" },
        );
        // Focused input ignores shortcuts
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "j" }, { ...itemState, isInputFocused: true }),
            { type: "none" },
        );
    });
});

describe("/research Redirect to /dashboard", () => {
    it("redirects bare /research to /dashboard", () => {
        assert.equal(buildResearchRedirectUrl(), "/dashboard");
        assert.equal(buildResearchRedirectUrl(undefined), "/dashboard");
        assert.equal(buildResearchRedirectUrl({}), "/dashboard");
        assert.equal(buildResearchRedirectUrl(""), "/dashboard");
    });

    it("preserves query parameters when redirecting /research to /dashboard", () => {
        assert.equal(
            buildResearchRedirectUrl({ q: "transformers" }),
            "/dashboard?q=transformers",
        );
        assert.equal(
            buildResearchRedirectUrl(new URLSearchParams("q=multi+agent&sort=newest")),
            "/dashboard?q=multi+agent&sort=newest",
        );
        assert.equal(
            buildResearchRedirectUrl({
                q: "attention",
                category: "cs.AI,cs.CL",
                start: "2026-01-01",
            }),
            "/dashboard?q=attention&category=cs.AI%2Ccs.CL&start=2026-01-01",
        );
    });
});

describe("Dashboard URL Filter Parsing & sessionStorage Cache Guard", () => {
    it("initializes filter state directly from URLSearchParams", () => {
        const params = new URLSearchParams(
            "q=transformers&category=cs.AI,cs.CL&start=2026-01-01&end=2026-02-01&sort=newest",
        );
        const parsed = parseDashboardSearchParams(params);
        assert.deepEqual(parsed, {
            selectedCategories: ["cs.AI", "cs.CL"],
            dateStart: "2026-01-01",
            dateEnd: "2026-02-01",
            searchQuery: "transformers",
            sortBy: "newest",
        });
        assert.equal(hasActiveDashboardFilters(parsed), true);
        assert.equal(shouldCacheDashboardPapers(parsed), false);
    });

    it("allows sessionStorage caching only when no query or filter is active", () => {
        const empty = parseDashboardSearchParams(new URLSearchParams());
        assert.deepEqual(empty, {
            selectedCategories: [],
            dateStart: null,
            dateEnd: null,
            searchQuery: "",
            sortBy: "relevance",
        });
        assert.equal(hasActiveDashboardFilters(empty), false);
        assert.equal(shouldCacheDashboardPapers(empty), true);
        assert.equal(serializeDashboardSearchParams(empty), "");

        assert.equal(
            shouldCacheDashboardPapers({ ...empty, searchQuery: "diffusion" }),
            false,
        );
        assert.equal(
            shouldCacheDashboardPapers({ ...empty, selectedCategories: ["cs.LG"] }),
            false,
        );
        assert.equal(
            shouldCacheDashboardPapers({ ...empty, dateStart: "2026-01-01" }),
            false,
        );
        assert.equal(
            shouldCacheDashboardPapers({ ...empty, sortBy: "newest" }),
            false,
        );
    });
});

describe("Component Structural Contracts", () => {
    it("SidebarRail exposes all 7 core routes, removes Collections, and delegates ShortcutOverlay", () => {
        const src = readFrontendFile("components/SidebarRail.tsx");
        for (const route of CORE_NAV_ROUTES) {
            assert.match(src, new RegExp(`name:\\s*['"]${route.name}['"]`));
            assert.match(src, new RegExp(`href:\\s*['"]${route.href}['"]`));
        }
        assert.doesNotMatch(src, /Collections/);
        assert.doesNotMatch(src, /<ShortcutOverlay/);
    });

    it("TopBar removes STATUS_TABS, Bell, UserCircle, ThemeToggle and provides + Add Paper", () => {
        const src = readFrontendFile("components/TopBar.tsx");
        assert.doesNotMatch(src, /STATUS_TABS/);
        assert.doesNotMatch(src, /Bell/);
        assert.doesNotMatch(src, /UserCircle/);
        assert.doesNotMatch(src, /ThemeToggle/);
        assert.match(src, /\+ Add Paper/);
    });

    it("HamburgerDrawer exposes unified routes and removes fake User / Pro Plan footer", () => {
        const src = readFrontendFile("components/HamburgerDrawer.tsx");
        for (const route of ALL_NAV_ROUTES) {
            assert.match(src, new RegExp(`name:\\s*['"]${route.name}['"]`));
            assert.match(src, new RegExp(`href:\\s*['"]${route.href}['"]`));
        }
        assert.doesNotMatch(src, /Pro Plan/);
        assert.doesNotMatch(src, /Discover/);
        assert.doesNotMatch(src, /Deep Dive/);
    });

    it("AppShell hosts single ShortcutOverlay, global useKeyboardNav, and AddPaperForm modal", () => {
        const src = readFrontendFile("components/AppShell.tsx");
        assert.match(src, /useKeyboardNav/);
        assert.match(src, /<ShortcutOverlay/);
        assert.match(src, /<AddPaperForm\s+onSuccess=/);
        assert.match(src, /OPEN_ADD_PAPER_EVENT/);
        assert.equal(OPEN_ADD_PAPER_EVENT, "open-add-paper");
    });

    it("DashboardContent initializes from searchParams, guards sessionStorage cache, and disables duplicate chord/overlay listeners", () => {
        const src = readFrontendFile("components/DashboardContent.tsx");
        assert.match(src, /parseDashboardSearchParams\(searchParams\)/);
        assert.match(src, /shouldCacheDashboardPapers/);
        assert.match(src, /enableChords:\s*false/);
        assert.match(src, /enableOverlayShortcut:\s*false/);
        assert.doesNotMatch(src, /<ShortcutOverlay/);
    });

    it("CommandPalette lists all 8 unified pages and dispatches OPEN_ADD_PAPER_EVENT", () => {
        const src = readFrontendFile("components/CommandPalette.tsx");
        for (const route of ALL_NAV_ROUTES) {
            assert.match(src, new RegExp(`name:\\s*["']${route.name}["']`));
            assert.match(src, new RegExp(`href:\\s*["']${route.href}["']`));
        }
        assert.match(src, /OPEN_ADD_PAPER_EVENT/);
        assert.doesNotMatch(src, /document\.querySelector/);
    });

    it("AddPaperForm supports optional onSuccess callback", () => {
        const src = readFrontendFile("components/AddPaperForm.tsx");
        assert.match(src, /onSuccess\?:\s*\(\)\s*=>\s*void/);
        assert.match(src, /onSuccess\?\.\(\)/);
    });
});
