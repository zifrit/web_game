"use client";

import { useEffect } from "react";

const APP_SCROLL_ROOT_SELECTOR = "[data-app-scroll-root]";

let lockCount = 0;
let previousBodyOverflow = "";
let previousBodyOverscrollBehavior = "";
let previousRootOverflowY: string | null = null;
let previousRootOverscrollBehavior: string | null = null;

function appScrollRoot() {
  return document.querySelector<HTMLElement>(APP_SCROLL_ROOT_SELECTOR);
}

function lockScroll() {
  if (lockCount === 0) {
    const root = appScrollRoot();

    previousBodyOverflow = document.body.style.overflow;
    previousBodyOverscrollBehavior = document.body.style.overscrollBehavior;
    previousRootOverflowY = root?.style.overflowY ?? null;
    previousRootOverscrollBehavior = root?.style.overscrollBehavior ?? null;

    document.body.style.overflow = "hidden";
    document.body.style.overscrollBehavior = "none";

    if (root) {
      root.style.overflowY = "hidden";
      root.style.overscrollBehavior = "none";
    }
  }

  lockCount += 1;
}

function unlockScroll() {
  lockCount = Math.max(0, lockCount - 1);

  if (lockCount === 0) {
    const root = appScrollRoot();

    document.body.style.overflow = previousBodyOverflow;
    document.body.style.overscrollBehavior = previousBodyOverscrollBehavior;

    if (root && previousRootOverflowY !== null) {
      root.style.overflowY = previousRootOverflowY;
      root.style.overscrollBehavior = previousRootOverscrollBehavior ?? "";
    }

    previousRootOverflowY = null;
    previousRootOverscrollBehavior = null;
  }
}

export function useModalScrollLock() {
  useEffect(() => {
    lockScroll();
    return unlockScroll;
  }, []);
}
