"use client";

import { useSyncExternalStore } from "react";

const WIDE_VIEWPORT_QUERY = "(min-width: 1024px)";

function subscribe(onChange: () => void): () => void {
  const mediaQuery = window.matchMedia(WIDE_VIEWPORT_QUERY);
  mediaQuery.addEventListener("change", onChange);
  return () => mediaQuery.removeEventListener("change", onChange);
}

function getSnapshot(): boolean {
  return window.matchMedia(WIDE_VIEWPORT_QUERY).matches;
}

function getServerSnapshot(): boolean {
  return false;
}

/** True when the viewport matches Tailwind's `lg` breakpoint (>= 1024px). */
export function useIsWideViewport(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
