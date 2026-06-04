"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Backpack, BookOpen, Compass, LogOut, Settings2, Swords, Trophy } from "lucide-react";
import { useEffect, useState } from "react";
import { AuthScreen } from "@/components/screens/auth-screen";
import { CharacterScreen } from "@/components/screens/character-screen";
import { CreateCharacterScreen } from "@/components/screens/create-character-screen";
import { DungeonsScreen } from "@/components/screens/dungeons-screen";
import { GuidebookScreen } from "@/components/screens/guide-screen";
import { InventoryScreen } from "@/components/screens/inventory-screen";
import { LeaderboardScreen } from "@/components/screens/leaderboard-screen";
import { SettingsScreen } from "@/components/screens/settings-screen";
import { LoadingLine, Skeleton } from "@/components/ui";
import { api } from "@/lib/api";
import { useI18n, useSession } from "@/components/providers";
import { formatNumber, splitCopper, type TranslationKey } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import type { MediaAssetUrls } from "@/lib/types";

type Tab = "character" | "dungeons" | "inventory" | "leaderboard" | "settings" | "guide";

const VALID_TABS: Tab[] = ["character", "dungeons", "inventory", "leaderboard", "settings", "guide"];

function getInitialTab(): Tab {
  if (typeof window === "undefined") return "character";
  const saved = localStorage.getItem("activeTab") as Tab | null;
  return saved && VALID_TABS.includes(saved) ? saved : "character";
}

/* ── nav structure ── */
const ADVENTURE_NAV: Array<{ key: Tab; labelKey: "nav.character" | "nav.dungeons" }> = [
  { key: "character", labelKey: "nav.character" },
  { key: "dungeons",  labelKey: "nav.dungeons"  },
];

const HERO_NAV: Array<{ key: Tab; labelKey: "nav.inventory" | "nav.leaderboard" | "nav.settings" | "nav.guide" }> = [
  { key: "inventory",   labelKey: "nav.inventory"   },
  { key: "leaderboard", labelKey: "nav.leaderboard" },
  { key: "guide",       labelKey: "nav.guide"       },
  { key: "settings",    labelKey: "nav.settings"    },
];

const NAV_ICONS: Record<Tab, React.ReactNode> = {
  character:   <Swords    size={15} strokeWidth={1.7} />,
  dungeons:    <Compass   size={15} strokeWidth={1.7} />,
  inventory:   <Backpack  size={15} strokeWidth={1.7} />,
  leaderboard: <Trophy    size={15} strokeWidth={1.7} />,
  guide:       <BookOpen  size={15} strokeWidth={1.7} />,
  settings:    <Settings2 size={15} strokeWidth={1.7} />,
};

const PAGE_META: Record<Tab, { sectionKey: TranslationKey; titleKey: TranslationKey }> = {
  character:   { sectionKey: "page.character.section",    titleKey: "page.character.title" },
  dungeons:    { sectionKey: "page.dungeons.section",     titleKey: "page.dungeons.title"  },
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
  characterAvatar,
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
  characterAvatar?: MediaAssetUrls | null;
  isLoadingCharacter?: boolean;
  onLogout: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const footerAvatarUrl = bestMediaUrl(characterAvatar ?? userAvatar, ["small_url", "medium_url", "large_url"]);

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
          }}>Ashreach</div>
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

/* ─── Mobile nav (bottom bar on small screens) ─── */
function MobileNav({ tab, setTab }: { tab: Tab; setTab: (t: Tab) => void }) {
  const { t } = useI18n();
  const all = [...ADVENTURE_NAV, ...HERO_NAV];
  return (
    <nav style={{
      display: "grid",
      gridTemplateColumns: `repeat(${all.length}, 1fr)`,
      borderBottom: "1px solid #2E3B5A",
      background: "#0D1525",
    }}>
      {all.map((item) => (
        <button
          key={item.key}
          onClick={() => setTab(item.key)}
          style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
            padding: "10px 4px",
            fontSize: 9, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em",
            color: tab === item.key ? "#60A5FA" : "#4B6AA3",
            background: "transparent", border: "none", cursor: "pointer",
            borderBottom: tab === item.key ? "2px solid #3B82F6" : "2px solid transparent",
            transition: "all 150ms ease",
          }}
        >
          <span style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 18, height: 18 }}>
            {NAV_ICONS[item.key]}
          </span>
          {t(item.labelKey)}
        </button>
      ))}
    </nav>
  );
}

