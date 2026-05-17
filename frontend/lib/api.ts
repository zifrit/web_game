import type * as AppTypes from "@/lib/types";
import type { Locale } from "@/lib/i18n";

export type Tokens = {
  access_token: string;
  refresh_token: string;
};

export type ApiUser = {
  id: number;
  email: string;
  money_copper?: number;
  has_character: boolean;
};

export type AuthPayload = Tokens & { user: ApiUser };

export type CharacterClass = {
  key: string;
  name: string;
  start_stats: Record<string, number>;
};

export type Character = {
  id: number;
  name: string;
  class: { key: string; name: string };
  level: number;
  experience: number;
  experience_to_next_level: number;
  stats: Record<string, number>;
  equipment: Record<string, ItemSummary | null>;
};

export type Dungeon = {
  id: number;
  name: string;
  description: string;
  duration_seconds: number;
  required_power: number;
  success_chance: number;
  item_drop_chance: number;
  rewards_preview: {
    experience: { min: number; max: number };
    money_copper: { min: number; max: number };
  };
};

export type CurrentRun =
  | { current_run: null }
  | {
      id: number;
      status: "IN_PROGRESS";
      location: { id: number; name: string };
      remaining_seconds: number;
      ends_at: string;
    }
  | {
      id: number;
      status: "SUCCESS_WAITING_CLAIM" | "FAILED_WAITING_CLAIM";
      location: { id: number; name: string };
      result_preview: {
        is_success: boolean;
        experience: number;
        money_copper: number;
        items_count: number;
        durability_loss: number;
      };
    };

export type ItemSummary = {
  id: number;
  name?: string;
  icon_url: string;
  slot: string;
  rarity: string;
  is_broken: boolean;
};

export type Inventory = {
  equipment_summary: Record<string, number>;
  equipped: Record<string, ItemSummary | null>;
  items_count: number;
  slots_limit: number | null;
  free_slots: number | null;
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  items: ItemSummary[];
};

export type ItemDetail = {
  id: number;
  name: string;
  slot: string;
  item_type: string;
  rarity: string;
  item_level: number;
  stats: Record<string, number>;
  durability: { current: number; max: number };
  is_equipped: boolean;
  is_broken: boolean;
  can_equip: boolean;
};

export type RepairPreview = {
  item_id: number;
  durability: { current: number; max: number; missing: number };
  repair_cost_copper: number;
  user_money_copper: number;
  can_repair: boolean;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
let activeLocale: Locale = "en";

export function setApiLocale(locale: Locale) {
  activeLocale = locale;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function readTokens(): Tokens | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem("rpg_tokens");
  return raw ? (JSON.parse(raw) as Tokens) : null;
}

export function getStoredTokens() {
  const tokens = readTokens();
  return {
    accessToken: tokens?.access_token ?? null,
    refreshToken: tokens?.refresh_token ?? null,
  };
}

export function writeTokens(tokens: Tokens | null) {
  if (typeof window === "undefined") return;
  if (!tokens) {
    window.localStorage.removeItem("rpg_tokens");
    return;
  }
  window.localStorage.setItem("rpg_tokens", JSON.stringify(tokens));
}

export function storeTokens(accessToken: string, refreshToken: string) {
  writeTokens({ access_token: accessToken, refresh_token: refreshToken });
}

export function clearTokens() {
  writeTokens(null);
}

async function refreshAccessToken(tokens: Tokens): Promise<Tokens> {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept-Language": activeLocale },
    body: JSON.stringify({ refresh: tokens.refresh_token }),
  });
  if (!response.ok) throw new ApiError(response.status, "Session expired");
  const data = (await response.json()) as { access?: string; refresh?: string; access_token?: string; refresh_token?: string };
  const next = {
    access_token: data.access ?? data.access_token ?? tokens.access_token,
    refresh_token: data.refresh ?? data.refresh_token ?? tokens.refresh_token,
  };
  writeTokens(next);
  return next;
}

export async function apiFetch<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const tokens = readTokens();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  headers.set("Accept-Language", activeLocale);
  if (tokens?.access_token) headers.set("Authorization", `Bearer ${tokens.access_token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 401 && retry && tokens?.refresh_token) {
    const next = await refreshAccessToken(tokens);
    return apiFetch<T>(path, {
      ...options,
      headers: { ...Object.fromEntries(headers.entries()), Authorization: `Bearer ${next.access_token}` },
    }, false);
  }
  if (!response.ok) {
    let message = response.statusText;
    try {
      const body = await response.json();
      message = body.detail ?? body.non_field_errors?.[0] ?? JSON.stringify(body);
    } catch {
      // keep status text
    }
    throw new ApiError(response.status, message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function formatMoney(copper: number) {
  const gold = Math.floor(copper / 10000);
  const silver = Math.floor((copper % 10000) / 100);
  const rest = copper % 100;
  return `${gold}g ${silver}s ${rest}c`;
}

export const api = {
  register(email: string, password: string) {
    return apiFetch<AppTypes.AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }, false);
  },
  login(email: string, password: string) {
    return apiFetch<AppTypes.AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }, false);
  },
  logout(refreshToken: string) {
    return apiFetch<void>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken, refresh: refreshToken }),
    });
  },
  me() {
    return apiFetch<AppTypes.User>("/auth/me");
  },
  characterClasses() {
    return apiFetch<AppTypes.CharacterClass[]>("/character-classes");
  },
  createCharacter(name: string, class_key: string) {
    return apiFetch<AppTypes.Character>("/characters", {
      method: "POST",
      body: JSON.stringify({ name, class_key }),
    });
  },
  character() {
    return apiFetch<AppTypes.Character>("/characters/me");
  },
  dungeons() {
    return apiFetch<AppTypes.Dungeon[]>("/dungeons");
  },
  startRun(location_id: number) {
    return apiFetch<AppTypes.DungeonRun>("/dungeon-runs", {
      method: "POST",
      body: JSON.stringify({ location_id }),
    });
  },
  currentRun() {
    return apiFetch<AppTypes.DungeonRun | { current_run: null }>("/dungeon-runs/current").then((run) =>
      "current_run" in run ? null : run,
    );
  },
  claimRun(runId: number) {
    return apiFetch<AppTypes.ClaimResponse>(`/dungeon-runs/${runId}/claim`, { method: "POST" });
  },
  inventory(page = 1, pageSize = 24) {
    return apiFetch<AppTypes.Inventory>(`/inventory?page=${page}&page_size=${pageSize}`);
  },
  item(itemId: number) {
    return apiFetch<AppTypes.ItemDetail>(`/inventory/items/${itemId}`);
  },
  repairPreview(itemId: number) {
    return apiFetch<AppTypes.RepairPreview>(`/inventory/items/${itemId}/repair-preview`);
  },
  repair(itemId: number) {
    return apiFetch(`/inventory/items/${itemId}/repair`, { method: "POST" });
  },
  equip(itemId: number) {
    return apiFetch(`/inventory/items/${itemId}/equip`, { method: "POST" });
  },
  unequip(itemId: number) {
    return apiFetch(`/inventory/items/${itemId}/unequip`, { method: "POST" });
  },
  leaderboard() {
    return apiFetch<AppTypes.Leaderboard>("/leaderboard?type=level");
  },
};
