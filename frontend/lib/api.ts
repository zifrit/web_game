import type * as AppTypes from "@/lib/types";
import type { Locale } from "@/lib/i18n";

export type Tokens = {
  access_token: string;
  refresh_token: string;
};

let activeLocale: Locale = "en";

function defaultApiBase() {
  if (typeof window === "undefined") {
    return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
  }

  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configured) {
    try {
      const url = new URL(configured);
      const currentHost = window.location.hostname;
      if (["localhost", "127.0.0.1", "0.0.0.0"].includes(url.hostname) && ["localhost", "127.0.0.1", "0.0.0.0"].includes(currentHost)) {
        url.hostname = currentHost;
        return url.toString().replace(/\/$/, "");
      }
      return configured.replace(/\/$/, "");
    } catch {
      return configured.replace(/\/$/, "");
    }
  }

  const protocol = window.location.protocol;
  const host = window.location.hostname;
  return `${protocol}//${host}:8000/api`;
}

function apiBase() {
  return defaultApiBase();
}

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

function fallbackErrorMessage(status: number, statusText: string): string {
  if (status >= 500) return "Сервер недоступен. Попробуйте позже.";
  if (status === 404) return "Ресурс не найден.";
  if (status === 403) return "Доступ запрещён.";
  if (status === 401) return "Сессия истекла. Войдите снова.";
  return statusText || "Что-то пошло не так. Попробуйте ещё раз.";
}

