/**
 * Minimal Service Worker for summary-complete notifications.
 *
 * Scope: notifications only. No caching, no offline strategy.
 *
 * Required on Android Chrome because `new Notification(...)` throws
 * `TypeError: Failed to construct 'Notification'` on mobile Chrome;
 * notifications must be delivered via `ServiceWorkerRegistration.showNotification`.
 */

self.addEventListener("install", () => {
  // Activate the new worker immediately instead of waiting for existing tabs.
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  // Take control of uncontrolled clients (existing tabs) without reload.
  event.waitUntil(self.clients.claim());
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const targetUrl = (event.notification.data && event.notification.data.url) || "/";

  event.waitUntil(
    (async () => {
      const allClients = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      });

      // Focus an existing tab already on the target URL if any.
      for (const client of allClients) {
        try {
          const clientUrl = new URL(client.url);
          const target = new URL(targetUrl, self.location.origin);
          if (clientUrl.pathname === target.pathname && "focus" in client) {
            return client.focus();
          }
        } catch {
          // Ignore malformed URLs and continue.
        }
      }

      // Otherwise open a new tab.
      if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
      }
      return null;
    })()
  );
});
