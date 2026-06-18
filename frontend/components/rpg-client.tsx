"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Backpack, BookOpen, ChevronRight, Compass, Gem, LogOut, MoreHorizontal, Plus, Settings2, ShoppingBag, Swords, Trophy } from "lucide-react";
import { useEffect, useState, type CSSProperties } from "react";
import { useIsMobile } from "@/lib/use-is-mobile";
import { AuthScreen } from "@/components/screens/auth-screen";
import { CharacterScreen } from "@/components/screens/character-screen";
import { CreateCharacterScreen } from "@/components/screens/create-character-screen";
import { DungeonsScreen } from "@/components/screens/dungeons-screen";
import { GuidebookScreen } from "@/components/screens/guide-screen";
import { InventoryScreen } from "@/components/screens/inventory-screen";
import { LeaderboardScreen } from "@/components/screens/leaderboard-screen";
import { SettingsScreen } from "@/components/screens/settings-screen";
import { ShopScreen } from "@/components/screens/shop-screen";
import { ExchangeModal } from "@/components/exchange-modal";
import { LoadingLine, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { useI18n, useSession } from "@/components/providers";
import { formatNumber, splitCopper, type TranslationKey } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import { useSwipeToClose } from "@/lib/use-modal-scroll-lock";
import type { MediaAssetUrls } from "@/lib/types";

type Tab = "character" | "dungeons" | "shop" | "inventory" | "leaderboard" | "settings" | "guide";

const VALID_TABS: Tab[] = ["character", "dungeons", "shop", "inventory", "leaderboard", "settings", "guide"];

function getInitialTab(): Tab {
  if (typeof window === "undefined") return "character";
  const saved = localStorage.getItem("activeTab") as Tab | null;
  return saved && VALID_TABS.includes(saved) ? saved : "character";
}

/* ── nav structure ── */
const ADVENTURE_NAV: Array<{ key: Tab; labelKey: "nav.character" | "nav.dungeons" | "nav.shop" }> = [
  { key: "character", labelKey: "nav.character" },
  { key: "dungeons",  labelKey: "nav.dungeons"  },
  { key: "shop",      labelKey: "nav.shop"      },
];

const HERO_NAV: Array<{ key: Tab; labelKey: "nav.inventory" | "nav.leaderboard" | "nav.settings" | "nav.guide" }> = [
  { key: "inventory",   labelKey: "nav.inventory"   },
  { key: "leaderboard", labelKey: "nav.leaderboard" },
  { key: "guide",       labelKey: "nav.guide"       },
  { key: "settings",    labelKey: "nav.settings"    },
];

const NAV_ICONS: Record<Tab, React.ReactNode> = {
  character:   <Swords      size={15} strokeWidth={1.7} />,
  dungeons:    <Compass     size={15} strokeWidth={1.7} />,
  shop:        <ShoppingBag size={15} strokeWidth={1.7} />,
  inventory:   <Backpack    size={15} strokeWidth={1.7} />,
  leaderboard: <Trophy      size={15} strokeWidth={1.7} />,
  guide:       <BookOpen    size={15} strokeWidth={1.7} />,
  settings:    <Settings2   size={15} strokeWidth={1.7} />,
};

const PAGE_META: Record<Tab, { sectionKey: TranslationKey; titleKey: TranslationKey }> = {
  character:   { sectionKey: "page.character.section",    titleKey: "page.character.title" },
  dungeons:    { sectionKey: "page.dungeons.section",     titleKey: "page.dungeons.title"  },
  shop:        { sectionKey: "page.shop.section",         titleKey: "page.shop.title" },
  inventory:   { sectionKey: "page.inventory.section",    titleKey: "page.inventory.title" },
  leaderboard: { sectionKey: "page.leaderboard.section",  titleKey: "page.leaderboard.title" },
  settings:    { sectionKey: "page.settings.section",     titleKey: "page.settings.title" },
  guide:       { sectionKey: "page.guide.section",        titleKey: "page.guide.title" },
};

/* ─── Sidebar ─── */
function Sidebar({
  tab,
  setTab,
  characterName,
  characterClass,
  characterLevel,
  characterRank,
  userAvatar,
  isLoadingCharacter,
  onLogout,
  t,
}: {
  tab: Tab;
  setTab: (t: Tab) => void;
  characterName?: string;
  characterClass?: string;
  characterLevel?: number;
  characterRank?: string;
  userAvatar?: MediaAssetUrls | null;
  isLoadingCharacter?: boolean;
  onLogout: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const footerAvatarUrl = bestMediaUrl(userAvatar, ["small_url", "medium_url", "large_url"]);

  return (
    <aside style={{
      background: "linear-gradient(180deg, #111827, #0B1020)",
      borderRight: "1px solid #2E3B5A",
      padding: "28px 18px",
      position: "sticky",
      top: 0,
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      gap: 4,
      width: 240,
      flexShrink: 0,
      overflowY: "auto",
    }}>
      {/* Brand */}
      <div style={{
        display: "flex", alignItems: "center", gap: 10,
        padding: "0 6px 22px", borderBottom: "1px solid #243150", marginBottom: 18,
      }}>
        <div style={{
          width: 32, height: 32, flexShrink: 0,
          background: "linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%)",
          borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center",
          border: "1px solid rgba(96,165,250,0.35)",
          boxShadow: "0 0 16px rgba(59,130,246,0.28), inset 0 1px 0 rgba(255,255,255,0.1)",
        }}>
          <Swords size={15} color="#93C5FD" strokeWidth={1.7} />
        </div>
        <div>
          <div style={{
            fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
            fontSize: 20, fontWeight: 600, letterSpacing: "0.02em",
          }}>VultWake</div>
        </div>
      </div>

      {/* Adventure section */}
      <div style={{
        fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
        fontSize: 10, letterSpacing: "0.20em", textTransform: "uppercase",
        color: "#64748B", padding: "18px 12px 6px",
      }}>{t("nav.adventure")}</div>

      {ADVENTURE_NAV.map((item) => (
        <button
          key={item.key}
          onClick={() => setTab(item.key)}
          className={`nav-item ${tab === item.key ? "active" : ""}`}
        >
          <span style={{
            width: 18, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
            color: tab === item.key ? "#60A5FA" : "#4B5E7A",
          }}>{NAV_ICONS[item.key]}</span>
          <span>{t(item.labelKey)}</span>
        </button>
      ))}

      {/* Hero section */}
      <div style={{
        fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
        fontSize: 10, letterSpacing: "0.20em", textTransform: "uppercase",
        color: "#64748B", padding: "18px 12px 6px",
      }}>{t("nav.hero")}</div>

      {HERO_NAV.map((item) => (
        <button
          key={item.key}
          onClick={() => setTab(item.key)}
          className={`nav-item ${tab === item.key ? "active" : ""}`}
        >
          <span style={{
            width: 18, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
            color: tab === item.key ? "#60A5FA" : "#4B5E7A",
          }}>{NAV_ICONS[item.key]}</span>
          <span>{t(item.labelKey)}</span>
        </button>
      ))}

      {/* Footer */}
      <div style={{
        marginTop: "auto", paddingTop: 18, borderTop: "1px solid #243150",
        display: "flex", flexDirection: "column", gap: 12,
      }}>
        {(characterName || isLoadingCharacter) && (
          <div style={{ display: "flex", alignItems: "center", gap: 10, width: "100%" }}>
            {/* Avatar: skeleton while loading, then real avatar or placeholder */}
            {isLoadingCharacter && !characterName ? (
              <Skeleton style={{ width: 47, height: 47, borderRadius: "50%", flexShrink: 0 }} />
            ) : (
              <div style={{
                width: 47, height: 47, borderRadius: "50%", flexShrink: 0,
                background: "#202B44",
                border: "1px solid #2E3B5A",
                overflow: "hidden",
                position: "relative",
              }}>
                {footerAvatarUrl && (
                  <img
                    src={footerAvatarUrl}
                    alt={characterName}
                    style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
                  />
                )}
              </div>
            )}
            <div style={{ minWidth: 0, flex: 1 }}>
              {isLoadingCharacter && !characterName ? (
                <>
                  <Skeleton style={{ height: 12, width: "70%", marginBottom: 6 }} />
                  <Skeleton style={{ height: 9, width: "90%" }} />
                </>
              ) : (
                <>
                  <div style={{
                    fontSize: 13, fontWeight: 500,
                    whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                    color: "#E5E7EB",
                  }}>{characterName}</div>
                  <div style={{
                    fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                    fontSize: 10, color: "#64748B", letterSpacing: "0.12em", textTransform: "uppercase",
                  }}>
                    {characterClass ?? "—"} · {t("common.levelShort")} {characterLevel ?? "—"} · {t("common.rank")} {characterRank ?? "—"}
                  </div>
                </>
              )}
            </div>
            <button
              onClick={onLogout}
              style={{
                background: "transparent", border: "none", cursor: "pointer",
                color: "#64748B", padding: "4px", borderRadius: 4, display: "flex",
              }}
              title="Logout"
            >
              <LogOut size={14} />
            </button>
          </div>
        )}
        <div style={{
          fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
          fontSize: 10, color: "#64748B", letterSpacing: "0.18em", textTransform: "uppercase",
          padding: "0 2px",
        }}>v0.1 — MVP</div>
      </div>
    </aside>
  );
}

/* ─── Mobile top app bar ─── */
function MobileTopbar({ gold, premium, onOpenExchange }: {
  gold?: number;
  premium?: number;
  onOpenExchange?: () => void;
}) {
  const { locale, t } = useI18n();
  const money = splitCopper(gold);
  const moneyLabels = locale === "ru"
    ? { gold: "з", silver: "с", copper: "м" }
    : { gold: "g", silver: "s", copper: "c" };
  return (
    <header style={{
      flexShrink: 0,
      display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10,
      padding: "10px 14px 12px",
      background: "#0B1020",
      borderBottom: "1px solid #2E3B5A",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0, flex: 1 }}>
        <div style={{
          width: 28, height: 28, flexShrink: 0,
          background: "linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%)",
          borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center",
          border: "1px solid rgba(96,165,250,0.35)",
          boxShadow: "0 0 16px rgba(59,130,246,0.25), inset 0 1px 0 rgba(255,255,255,0.1)",
        }}>
          <Swords size={14} color="#93C5FD" strokeWidth={1.7} />
        </div>
        <div style={{
          minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
          fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
          fontSize: 16, fontWeight: 600, letterSpacing: "0.02em", color: "#F1F5F9",
        }}>VultWake</div>
      </div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 6, flexShrink: 0 }}>
        {premium !== undefined && (
          <div style={{
            display: "flex", alignItems: "center", gap: 4,
            padding: "6px 9px", borderRadius: 9,
            background: "rgba(168,85,247,0.10)", border: "1px solid rgba(168,85,247,0.25)",
            fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
          }}>
            <Gem size={11} color="#c084fc" />
            <span style={{ fontSize: 11, fontWeight: 600, color: "#d8b4fe" }}>{formatNumber(premium, locale)}</span>
          </div>
        )}
        {gold !== undefined && (
          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "6px 10px", boxSizing: "border-box",
            borderRadius: 9, whiteSpace: "nowrap", overflow: "hidden",
            background: "#1A2235", border: "1px solid #2E3B5A",
            fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
          }}>
            <span style={{ color: "#64748B", letterSpacing: "0.1em", textTransform: "uppercase", fontSize: 8 }}>{t("common.money")}</span>
            <span style={{ display: "inline-flex", alignItems: "baseline", gap: 4, fontSize: 11, fontWeight: 700 }}>
              <span style={{ color: "#FBBF24" }}>{formatNumber(money.gold, locale)}{moneyLabels.gold}</span>
              <span style={{ color: "#CBD5E1" }}>{money.silver}{moneyLabels.silver}</span>
              <span style={{ color: "#CD7C45" }}>{money.copper}{moneyLabels.copper}</span>
            </span>
            {onOpenExchange && (
              <button
                onClick={onOpenExchange}
                title={t("exchange.title")}
                aria-label={t("exchange.title")}
                style={{
                  display: "inline-flex", alignItems: "center", justifyContent: "center",
                  width: 17, height: 17, borderRadius: 5, cursor: "pointer",
                  background: "rgba(96,165,250,0.14)", border: "1px solid rgba(96,165,250,0.35)",
                  color: "#93C5FD",
                }}
              >
                <Plus size={10} strokeWidth={3} />
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

/* ─── Mobile bottom nav (5 items; last opens the More sheet) ─── */
const BOTTOM_NAV: Array<{ key: Tab; labelKey: TranslationKey; icon: React.ReactNode }> = [
  { key: "character", labelKey: "nav.character", icon: <Swords size={22} strokeWidth={1.9} /> },
  { key: "dungeons",  labelKey: "nav.dungeons",  icon: <Compass size={22} strokeWidth={1.9} /> },
  { key: "shop",      labelKey: "nav.shop",      icon: <ShoppingBag size={22} strokeWidth={1.9} /> },
  { key: "inventory", labelKey: "nav.inventory", icon: <Backpack size={22} strokeWidth={1.9} /> },
];

const MORE_TABS: Tab[] = ["leaderboard", "guide", "settings"];

function BottomNav({ tab, setTab, moreOpen, onOpenMore }: {
  tab: Tab;
  setTab: (t: Tab) => void;
  moreOpen: boolean;
  onOpenMore: () => void;
}) {
  const { t } = useI18n();
  const moreActive = moreOpen || MORE_TABS.includes(tab);
  const itemStyle = (active: boolean): CSSProperties => ({
    flex: 1, background: "none", border: "none", cursor: "pointer",
    display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
    padding: "6px 0",
    color: active ? "#60A5FA" : "#5d6b86",
    transition: "color 150ms ease",
  });
  const labelStyle: CSSProperties = { fontSize: 10, fontWeight: 600 };
  return (
    <nav style={{
      position: "fixed", left: 0, right: 0, bottom: 0, zIndex: 40,
      height: "var(--mobile-nav-h)",
      padding: "8px 10px calc(env(safe-area-inset-bottom, 0px) + 10px)",
      background: "linear-gradient(180deg, rgba(8,11,20,0.4), rgba(6,8,15,0.96) 45%)",
      backdropFilter: "blur(16px)",
      borderTop: "1px solid rgba(110,140,190,0.10)",
      display: "flex", alignItems: "flex-start",
    }}>
      {BOTTOM_NAV.map((item) => {
        const active = tab === item.key;
        return (
          <button key={item.key} onClick={() => setTab(item.key)} style={itemStyle(active)}>
            {item.icon}
            <span style={labelStyle}>{t(item.labelKey)}</span>
          </button>
        );
      })}
      <button onClick={onOpenMore} style={itemStyle(moreActive)}>
        <MoreHorizontal size={22} strokeWidth={1.9} />
        <span style={labelStyle}>{t("nav.more")}</span>
      </button>
    </nav>
  );
}

/* ─── More bottom-sheet (Leaderboard / Guide / Settings + logout) ─── */
function MoreSheet({ tab, setTab, onClose, onLogout, characterName, characterClass, characterLevel, characterRank, userAvatar }: {
  tab: Tab;
  setTab: (t: Tab) => void;
  onClose: () => void;
  onLogout: () => void;
  characterName?: string;
  characterClass?: string;
  characterLevel?: number;
  characterRank?: string;
  userAvatar?: MediaAssetUrls | null;
}) {
  const { t } = useI18n();
  const swipeToClose = useSwipeToClose(onClose);
  const avatarUrl = bestMediaUrl(userAvatar, ["small_url", "medium_url", "large_url"]);
  const items: Array<{ key: Tab; labelKey: TranslationKey; icon: React.ReactNode }> = [
    { key: "leaderboard", labelKey: "nav.leaderboard", icon: <Trophy size={18} strokeWidth={1.8} /> },
    { key: "guide",       labelKey: "nav.guide",       icon: <BookOpen size={18} strokeWidth={1.8} /> },
    { key: "settings",    labelKey: "nav.settings",    icon: <Settings2 size={18} strokeWidth={1.8} /> },
  ];
  const pick = (next: Tab) => { setTab(next); onClose(); };
  return (
    <>
      <div className="mobile-sheet-overlay" style={{ zIndex: 50 }} onClick={onClose} />
      <div className="mobile-sheet animate-sheet-up" {...swipeToClose} style={{
        zIndex: 51,
        padding: "10px 16px calc(env(safe-area-inset-bottom, 0px) + 24px)",
      }}>
        <div className="mobile-sheet-grabber" style={{ margin: "4px auto 14px" }} />
        <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
          {items.map((mi) => {
            const active = tab === mi.key;
            return (
              <button key={mi.key} onClick={() => pick(mi.key)} style={{
                display: "flex", alignItems: "center", gap: 13, padding: 14, borderRadius: 14,
                textAlign: "left", cursor: "pointer",
                border: `1px solid ${active ? "rgba(96,165,250,0.35)" : "rgba(110,140,190,0.12)"}`,
                background: active ? "rgba(59,130,246,0.12)" : "rgba(16,22,38,0.5)",
                color: active ? "#9cc0ff" : "#cdd6e6",
              }}>
                <span style={{ width: 24, display: "flex", justifyContent: "center" }}>{mi.icon}</span>
                <span style={{ flex: 1, fontWeight: 600, fontSize: 14 }}>{t(mi.labelKey)}</span>
                <ChevronRight size={16} style={{ opacity: 0.5 }} />
              </button>
            );
          })}
        </div>
        {characterName && (
          <div style={{
            marginTop: 14, display: "flex", alignItems: "center", gap: 11,
            padding: "13px 14px", borderRadius: 14,
            background: "rgba(11,16,28,0.5)", border: "1px solid rgba(110,140,190,0.08)",
          }}>
            <div style={{
              width: 40, height: 40, borderRadius: "50%", flexShrink: 0, overflow: "hidden",
              background: "linear-gradient(135deg,#2a3656,#171f36)", position: "relative",
            }}>
              {avatarUrl && <img src={avatarUrl} alt={characterName} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 700, fontSize: 13, color: "#dbe2ef", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{characterName}</div>
              <div style={{
                fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                fontSize: 8.5, letterSpacing: "0.12em", textTransform: "uppercase", color: "#7c89a3", marginTop: 1,
              }}>{characterClass ?? "—"} · {t("common.levelShort")} {characterLevel ?? "—"} · {t("common.rank")} {characterRank ?? "—"}</div>
            </div>
            <button onClick={() => { onClose(); onLogout(); }} title="Logout" style={{
              width: 38, height: 38, borderRadius: 10, flexShrink: 0, cursor: "pointer",
              border: "1px solid rgba(239,90,90,0.3)", background: "rgba(239,90,90,0.1)", color: "#f87171",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <LogOut size={17} />
            </button>
          </div>
        )}
      </div>
    </>
  );
}

/* ─── Topbar ─── */
function Topbar({ meta, title, level, rank, gold, premium, onOpenExchange }: {
  meta: { section: string };
  title: string;
  level?: number;
  rank?: string;
  gold?: number;
  premium?: number;
  onOpenExchange?: () => void;
}) {
  const { locale, t } = useI18n();
  const money = splitCopper(gold);
  const moneyLabels = locale === "ru"
    ? { gold: "з", silver: "с", copper: "м" }
    : { gold: "g", silver: "s", copper: "c" };
  // Shared pill chrome; width is per-pill (level + premium hug content, money is wider).
  const pillStyle: CSSProperties = {
    display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
    height: 38, padding: "0 16px", boxSizing: "border-box",
    borderRadius: 11, whiteSpace: "nowrap", overflow: "hidden",
    fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
  };
  return (
    <header style={{
      display: "flex", alignItems: "flex-end", justifyContent: "space-between",
      borderBottom: "1px solid #2E3B5A", background: "#0B1020",
      padding: "20px 36px 20px",
      flexShrink: 0,
    }}>
      <div>
        <div style={{
          fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
          fontSize: 11, letterSpacing: "0.20em", textTransform: "uppercase",
          color: "#64748B", marginBottom: 4,
        }}>{meta.section}</div>
        <h1 style={{
          fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
          fontWeight: 600, fontSize: 28, margin: 0, letterSpacing: "0.04em", color: "#F1F5F9",
        }}>{title}</h1>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {level !== undefined && (
          <div style={{
            ...pillStyle,
            background: "#1A2235", border: "1px solid #2E3B5A",
            fontSize: 12,
          }}>
            <span style={{ color: "#64748B", letterSpacing: "0.12em", textTransform: "uppercase", fontSize: 10 }}>{t("common.levelShort")}</span>
            <span style={{ color: "#F1F5F9", fontWeight: 600 }}>{level}</span>
            {rank && <span style={{ color: "#94A3B8", fontWeight: 700 }}>{rank}</span>}
          </div>
        )}
        {premium !== undefined && (
          <div style={{
            ...pillStyle,
            background: "#1A2235", border: "1px solid #3B2A55",
            fontSize: 14, fontWeight: 700,
            color: "#C084FC",
          }}>
            <Gem size={14} /> {formatNumber(premium, locale)}
          </div>
        )}
        {gold !== undefined && (
          <div style={{
            ...pillStyle,
            background: "#1A2235", border: "1px solid #2E3B5A",
            fontSize: 14, minWidth: 200,
          }}>
            <span style={{ color: "#64748B", letterSpacing: "0.12em", textTransform: "uppercase", fontSize: 12 }}>{t("common.money")}</span>
            <span style={{ display: "inline-flex", alignItems: "baseline", gap: 7, fontWeight: 700 }}>
              <span style={{ color: "#FBBF24" }}>{formatNumber(money.gold, locale)}{moneyLabels.gold}</span>
              <span style={{ color: "#CBD5E1" }}>{money.silver}{moneyLabels.silver}</span>
              <span style={{ color: "#CD7C45" }}>{money.copper}{moneyLabels.copper}</span>
            </span>
            {onOpenExchange && (
              <button
                onClick={onOpenExchange}
                title={t("exchange.title")}
                aria-label={t("exchange.title")}
                style={{
                  display: "inline-flex", alignItems: "center", justifyContent: "center",
                  width: 24, height: 24, marginLeft: 2, borderRadius: 7, cursor: "pointer",
                  background: "rgba(96,165,250,0.14)", border: "1px solid rgba(96,165,250,0.35)",
                  color: "#93C5FD",
                }}
              >
                <Plus size={14} strokeWidth={2.2} />
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

/* ═══════════════════════════════════════
   Main RpgClient
═══════════════════════════════════════ */
export function RpgClient() {
  const { accessToken, user, isBooting, logout, setUser } = useSession();
  const { t } = useI18n();
  const [tab, setTabState] = useState<Tab>(getInitialTab);
  const [inventoryInitialSection, setInventoryInitialSection] = useState<"equipment" | "consumables">("equipment");
  const setTab = (next: Tab) => {
    if (next === "inventory") {
      setInventoryInitialSection("equipment");
    }
    setTabState(next);
    localStorage.setItem("activeTab", next);
  };
  const openInventory = (section: "equipment" | "consumables" = "equipment") => {
    setInventoryInitialSection(section);
    setTabState("inventory");
    localStorage.setItem("activeTab", "inventory");
  };
  const [exchangeOpen, setExchangeOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const isMobile = useIsMobile();
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: api.me,
    enabled: Boolean(accessToken),
    staleTime: 10_000,
  });

  const characterQuery = useQuery({
    queryKey: ["character"],
    queryFn: api.character,
    enabled: Boolean(accessToken) && Boolean(meQuery.data?.has_character),
    staleTime: 30_000,
  });

  const activeUser = meQuery.data ?? user;

  useEffect(() => {
    if (meQuery.data) setUser(meQuery.data);
  }, [meQuery.data, setUser]);

  /* ── Loading / auth gates ── */
  if (isBooting) {
    return (
      <main style={{ display: "grid", minHeight: "100vh", placeItems: "center", padding: 24 }}>
        <LoadingLine label={t("common.loading")} />
      </main>
    );
  }
  if (!accessToken) return <AuthScreen />;
  if (meQuery.isLoading && !activeUser) {
    return (
      <main style={{ display: "grid", minHeight: "100vh", placeItems: "center", padding: 24 }}>
        <LoadingLine label={t("character.loadingHero")} />
      </main>
    );
  }
  if (!activeUser?.has_character) return <CreateCharacterScreen />;

  const charLevel = characterQuery.data?.level;
  const gold = activeUser.money_copper ?? 0;
  const premium = activeUser.premium_currency ?? 0;
  const pageMeta = PAGE_META[tab];
  const meta = { section: t(pageMeta.sectionKey) };
  const pageTitle = tab === "character" && characterQuery.data
    ? characterQuery.data.name
    : t(pageMeta.titleKey);

  const handleLogout = () => {
    queryClient.clear();
    void logout();
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>

      {/* ─── Sidebar (desktop) ─── */}
      <div className="hidden lg:block">
        <Sidebar
          tab={tab}
          setTab={setTab}
          characterName={characterQuery.data?.name}
          characterClass={characterQuery.data?.class?.name}
          characterLevel={characterQuery.data?.level}
          characterRank={characterQuery.data?.rank}
          userAvatar={activeUser?.avatar}
          isLoadingCharacter={characterQuery.isLoading}
          onLogout={handleLogout}
          t={t}
        />
      </div>

      {/* ─── Main area ─── */}
      <div style={{ display: "flex", flexDirection: "column", flex: 1, minWidth: 0 }}>

        {/* Top header: full desktop topbar, slim currency bar on mobile */}
        {isMobile ? (
          <MobileTopbar
            gold={gold}
            premium={premium}
            onOpenExchange={() => setExchangeOpen(true)}
          />
        ) : (
          <Topbar
            meta={meta}
            title={pageTitle}
            level={charLevel}
            rank={characterQuery.data?.rank}
            gold={gold}
            premium={premium}
            onOpenExchange={() => setExchangeOpen(true)}
          />
        )}

        {/* Page content */}
        <div
          data-app-scroll-root
          className={isMobile ? "mobile-noscroll" : undefined}
          style={{
            flex: 1, overflowY: "auto",
            padding: isMobile ? "16px 16px calc(var(--mobile-nav-h) + 16px)" : "28px 36px 60px",
          }}
        >
          <div
            style={{ maxWidth: isMobile ? "100%" : 1400, width: "100%", margin: "0 auto" }}
            className="animate-fade-in"
          >
            {tab === "character"   && (
              <CharacterScreen
                onOpenDungeons={() => setTab("dungeons")}
                onOpenInventory={() => openInventory("equipment")}
              />
            )}
            {tab === "dungeons"    && (
              <DungeonsScreen
                onOpenInventory={() => openInventory("equipment")}
                onOpenConsumables={() => openInventory("consumables")}
              />
            )}
            {tab === "shop"        && <ShopScreen />}
            {tab === "inventory"   && <InventoryScreen initialSection={inventoryInitialSection} />}
            {tab === "leaderboard" && <LeaderboardScreen />}
            {tab === "settings"    && <SettingsScreen />}
            {tab === "guide"       && <GuidebookScreen />}
          </div>
        </div>
      </div>

      {/* ─── Mobile bottom nav + More sheet ─── */}
      {isMobile && (
        <BottomNav
          tab={tab}
          setTab={setTab}
          moreOpen={moreOpen}
          onOpenMore={() => setMoreOpen(true)}
        />
      )}
      {isMobile && moreOpen && (
        <MoreSheet
          tab={tab}
          setTab={setTab}
          onClose={() => setMoreOpen(false)}
          onLogout={handleLogout}
          characterName={characterQuery.data?.name}
          characterClass={characterQuery.data?.class?.name}
          characterLevel={characterQuery.data?.level}
          characterRank={characterQuery.data?.rank}
          userAvatar={activeUser?.avatar}
        />
      )}

      {exchangeOpen && <ExchangeModal onClose={() => setExchangeOpen(false)} />}
    </div>
  );
}