// Превращает тело ответа DRF в человекочитаемое сообщение.
// Никогда не возвращает сырой JSON.
export function extractApiErrorMessage(body: unknown, status: number, statusText: string): string {
  if (typeof body === "string" && body.trim()) return body;
  if (!body || typeof body !== "object") return fallbackErrorMessage(status, statusText);

  const record = body as Record<string, unknown>;

  const pickString = (value: unknown): string | null => {
    if (typeof value === "string" && value.trim()) return value;
    if (Array.isArray(value)) {
      for (const item of value) {
        const found = pickString(item);
        if (found) return found;
      }
    }
    return null;
  };

  const detail = pickString(record.detail);
  if (detail) return detail;

  const nonField = pickString(record.non_field_errors);
  if (nonField) return nonField;

  // DRF field-errors: { field: ["msg", ...] }
  for (const value of Object.values(record)) {
    const message = pickString(value);
    if (message) return message;
  }

  return fallbackErrorMessage(status, statusText);
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
  const response = await fetch(`${apiBase()}/auth/refresh`, {
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
  const response = await fetch(`${apiBase()}${path}`, { ...options, headers });
  if (response.status === 401 && retry && tokens?.refresh_token) {
    const next = await refreshAccessToken(tokens);
    return apiFetch<T>(path, {
      ...options,
      headers: { ...Object.fromEntries(headers.entries()), Authorization: `Bearer ${next.access_token}` },
    }, false);
  }
  if (!response.ok) {
    let message = fallbackErrorMessage(response.status, response.statusText);
    try {
      const body = await response.json();
      message = extractApiErrorMessage(body, response.status, response.statusText);
    } catch {
      // keep fallback message
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
    return apiFetch<AppTypes.LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }, false);
  },
  verifyLoginTotp(challengeToken: string, code: string) {
    return apiFetch<AppTypes.AuthResponse>("/auth/login/totp", {
      method: "POST",
      body: JSON.stringify({ challenge_token: challengeToken, code }),
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
  createCharacter(name: string, class_key: string, gender: "male" | "female") {
    return apiFetch<AppTypes.Character>("/characters", {
      method: "POST",
      body: JSON.stringify({ name, class_key, gender }),
    });
  },
  character() {
    return apiFetch<AppTypes.Character>("/characters/me");
  },
  dungeons() {
    return apiFetch<AppTypes.Dungeon[]>("/dungeons");
  },
  dungeonLoot(dungeonId: number) {
    return apiFetch<AppTypes.DungeonLootItem[]>(`/dungeons/${dungeonId}/loot`);
  },
  dungeonResources(dungeonId: number) {
    return apiFetch<AppTypes.DungeonResourceDrop[]>(`/dungeons/${dungeonId}/resources`);
  },
  startRun(locationId: number, autoRun = false) {
    return apiFetch<AppTypes.DungeonRun>("/dungeon-runs", {
      method: "POST",
      body: JSON.stringify({ location_id: locationId, auto_run: autoRun }),
    });
  },
  currentRun() {
    return apiFetch<AppTypes.CurrentRunResponse>("/dungeon-runs/current");
  },
  stopAutoRun() {
    return apiFetch<AppTypes.AutoRunState>("/dungeon-auto-runs/current/stop", { method: "POST" });
  },
  markAutoRunSummaryRead() {
    return apiFetch<{ summary_unread: false }>("/dungeon-auto-runs/current/summary/read", { method: "POST" });
  },
  claimRun(runId: number) {
    return apiFetch<AppTypes.ClaimResponse>(`/dungeon-runs/${runId}/claim`, { method: "POST" });
  },
  miniGameConfigs() {
    return apiFetch<AppTypes.DungeonMiniGameConfig[]>("/mini-game/configs");
  },
  miniGameCardFaces() {
    return apiFetch<AppTypes.MiniGameCardFaceCatalog>("/mini-game/card-faces");
  },
  startMiniGame(runId: number, configId?: number) {
    return apiFetch<AppTypes.DungeonMiniGameAttempt>(`/dungeon-runs/${runId}/mini-game/start`, {
      method: "POST",
      body: JSON.stringify(configId != null ? { config_id: configId } : {}),
    });
  },
  revealMiniGameCard(attemptId: number, cardId: string) {
    return apiFetch<AppTypes.DungeonMiniGameRevealResponse>(`/dungeon-mini-games/${attemptId}/reveal`, {
      method: "POST",
      body: JSON.stringify({ card_id: cardId }),
    });
  },
  moveMiniGame(attemptId: number, payload: { first_card_id: string; second_card_id: string }) {
    return apiFetch<AppTypes.DungeonMiniGameMoveResponse>(`/dungeon-mini-games/${attemptId}/move`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  miniGameHistory(limit = 20) {
    return apiFetch<AppTypes.DungeonMiniGameHistoryItem[]>(`/dungeon-mini-games/history?limit=${limit}`);
  },
  inventory(page = 1, pageSize = 24) {
    return apiFetch<AppTypes.Inventory>(`/inventory?page=${page}&page_size=${pageSize}`);
  },
  item(itemId: number) {
    return apiFetch<AppTypes.ItemDetail>(`/inventory/items/${itemId}`);
  },
  repairPreview(itemIds: number[]) {
    return apiFetch<AppTypes.RepairPreview>("/inventory/items/repair-preview", {
      method: "POST",
      body: JSON.stringify({ item_ids: itemIds }),
    });
  },
  repair(itemIds: number[]) {
    return apiFetch<AppTypes.RepairResponse>("/inventory/items/repair", {
      method: "POST",
      body: JSON.stringify({ item_ids: itemIds }),
    });
  },
  destroyPreview(itemIds: number[]) {
    return apiFetch<AppTypes.DestroyPreview>("/inventory/items/destroy-preview", {
      method: "POST",
      body: JSON.stringify({ item_ids: itemIds }),
    });
  },
  destroy(itemIds: number[]) {
    return apiFetch<AppTypes.DestroyResponse>("/inventory/items/destroy", {
      method: "POST",
      body: JSON.stringify({ item_ids: itemIds }),
    });
  },
  equip(itemId: number) {
    return apiFetch<AppTypes.InventoryMutationResponse>(`/inventory/items/${itemId}/equip`, { method: "POST" });
  },
  unequip(itemId: number) {
    return apiFetch<AppTypes.InventoryMutationResponse>(`/inventory/items/${itemId}/unequip`, { method: "POST" });
  },
  potions() {
    return apiFetch<AppTypes.Potion[]>("/potions");
  },
  ingredients() {
    return apiFetch<AppTypes.Ingredient[]>("/ingredients");
  },
  usePotion(body: { potion_id: number; quantity: number }) {
    return apiFetch<AppTypes.UsePotionResponse>("/potions/use", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  craftRecipes() {
    return apiFetch<AppTypes.CraftRecipe[]>("/craft/recipes");
  },
  craftPotions(body: { recipe_id: number; quantity: number }) {
    return apiFetch<AppTypes.CraftResponse>("/craft/potions", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  leaderboard(type: AppTypes.LeaderboardMetric = "level") {
    return apiFetch<AppTypes.Leaderboard>(`/leaderboard?type=${type}`);
  },
  iconAssets() {
    return apiFetch<AppTypes.IconAsset[]>("/media/icons");
  },
  updateAvatar(avatarMediaId: number) {
    return apiFetch<{ avatar: AppTypes.MediaAssetUrls }>("/auth/me/avatar", {
      method: "PATCH",
      body: JSON.stringify({ avatar_media_id: avatarMediaId }),
    });
  },
  shopOffers() {
    return apiFetch<AppTypes.ShopOffer[]>("/shop/offers");
  },
  shopOffer(id: number) {
    return apiFetch<AppTypes.ShopOfferDetail>(`/shop/offers/${id}`);
  },
  buyShopOffer(id: number, payload: { purchase_count: number; payment_currency: AppTypes.PaymentCurrency }) {
    return apiFetch<AppTypes.BuyShopOfferResponse>(`/shop/offers/${id}/buy`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  shopPurchases() {
    return apiFetch<{ results: AppTypes.ShopPurchase[] }>("/shop/purchases");
  },
  billingExchangeOffers() {
    return apiFetch<AppTypes.ExchangeOffer[]>("/billing/exchange-offers");
  },
  billingExchangeOffer(id: number) {
    return apiFetch<AppTypes.ExchangeOffer>(`/billing/exchange-offers/${id}`);
  },
  exchangeCurrency(id: number) {
    return apiFetch<AppTypes.ExchangeResponse>(`/billing/exchange-offers/${id}/exchange`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },
  billingExchangeTransactions() {
    return apiFetch<{ results: AppTypes.ExchangeTransaction[] }>("/billing/exchange-transactions");
  },
  billingPremiumTransactions() {
    return apiFetch<{ results: AppTypes.PremiumTransaction[] }>("/billing/premium-transactions");
  },
  twoFactorStatus() {
    return apiFetch<AppTypes.TwoFactorStatus>("/auth/two-factor");
  },
  startTwoFactorSetup() {
    return apiFetch<AppTypes.TwoFactorSetup>("/auth/two-factor/setup", { method: "POST" });
  },
  confirmTwoFactorSetup(code: string) {
    return apiFetch<AppTypes.TwoFactorStatus>("/auth/two-factor/confirm", {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  },
  disableTwoFactor(password: string, code: string) {
    return apiFetch<AppTypes.TwoFactorStatus>("/auth/two-factor/disable", {
      method: "POST",
      body: JSON.stringify({ password, code }),
    });
  },
};
