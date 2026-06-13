"use client";

import { useEffect, useRef } from "react";
import type { PointerEventHandler } from "react";

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

export function useSwipeToClose(onClose: () => void) {
  const startXRef = useRef(0);
  const startYRef = useRef(0);
  const trackingRef = useRef(false);
  const closedRef = useRef(false);

  const closeIfSwipe = (clientX: number, clientY: number) => {
    if (!trackingRef.current || closedRef.current) return;

    const deltaX = clientX - startXRef.current;
    const deltaY = clientY - startYRef.current;
    if (deltaY > 78 && deltaY > Math.abs(deltaX) * 1.2) {
      trackingRef.current = false;
      closedRef.current = true;
      onClose();
    }
  };

  const onPointerDown: PointerEventHandler<HTMLElement> = (event) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;

    const target = event.target as HTMLElement | null;
    const surface = event.currentTarget;
    const rect = surface.getBoundingClientRect();
    const startedOnHandle = Boolean(
      target?.closest(".mobile-sheet-grabber, .mini-game-head, .mini-game-result-head, .card-h, [data-swipe-close-handle='true']")
    );
    const startedNearTop = event.clientY - rect.top <= 104;

    if (!startedOnHandle && !startedNearTop) return;

    startXRef.current = event.clientX;
    startYRef.current = event.clientY;
    trackingRef.current = true;
    closedRef.current = false;
    surface.setPointerCapture?.(event.pointerId);
  };

  const onPointerMove: PointerEventHandler<HTMLElement> = (event) => {
    closeIfSwipe(event.clientX, event.clientY);
  };

  const finish: PointerEventHandler<HTMLElement> = (event) => {
    if (!trackingRef.current) return;
    closeIfSwipe(event.clientX, event.clientY);
    trackingRef.current = false;
  };

  return {
    onPointerDown,
    onPointerMove,
    onPointerUp: finish,
    onPointerCancel: () => {
      trackingRef.current = false;
    },
  };
}
