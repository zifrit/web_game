/** Единый источник палитр редкости (rank f..ex). Не дублировать по компонентам. */

export const RARITY_COLOR: Record<string, string> = {
  f: "#94A3B8",
  e: "#22C55E",
  d: "#38BDF8",
  c: "#3B82F6",
  b: "#A855F7",
  a: "#F59E0B",
  s: "#EF4444",
  ex: "#F8FAFC",
};

export const RARITY_GLOW: Record<string, string> = {
  f: "rgba(148,163,184,0.25)",
  e: "rgba(34,197,94,0.30)",
  d: "rgba(56,189,248,0.32)",
  c: "rgba(59,130,246,0.35)",
  b: "rgba(168,85,247,0.35)",
  a: "rgba(245,158,11,0.35)",
  s: "rgba(239,68,68,0.35)",
  ex: "rgba(248,250,252,0.35)",
};

export const RARITY_BG: Record<string, string> = {
  f: "rgba(148,163,184,0.05)",
  e: "rgba(34,197,94,0.06)",
  d: "rgba(56,189,248,0.06)",
  c: "rgba(59,130,246,0.07)",
  b: "rgba(168,85,247,0.08)",
  a: "rgba(245,158,11,0.08)",
  s: "rgba(239,68,68,0.08)",
  ex: "rgba(248,250,252,0.08)",
};

export const RARITY_BORDER: Record<string, string> = {
  f: "rgba(148,163,184,0.15)",
  e: "rgba(34,197,94,0.22)",
  d: "rgba(56,189,248,0.22)",
  c: "rgba(59,130,246,0.24)",
  b: "rgba(168,85,247,0.28)",
  a: "rgba(245,158,11,0.3)",
  s: "rgba(239,68,68,0.3)",
  ex: "rgba(248,250,252,0.28)",
};

export function rarityColor(rarity?: string | null): string {
  return RARITY_COLOR[(rarity ?? "f").toLowerCase()] ?? RARITY_COLOR.f;
}

export function rarityGlow(rarity?: string | null): string {
  return RARITY_GLOW[(rarity ?? "f").toLowerCase()] ?? RARITY_GLOW.f;
}
