/**
 * Notification helpers for summary-complete signaling.
 *
 * Primary delivery path is `ServiceWorkerRegistration.showNotification`
 * because Android Chrome does not support the foreground `Notification`
 * constructor (throws `TypeError: Failed to construct 'Notification'`).
 *
 * All functions are SSR-safe and fail silently on unsupported browsers
 * (notably iOS Safari), so callers do not need to feature-detect.
 */

type PaperIdLike = number | string;

/**
 * Show a "Summarization Complete" notification for the given paper.
 *
 * Feature-detects in this order:
 *   1. Service Worker with granted permission → `showNotification` (works on Android Chrome).
 *   2. Foreground `Notification` constructor  → desktop fallback.
 *   3. Otherwise swallow silently (e.g. iOS Safari, permission not granted).
 */
export async function showSummaryCompleteNotification(
    title: string,
    paperId: PaperIdLike,
): Promise<void> {
    if (typeof window === "undefined") return;
    if (!("Notification" in window) || Notification.permission !== "granted") return;

    const body = `The summary for "${title}" is ready.`;
    const tag = `summary-${paperId}`;
    const data = { url: `/paper/${paperId}` };

    // Try the Service Worker path first (required on Android Chrome).
    if ("serviceWorker" in navigator) {
        try {
            // `navigator.serviceWorker.ready` only resolves once a Service
            // Worker is controlling the page. If registration silently failed
            // (insecure origin, 404 on /sw.js, browser policy), it never
            // resolves. Race with a short timeout so we fall back to the
            // desktop constructor instead of hanging forever.
            const READY_TIMEOUT_MS = 3000;
            const registration = await Promise.race([
                navigator.serviceWorker.ready,
                new Promise<never>((_, reject) =>
                    setTimeout(
                        () => reject(new Error("serviceWorker.ready timeout")),
                        READY_TIMEOUT_MS,
                    ),
                ),
            ]);
            await registration.showNotification("Summarization Complete", {
                body,
                tag,
                data,
            });
            return;
        } catch (err) {
            console.warn("Service Worker notification failed, falling back:", err);
            // fall through to desktop constructor
        }
    }

    // Desktop fallback if Service Worker is unavailable or failed.
    try {
        new Notification("Summarization Complete", { body, tag });
    } catch (err) {
        console.warn("Notification failed:", err);
    }
}

/**
 * Request Notification permission if supported and not already decided.
 * Safe to call unconditionally; returns early on unsupported browsers.
 */
export function requestNotificationPermission(): void {
    if (typeof window === "undefined") return;
    if (!("Notification" in window)) return;
    if (Notification.permission === "granted" || Notification.permission === "denied") return;

    // Fire-and-forget; the browser decides when to show the prompt.
    void Notification.requestPermission().catch((err) => {
        console.warn("Notification permission request failed:", err);
    });
}