/* ─── Topbar ─── */
function Topbar({ meta, title, level, rank, gold }: {
  meta: { section: string };
  title: string;
  level?: number;
  rank?: string;
  gold?: number;
}) {
  const { locale, t } = useI18n();
  const money = splitCopper(gold);
  const moneyLabels = locale === "ru"
    ? { gold: "з", silver: "с", copper: "м" }
    : { gold: "g", silver: "s", copper: "c" };
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
            display: "flex", alignItems: "center", gap: 8,
            padding: "8px 14px", borderRadius: 10,
            background: "#1A2235", border: "1px solid #2E3B5A",
            fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)", fontSize: 12,
          }}>
            <span style={{ color: "#64748B", letterSpacing: "0.12em", textTransform: "uppercase", fontSize: 10 }}>{t("common.levelShort")}</span>
            <span style={{ color: "#F1F5F9", fontWeight: 600 }}>{level}</span>
            {rank && <span style={{ color: "#94A3B8", fontWeight: 700 }}>{rank}</span>}
          </div>
        )}
        {gold !== undefined && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8,
            padding: "10px 17px", borderRadius: 12,
            background: "#1A2235", border: "1px solid #2E3B5A",
            fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)", fontSize: 14,
          }}>
            <span style={{ color: "#64748B", letterSpacing: "0.12em", textTransform: "uppercase", fontSize: 12 }}>{t("common.money")}</span>
            <span style={{ display: "inline-flex", alignItems: "baseline", gap: 7, fontWeight: 700 }}>
              <span style={{ color: "#FBBF24" }}>{formatNumber(money.gold, locale)}{moneyLabels.gold}</span>
              <span style={{ color: "#CBD5E1" }}>{money.silver}{moneyLabels.silver}</span>
              <span style={{ color: "#CD7C45" }}>{money.copper}{moneyLabels.copper}</span>
            </span>
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
  const setTab = (next: Tab) => {
    setTabState(next);
    localStorage.setItem("activeTab", next);
  };
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
          characterAvatar={characterQuery.data?.avatar}
          isLoadingCharacter={characterQuery.isLoading}
          onLogout={handleLogout}
          t={t}
        />
      </div>

      {/* ─── Main area ─── */}
      <div style={{ display: "flex", flexDirection: "column", flex: 1, minWidth: 0 }}>

        {/* Top header */}
        <Topbar
          meta={meta}
          title={pageTitle}
          level={charLevel}
          rank={characterQuery.data?.rank}
          gold={gold}
        />

        {/* Mobile nav */}
        <div className="lg:hidden">
          <MobileNav tab={tab} setTab={setTab} />
        </div>

        {/* Page content */}
        <div style={{ flex: 1, overflowY: "auto", padding: "28px 36px 60px" }}>
          <div style={{ maxWidth: 1400, width: "100%", margin: "0 auto" }} className="animate-fade-in">
            {tab === "character"   && (
              <CharacterScreen
                onOpenDungeons={() => setTab("dungeons")}
                onOpenInventory={() => setTab("inventory")}
              />
            )}
            {tab === "dungeons"    && <DungeonsScreen />}
            {tab === "inventory"   && <InventoryScreen />}
            {tab === "leaderboard" && <LeaderboardScreen />}
            {tab === "settings"    && <SettingsScreen />}
            {tab === "guide"       && <GuidebookScreen />}
          </div>
        </div>
      </div>
    </div>
  );
}
