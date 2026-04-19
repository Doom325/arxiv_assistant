"use client";

import { useEffect } from "react";

/**
 * Registers `/sw.js` once on app load.
 *
 * The Service Worker is notification-only (see `public/sw.js`) and is
 * required on Android Chrome, which does not support the foreground
 * `Notification` constructor.
 *
 * Renders nothing. Registration errors are logged but swallowed so that
 * an unsupported browser (e.g. iOS Safari in private mode) never crashes
 * the app at render time.
 */
export function ServiceWorkerRegister(): null {
    useEffect(() => {
        if (typeof window === "undefined") return;
        if (!("serviceWorker" in navigator)) return;

        navigator.serviceWorker
            .register("/sw.js")
            .catch((err) => {
                console.warn("Service Worker registration failed:", err);
            });
    }, []);

    return null;
}
