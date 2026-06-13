"use client";

import { useEffect, useState } from "react";

/**
 * SSR-safe media-query hook. Returns true when the viewport is below the given
 * breakpoint (default 1024px, i.e. Tailwind's `lg`). Used to branch between the
 * desktop layout and the ported mobile layout from `mobile/`.
 *
 * Initialises to `false` on the server / first paint to avoid hydration
 * mismatches, then resolves to the real value on mount.
 */
export function useIsMobile(maxWidth = 1023): boolean {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mql = window.matchMedia(`(max-width: ${maxWidth}px)`);
    const update = () => setIsMobile(mql.matches);
    update();
    mql.addEventListener("change", update);
    return () => mql.removeEventListener("change", update);
  }, [maxWidth]);

  return isMobile;
}
