"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";
import { createPortal } from "react-dom";

export type ToastTone = "success" | "error";

type ToastInput = {
  tone: ToastTone;
  message: string;
};

type ToastItem = ToastInput & {
  id: number;
  phase: "entering" | "leaving";
};

type ToastContextValue = {
  showToast: (toast: ToastInput) => void;
  showError: (error: unknown, fallback?: string) => void;
  showSuccess: (message: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const VISIBLE_MS = 5000;
const LEAVE_MS = 300;

let nextId = 1;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const timersRef = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  const clearTimer = useCallback((id: number) => {
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const remove = useCallback((id: number) => {
    clearTimer(id);
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, [clearTimer]);

  const dismiss = useCallback((id: number) => {
    clearTimer(id);
    setToasts((prev) =>
      prev.map((toast) => (toast.id === id ? { ...toast, phase: "leaving" } : toast)),
    );
    const timer = setTimeout(() => remove(id), LEAVE_MS);
    timersRef.current.set(id, timer);
  }, [clearTimer, remove]);

  const scheduleDismiss = useCallback((id: number) => {
    clearTimer(id);
    const timer = setTimeout(() => dismiss(id), VISIBLE_MS);
    timersRef.current.set(id, timer);
  }, [clearTimer, dismiss]);

  const showToast = useCallback((input: ToastInput) => {
    const message = input.message?.trim();
    if (!message) return;

    setToasts((prev) => {
      // Дедупликация: тот же текст и тон уже показывается — сбрасываем таймер.
      const existing = prev.find(
        (toast) => toast.message === message && toast.tone === input.tone && toast.phase === "entering",
      );
      if (existing) {
        scheduleDismiss(existing.id);
        return prev;
      }
      const id = nextId++;
      scheduleDismiss(id);
      return [...prev, { id, tone: input.tone, message, phase: "entering" }];
    });
  }, [scheduleDismiss]);

  const showError = useCallback((error: unknown, fallback?: string) => {
    const message =
      error instanceof Error && error.message
        ? error.message
        : fallback ?? "Что-то пошло не так. Попробуйте ещё раз.";
    showToast({ tone: "error", message });
  }, [showToast]);

  const showSuccess = useCallback((message: string) => {
    showToast({ tone: "success", message });
  }, [showToast]);

  // Регистрируем мост, чтобы React Query (вне React-дерева) мог показывать тосты.
  useEffect(() => {
    setToastBridge(showToast);
    return () => setToastBridge(null);
  }, [showToast]);

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach((timer) => clearTimeout(timer));
      timers.clear();
    };
  }, []);

  const value = useMemo(
    () => ({ showToast, showError, showSuccess }),
    [showToast, showError, showSuccess],
  );

  const stack = typeof document !== "undefined" && toasts.length > 0
    ? createPortal(
        <div className="toast-stack" aria-live="polite" role="region" aria-label="Notifications">
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className={`toast toast-${toast.tone}${toast.phase === "leaving" ? " toast-leaving" : ""}`}
              role="status"
              onClick={() => dismiss(toast.id)}
            >
              {toast.message}
            </div>
          ))}
        </div>,
        document.body,
      )
    : null;

  return (
    <ToastContext.Provider value={value}>
      {children}
      {stack}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used inside ToastProvider");
  }
  return context;
}

// ── Мост для использования вне React-дерева (React Query onError) ──
type ToastBridge = (toast: ToastInput) => void;
let toastBridge: ToastBridge | null = null;

function setToastBridge(bridge: ToastBridge | null) {
  toastBridge = bridge;
}

export function emitToast(toast: ToastInput) {
  toastBridge?.(toast);
}
