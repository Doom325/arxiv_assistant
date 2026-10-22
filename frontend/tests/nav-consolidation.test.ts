/**
 * Navigation & Page Consolidation Test Suite (`feat/nav-page-consolidation`)
 *
 * Omission Ledger (L-SE-W103 / Quality Rule 20):
 * - Interactive browser DOM mounting (React component tree rendering in jsdom/Playwright,
 *   Framer Motion portal animations, focus-trap tab cycling, and cmdk keyboard filtering)
 *   is omitted from this `node --test` unit lane because `frontend/package.json` intentionally
 *   ships zero DOM test libraries (`@testing-library/react`, `jsdom`, `playwright` are absent)
 *   to keep the unit runner dependency-free (`node --test tests/*.test.ts`, ~70ms).
 * - Compensation: All stateful decision logic (`parseDashboardSearchParams`,
 *   `serializeDashboardSearchParams`, `shouldUseDashboardSearchApi`, `writeDashboardCacheIfEligible`,
 *   `resolveKeyboardNavAction`, `executeResearchRedirect`, `triggerOpenAddPaper`,
 *   `submitAddPaperRequest`) is extracted into pure, dependency-injected functions in
 *   `lib/navigation.ts` and verified behaviorally alongside structural wiring checks on
 *   the thin React component seams.
 * - Repayment Trigger: When a browser E2E or DOM integration runner (Playwright or Vitest +
 *   Testing Library) is added to `frontend/package.json` or when a second modal/drawer workflow
 *   is introduced in `AppShell`.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
    CORE_NAV_ROUTES,
    ALL_NAV_ROUTES,
    SETTINGS_NAV_ROUTE,
    CHORD_MAP,
    SHORTCUT_DEFINITIONS,
    OPEN_ADD_PAPER_EVENT,
    isRouteActive,
    normalizePathname,
    buildResearchRedirectUrl,
    executeResearchRedirect,
    parseDashboardSearchParams,
    serializeDashboardSearchParams,
    shouldUseDashboardSearchApi,
    hasActiveDashboardFilters,
    shouldCacheDashboardPapers,
    writeDashboardCacheIfEligible,
    resolveKeyboardNavAction,
    triggerOpenAddPaper,
    submitAddPaperRequest,
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
        assert.deepEqual(ALL_NAV_ROUTES[7], SETTINGS_NAV_ROUTE);
        assert.deepEqual(SETTINGS_NAV_ROUTE, {
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

    it("resolves global g+<key> chords, Shift+key chords, Escape, and ? in AppShell mode without hijacking Space scrolling", () => {
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

        // Pressing Shift while chordPending is true must NOT clear the pending chord,
        // and subsequent uppercase chord keys (e.g. G then Shift+Q) must navigate.
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "Shift" }, { ...appShellState, chordPending: true }),
            { type: "none" },
        );
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "Q" }, { ...appShellState, chordPending: true }),
            {
                type: "navigate",
                href: "/queue",
                preventDefault: true,
                clearChord: true,
            },
        );

        assert.deepEqual(
            resolveKeyboardNavAction({ key: "?" }, appShellState),
            { type: "toggle-shortcuts", preventDefault: true },
        );

        // Escape in AppShell mode closes the shortcut overlay (closeShortcuts: true)
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "Escape" }, appShellState),
            { type: "escape", closeShortcuts: true },
        );

        // Space in AppShell (itemCount: 0) must not preventDefault so page scrolling works
        assert.deepEqual(
            resolveKeyboardNavAction({ key: " " }, appShellState),
            { type: "none" },
        );
    });

    it("resolves j/k/Space/b/Escape in DashboardContent item mode and handles g-prefixed sequences cleanly", () => {
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
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "Escape" }, itemState),
            { type: "escape", closeShortcuts: false },
        );

        // Two-step g -> b in DashboardContent item mode must consume the chord and NOT fire bookmark
        const afterG = resolveKeyboardNavAction({ key: "g" }, itemState);
        assert.deepEqual(afterG, { type: "start-chord" });
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "b" }, { ...itemState, chordPending: true }),
            { type: "none", clearChord: true },
        );

        // Two-step g -> j/k/Space/Escape in item mode must clear the pending chord AND execute the item shortcut
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "j" }, { ...itemState, chordPending: true }),
            { type: "focus", nextIndex: 1, preventDefault: true, clearChord: true },
        );
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "k" }, { ...itemState, focusedIndex: 2, chordPending: true }),
            { type: "focus", nextIndex: 1, preventDefault: true, clearChord: true },
        );
        assert.deepEqual(
            resolveKeyboardNavAction({ key: " " }, { ...itemState, chordPending: true }),
            { type: "peek", index: 0, nextFocusedIndex: 0, preventDefault: true, clearChord: true },
        );
        assert.deepEqual(
            resolveKeyboardNavAction({ key: "Escape" }, { ...itemState, chordPending: true }),
            { type: "escape", closeShortcuts: false, clearChord: true },
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
        assert.equal(buildResearchRedirectUrl("?"), "/dashboard");
    });

    it("preserves string, URLSearchParams, and multi-value array query parameters when redirecting /research to /dashboard", () => {
        assert.equal(
            buildResearchRedirectUrl({ q: "transformers" }),
            "/dashboard?q=transformers",
        );
        assert.equal(
            buildResearchRedirectUrl("?q=transformers&sort=newest"),
            "/dashboard?q=transformers&sort=newest",
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
        assert.equal(
            buildResearchRedirectUrl({
                category: ["cs.AI", "cs.LG"],
                q: "graph",
            }),
            "/dashboard?category=cs.AI&category=cs.LG&q=graph",
        );
    });

    it("executes Next.js server redirect with resolved async searchParams", async () => {
        const redirectedUrls: string[] = [];
        const fakeRedirect = (url: string): never => {
            redirectedUrls.push(url);
            throw new Error(`REDIRECT:${url}`);
        };

        await assert.rejects(
            () => executeResearchRedirect(Promise.resolve({ q: "transformers", category: ["cs.AI", "cs.LG"] }), fakeRedirect),
            /REDIRECT:\/dashboard\?q=transformers&category=cs\.AI&category=cs\.LG/,
        );
        await assert.rejects(
            () => executeResearchRedirect(undefined, fakeRedirect),
            /REDIRECT:\/dashboard$/,
        );
        assert.deepEqual(redirectedUrls, [
            "/dashboard?q=transformers&category=cs.AI&category=cs.LG",
            "/dashboard",
        ]);
    });
});

describe("Dashboard URL Filter Parsing, Serialization & sessionStorage Cache Guard", () => {
    it("initializes filter state directly from URLSearchParams and round-trips via serializeDashboardSearchParams", () => {
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
        assert.equal(shouldUseDashboardSearchApi(parsed.searchQuery), true);
        assert.equal(hasActiveDashboardFilters(parsed), true);
        assert.equal(shouldCacheDashboardPapers(parsed), false);

        const serialized = serializeDashboardSearchParams(parsed);
        assert.equal(
            serialized,
            "category=cs.AI%2Ccs.CL&start=2026-01-01&end=2026-02-01&q=transformers&sort=newest",
        );
        assert.deepEqual(
            parseDashboardSearchParams(new URLSearchParams(serialized)),
            parsed,
        );
    });

    it("treats whitespace-only searchQuery consistently across search API branching, serialization, and caching", () => {
        assert.equal(shouldUseDashboardSearchApi(""), false);
        assert.equal(shouldUseDashboardSearchApi("   "), false);
        assert.equal(shouldUseDashboardSearchApi("  rag  "), true);

        const whitespaceState = {
            selectedCategories: [],
            dateStart: null,
            dateEnd: null,
            searchQuery: "   ",
            sortBy: "relevance",
        };
        assert.equal(hasActiveDashboardFilters(whitespaceState), false);
        assert.equal(shouldCacheDashboardPapers(whitespaceState), true);
        assert.equal(serializeDashboardSearchParams(whitespaceState), "");
    });

    it("writes to sessionStorage via writeDashboardCacheIfEligible only when no query or filter is active", () => {
        const empty = parseDashboardSearchParams(new URLSearchParams());
        assert.equal(hasActiveDashboardFilters(empty), false);
        assert.equal(shouldCacheDashboardPapers(empty), true);
        assert.equal(serializeDashboardSearchParams(empty), "");

        const store = new Map<string, string>();
        const fakeStorage = {
            setItem(key: string, value: string) {
                store.set(key, value);
            },
        };

        // Filtered states must NOT write to storage
        assert.equal(
            writeDashboardCacheIfEligible(
                fakeStorage,
                { ...empty, searchQuery: "diffusion" },
                [{ id: 1 }],
                0,
                true,
                1700000000000,
            ),
            false,
        );
        assert.equal(store.size, 0);

        assert.equal(
            writeDashboardCacheIfEligible(
                fakeStorage,
                { ...empty, selectedCategories: ["cs.LG"] },
                [{ id: 1 }],
                0,
                true,
                1700000000000,
            ),
            false,
        );
        assert.equal(store.size, 0);

        assert.equal(
            writeDashboardCacheIfEligible(
                fakeStorage,
                { ...empty, dateStart: "2026-01-01" },
                [{ id: 1 }],
                0,
                true,
                1700000000000,
            ),
            false,
        );
        assert.equal(store.size, 0);

        assert.equal(
            writeDashboardCacheIfEligible(
                fakeStorage,
                { ...empty, sortBy: "newest" },
                [{ id: 1 }],
                0,
                true,
                1700000000000,
            ),
            false,
        );
        assert.equal(store.size, 0);

        // Unfiltered state writes all 4 cache keys
        assert.equal(
            writeDashboardCacheIfEligible(
                fakeStorage,
                empty,
                [{ id: 42 }],
                1,
                false,
                1700000000000,
            ),
            true,
        );
        assert.equal(store.get("dashboard_papers"), JSON.stringify([{ id: 42 }]));
        assert.equal(store.get("dashboard_page"), "1");
        assert.equal(store.get("dashboard_has_more"), "false");
        assert.equal(store.get("dashboard_cached_at"), "1700000000000");
    });
});

describe("AddPaperForm Submission & TopBar Trigger Helpers", () => {
    it("submitAddPaperRequest invokes onSuccess only on resolved submission and never on error", async () => {
        const events: string[] = [];

        // Empty/whitespace query is a no-op
        const emptyResult = await submitAddPaperRequest("   ", {
            addPaperFn: async () => {
                events.push("api");
                return { arxiv_id: "2501.00001", title: "Test" };
            },
            onResetQuery: () => events.push("reset"),
            onSuccessToast: (m) => events.push(`toast:${m}`),
            onErrorToast: (m) => events.push(`error:${m}`),
            onSuccess: () => events.push("onSuccess"),
            onNavigate: (href) => events.push(`nav:${href}`),
        });
        assert.equal(emptyResult, false);
        assert.deepEqual(events, []);

        // Successful submission calls onSuccess and navigates
        const okResult = await submitAddPaperRequest("2501.00001", {
            addPaperFn: async (q) => {
                events.push(`api:${q}`);
                return { arxiv_id: "2501.00001", title: "Attention Paper" };
            },
            onResetQuery: () => events.push("reset"),
            onSuccessToast: (m) => events.push(`toast:${m}`),
            onErrorToast: (m) => events.push(`error:${m}`),
            onSuccess: () => events.push("onSuccess"),
            onNavigate: (href) => events.push(`nav:${href}`),
        });
        assert.equal(okResult, true);
        assert.deepEqual(events, [
            "api:2501.00001",
            "reset",
            'toast:Added "Attention Paper"',
            "onSuccess",
            "nav:/paper/2501.00001",
        ]);

        // Rejected submission shows error toast and NEVER calls onSuccess or onNavigate
        events.length = 0;
        const failResult = await submitAddPaperRequest("invalid-id", {
            addPaperFn: async () => {
                throw new Error("Invalid arXiv ID");
            },
            onResetQuery: () => events.push("reset"),
            onSuccessToast: (m) => events.push(`toast:${m}`),
            onErrorToast: (m) => events.push(`error:${m}`),
            onSuccess: () => events.push("onSuccess"),
            onNavigate: (href) => events.push(`nav:${href}`),
        });
        assert.equal(failResult, false);
        assert.deepEqual(events, ["error:Invalid arXiv ID"]);
    });

    it("triggerOpenAddPaper invokes callback when provided or dispatches OPEN_ADD_PAPER_EVENT", () => {
        let callbackCount = 0;
        const dispatched: string[] = [];
        const fakeTarget = {
            dispatchEvent(event: Event) {
                dispatched.push(event.type);
                return true;
            },
        };

        triggerOpenAddPaper(() => {
            callbackCount += 1;
        }, fakeTarget);
        assert.equal(callbackCount, 1);
        assert.deepEqual(dispatched, []);

        triggerOpenAddPaper(undefined, fakeTarget);
        assert.equal(callbackCount, 1);
        assert.deepEqual(dispatched, [OPEN_ADD_PAPER_EVENT]);
    });
});

describe("Component Structural Contracts & Single-Source Wiring", () => {
    it("SidebarRail, HamburgerDrawer, and CommandPalette derive routes from CORE_NAV_ROUTES / ALL_NAV_ROUTES", () => {
        const sidebarSrc = readFrontendFile("components/SidebarRail.tsx");
        assert.match(sidebarSrc, /CORE_NAV_ROUTES\.map/);
        assert.doesNotMatch(sidebarSrc, /Collections/);
        assert.doesNotMatch(sidebarSrc, /<ShortcutOverlay/);

        const drawerSrc = readFrontendFile("components/HamburgerDrawer.tsx");
        assert.match(drawerSrc, /ALL_NAV_ROUTES\.map/);
        assert.doesNotMatch(drawerSrc, /Pro Plan/);
        assert.doesNotMatch(drawerSrc, /Discover/);
        assert.doesNotMatch(drawerSrc, /Deep Dive/);

        const paletteSrc = readFrontendFile("components/CommandPalette.tsx");
        assert.match(paletteSrc, /ALL_NAV_ROUTES\.map/);
        assert.match(paletteSrc, /triggerOpenAddPaper\(\)/);
        assert.doesNotMatch(paletteSrc, /document\.querySelector/);

        // Every canonical route name has an explicit icon entry in all three components
        for (const route of CORE_NAV_ROUTES) {
            assert.match(sidebarSrc, new RegExp(`\\b${route.name}:\\s*\\w+`));
        }
        for (const route of ALL_NAV_ROUTES) {
            assert.match(drawerSrc, new RegExp(`\\b${route.name}:\\s*\\w+`));
            assert.match(paletteSrc, new RegExp(`\\b${route.name}:\\s*\\w+`));
        }
    });

    it("app/research/page.tsx delegates directly to executeResearchRedirect", () => {
        const researchPageSrc = readFrontendFile("app/research/page.tsx");
        assert.match(researchPageSrc, /executeResearchRedirect\(searchParams,\s*redirect\)/);
    });

    it("useKeyboardNav.ts wires router.push(action.href) and action.closeShortcuts", () => {
        const hookSrc = readFrontendFile("lib/useKeyboardNav.ts");
        assert.match(hookSrc, /case\s+['"]navigate['"]:[\s\S]*?router\.push\(action\.href\)/);
        assert.match(hookSrc, /case\s+['"]escape['"]:[\s\S]*?if\s*\(action\.closeShortcuts\)\s*\{?\s*setShowShortcuts\(false\)/);
    });

    it("TopBar removes STATUS_TABS, Bell, UserCircle, ThemeToggle and wires triggerOpenAddPaper", () => {
        const src = readFrontendFile("components/TopBar.tsx");
        assert.doesNotMatch(src, /STATUS_TABS/);
        assert.doesNotMatch(src, /Bell/);
        assert.doesNotMatch(src, /UserCircle/);
        assert.doesNotMatch(src, /ThemeToggle/);
        assert.match(src, /\+ Add Paper/);
        assert.match(src, /triggerOpenAddPaper\(onAddPaperOpen\)/);
    });

    it("AppShell hosts single ShortcutOverlay, global useKeyboardNav, and AddPaperForm modal", () => {
        const src = readFrontendFile("components/AppShell.tsx");
        assert.match(src, /useKeyboardNav\(\{/);
        assert.match(src, /<ShortcutOverlay/);
        assert.match(src, /<AddPaperForm\s+onSuccess=/);
        assert.match(src, /OPEN_ADD_PAPER_EVENT/);
        assert.equal(OPEN_ADD_PAPER_EVENT, "open-add-paper");
    });

    it("DashboardContent initializes state from initialFilters, branches on shouldUseDashboardSearchApi, and caches via writeDashboardCacheIfEligible", () => {
        const src = readFrontendFile("components/DashboardContent.tsx");
        assert.match(src, /const initialFilters = parseDashboardSearchParams\(searchParams\)/);
        assert.match(src, /useState<string\[\]>\(\s*initialFilters\.selectedCategories\s*,?\s*\)/);
        assert.match(src, /useState<string \| null>\(\s*initialFilters\.dateStart\s*,?\s*\)/);
        assert.match(src, /useState<string \| null>\(\s*initialFilters\.dateEnd\s*,?\s*\)/);
        assert.match(src, /useState<string>\(\s*initialFilters\.searchQuery\s*,?\s*\)/);
        assert.match(src, /useState<string>\(\s*initialFilters\.sortBy\s*,?\s*\)/);
        assert.match(src, /shouldUseDashboardSearchApi\(searchQuery\)\s*\?\s*await api\.searchPapers/);
        assert.match(
            src,
            /writeDashboardCacheIfEligible\(\s*sessionStorage,\s*\{\s*selectedCategories,\s*dateStart,\s*dateEnd,\s*searchQuery,\s*sortBy\s*\}/,
        );
        assert.doesNotMatch(src, /sessionStorage\.setItem\(['"]dashboard_papers['"]/);
        assert.match(src, /enableChords:\s*false/);
        assert.match(src, /enableOverlayShortcut:\s*false/);
        assert.doesNotMatch(src, /<ShortcutOverlay/);
    });

    it("AddPaperForm delegates submission to submitAddPaperRequest with onSuccess", () => {
        const src = readFrontendFile("components/AddPaperForm.tsx");
        assert.match(src, /onSuccess\?:\s*\(\)\s*=>\s*void/);
        assert.match(src, /submitAddPaperRequest\(query,\s*\{[\s\S]*?onSuccess,/);
    });
});
