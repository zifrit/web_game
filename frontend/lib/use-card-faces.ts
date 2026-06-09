"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { api } from "@/lib/api";
import type { MiniGameCardFaceCatalog } from "@/lib/types";

const STORAGE_KEY = "mini-game-card-faces";
// localStorage нужен только для мгновенного первого рендера; backend остаётся
// источником истины, чтобы изменения из админки подтягивались сразу.
const STALE_TIME_MS = 0;

function readCache(): MiniGameCardFaceCatalog | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as MiniGameCardFaceCatalog) : undefined;
  } catch {
    return undefined;
  }
}

function writeCache(catalog: MiniGameCardFaceCatalog) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(catalog));
  } catch {
    // localStorage недоступен — работаем без персистентного кеша.
  }
}

/**
 * Загружает каталог SVG-лиц, обновляет localStorage и резолвит code → svg.
 * Возвращает карту кодов в разметку для локального рендера карточек.
 */
export function useCardFaces() {
  const query = useQuery({
    queryKey: ["mini-game-card-faces"],
    queryFn: async () => {
      const catalog = await api.miniGameCardFaces();
      writeCache(catalog);
      return catalog;
    },
    initialData: readCache,
    initialDataUpdatedAt: 0,
    staleTime: STALE_TIME_MS,
    refetchOnMount: "always",
  });

  const facesByCode = useMemo(() => {
    const map = new Map<string, string>();
    for (const face of query.data?.faces ?? []) {
      map.set(face.code, face.svg);
    }
    return map;
  }, [query.data]);

  return { facesByCode, isLoading: query.isLoading };
}
