"use client";

import { useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import type React from "react";
import { api } from "@/lib/api";
import type { Dungeon } from "@/lib/types";
import { useI18n } from "@/components/providers";
import { LoadingLine } from "@/components/ui";
import { formatCopperCompact, formatDuration, formatStatName } from "@/lib/i18n";
import type { TranslationKey } from "@/lib/i18n";
import { RARITY_BG, RARITY_BORDER, RARITY_COLOR } from "@/lib/rarity";
import { useModalScrollLock, useSwipeToClose } from "@/lib/use-modal-scroll-lock";

function getRarityStyle(rarity: string | null) {
  const key = (rarity ?? "f").toLowerCase();
  return {
    color: RARITY_COLOR[key] ?? RARITY_COLOR.f,
    bg: RARITY_BG[key] ?? RARITY_BG.f,
    border: RARITY_BORDER[key] ?? RARITY_BORDER.f,
  };
}

function formatPercent(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function StatCard({
  label,
  color,
  children,
}: {
  label: string;
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(255,255,255,0.07)",
      borderRadius: 8, padding: "10px 12px",
      minWidth: 0,
    }}>
      <div className="mono" style={{
        fontSize: 9, letterSpacing: "0.16em", color: "var(--text-mute)",
        marginBottom: 5, textTransform: "uppercase",
      }}>
        {label}
      </div>
      <div className="mono" style={{
        fontSize: 13, fontWeight: 600, color, lineHeight: 1.35,
        display: "flex", flexDirection: "column", alignItems: "flex-start",
        overflow: "hidden",
      }}>
        {children}
      </div>
    </div>
  );
}

export function DungeonLootModal({
  dungeon,
  onClose,
}: {
  dungeon: Dungeon;
  onClose: () => void;
}) {
  useModalScrollLock();
  const swipeToClose = useSwipeToClose(onClose);

  const { locale, t } = useI18n();
  const lootQuery = useQuery({
    queryKey: ["dungeon-loot", dungeon.id],
    queryFn: () => api.dungeonLoot(dungeon.id),
    staleTime: 60_000,
  });

  const durLabel = formatDuration(dungeon.duration_seconds, locale);

  return (
    /* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions */
    <div
      className="modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      style={{ alignItems: "flex-start", paddingTop: "clamp(60px, 6vh, 80px)", paddingBottom: "clamp(16px, 3vh, 40px)" }}
    >
      <div
        className="modal"
        {...swipeToClose}
        style={{
          width: "min(660px, 94vw)",
          maxHeight: "calc(100vh - clamp(76px, 9vh, 120px))",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div style={{
          padding: "20px 24px 14px",
          borderBottom: "1px solid var(--line-soft)",
          display: "flex", justifyContent: "space-between", alignItems: "flex-start",
          background: "linear-gradient(135deg, rgba(59,130,246,0.08), rgba(15,23,42,0))",
        }}>
          <div style={{ flex: 1, minWidth: 0, paddingRight: 16 }}>
            <h2 style={{
              fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
              fontSize: 19, fontWeight: 600, margin: 0,
              letterSpacing: "0.04em", color: "var(--bone)",
            }}>
              {dungeon.name}
            </h2>
            <div className="mono" style={{
              fontSize: 9, letterSpacing: "0.22em", color: "var(--primary-bright)",
              marginTop: 5, textTransform: "uppercase",
            }}>
              {t("dungeons.overview")}
            </div>
            {dungeon.description && (
              <p style={{
                margin: "10px 0 0",
                color: "var(--text-dim)",
                fontSize: 13,
                lineHeight: 1.5,
                maxWidth: 520,
              }}>
                {dungeon.description}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            style={{
              background: "none", border: "none", cursor: "pointer",
              color: "var(--text-mute)", padding: 4, borderRadius: 6,
              transition: "color 0.15s ease",
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Overview stats strip */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
          gap: 8, padding: "14px 24px",
          borderBottom: "1px solid var(--line-soft)",
        }}>
          {/* Время */}
          <StatCard label={locale === "ru" ? "Время" : "Duration"} color="var(--bone)">
            <span style={{ whiteSpace: "nowrap" }}>{durLabel}</span>
          </StatCard>

          {/* Опыт */}
          <StatCard label={locale === "ru" ? "Опыт" : "XP"} color="#60a5fa">
            <span style={{ whiteSpace: "nowrap" }}>
              {dungeon.rewards_preview?.experience?.min ?? "?"}
              <span style={{ color: "var(--text-mute)", fontWeight: 400, margin: "0 3px" }}>–</span>
              {dungeon.rewards_preview?.experience?.max ?? "?"}&thinsp;XP
            </span>
          </StatCard>

          {/* Золото */}
          <StatCard label={locale === "ru" ? "Золото" : "Gold"} color="#fbbf24">
            <span style={{ whiteSpace: "nowrap" }}>
              {formatCopperCompact(dungeon.rewards_preview?.money_copper?.min, locale)}
            </span>
            <span style={{ color: "var(--text-mute)", fontSize: 10, margin: "1px 0" }}>—</span>
            <span style={{ whiteSpace: "nowrap" }}>
              {formatCopperCompact(dungeon.rewards_preview?.money_copper?.max, locale)}
            </span>
          </StatCard>

          {/* Лут */}
          <StatCard label={locale === "ru" ? "Лут" : "Loot"} color="var(--success)">
            <span style={{ whiteSpace: "nowrap" }}>{dungeon.item_drop_chance}%</span>
          </StatCard>

          <StatCard label={t("dungeons.hpLossSuccess")} color="#f87171">
            <span style={{ whiteSpace: "nowrap" }}>{formatPercent(dungeon.hp_loss_success_percent)}%</span>
          </StatCard>

          <StatCard label={t("dungeons.hpLossFail")} color="#ef4444">
            <span style={{ whiteSpace: "nowrap" }}>{formatPercent(dungeon.hp_loss_fail_percent)}%</span>
          </StatCard>
        </div>

        {/* Loot table — высота ≈ 3 карточки */}
        <div style={{ overflowY: "auto", padding: "16px 24px", maxHeight: 340 }}>
          <div className="mono" style={{
            fontSize: 9, letterSpacing: "0.22em", color: "var(--text-mute)",
            marginBottom: 12, textTransform: "uppercase",
          }}>
            {locale === "ru" ? "Возможные предметы" : "Possible Items"}
          </div>

          {lootQuery.isLoading && <LoadingLine />}

          {lootQuery.data?.length === 0 && (
            <div className="mono" style={{
              fontSize: 13, color: "var(--text-mute)", textAlign: "center",
              padding: "40px 0",
            }}>
              {locale === "ru" ? "Предметы для этого данжа не заданы" : "No items configured for this dungeon"}
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {lootQuery.data?.map((item, idx) => {
              const { color, bg, border } = getRarityStyle(item.rarity);
              const hasStats = Object.keys(item.possible_stats).length > 0;

              return (
                <div
                  key={idx}
                  style={{
                    background: bg,
                    border: `1px solid ${border}`,
                    borderRadius: 10, padding: "14px 16px",
                  }}
                >
                  {/* Item name row */}
                  <div style={{
                    display: "flex", justifyContent: "space-between",
                    alignItems: "center", flexWrap: "wrap", gap: 8,
                    marginBottom: 10,
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                      <span style={{
                        fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                        fontSize: 15, fontWeight: 600, color: "var(--bone)",
                      }}>
                        {item.name}
                      </span>
                      {item.rarity && (
                        <span className="mono" style={{
                          fontSize: 9, letterSpacing: "0.14em",
                          padding: "2px 8px", borderRadius: 4,
                          background: `color-mix(in srgb, ${color} 14%, transparent)`,
                          border: `1px solid ${border}`,
                          color, textTransform: "uppercase",
                        }}>
                          {item.rarity}
                        </span>
                      )}
                    </div>
                    <span className="mono" style={{
                      fontSize: 10, letterSpacing: "0.1em", color: "var(--success)",
                      flexShrink: 0,
                    }}>
                      {item.chance}%
                    </span>
                  </div>

                  {/* Meta row: slot / durability / classes */}
                  <div style={{
                    display: "flex", flexWrap: "wrap", gap: "3px 18px",
                    marginBottom: hasStats ? 10 : 0,
                    fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                    fontSize: 11, color: "var(--text-mute)",
                  }}>
                    <span>
                      {locale === "ru" ? "Слот" : "Slot"}:{" "}
                      <strong style={{ color: "var(--bone)" }}>
                        {t(`slot.${item.slot}` as TranslationKey)}
                      </strong>
                    </span>
                    <span>
                      {locale === "ru" ? "Прочность" : "Durability"}:{" "}
                      <strong style={{ color: "var(--bone)" }}>
                        {item.min_durability}–{item.max_durability}
                      </strong>
                    </span>
                    <span>
                      {locale === "ru" ? "Классы" : "Classes"}:{" "}
                      <strong style={{ color: "var(--bone)" }}>
                        {item.allowed_classes.length > 0
                          ? item.allowed_classes.join(", ")
                          : locale === "ru" ? "Все" : "All"}
                      </strong>
                    </span>
                  </div>

                  {/* Possible stats */}
                  {hasStats && (
                    <div style={{
                      display: "flex", flexWrap: "wrap", gap: "4px 14px",
                      fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                      fontSize: 11,
                    }}>
                      {Object.entries(item.possible_stats).map(([key, range]) => (
                        <span key={key} style={{ color: "var(--text-mute)" }}>
                          {formatStatName(key, locale)}:{" "}
                          <strong style={{ color }}>{range.min}–{range.max}</strong>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: "12px 24px",
          borderTop: "1px solid var(--line-soft)",
          display: "flex", justifyContent: "flex-end",
        }}>
          <button className="btn btn-secondary" onClick={onClose}>
            {locale === "ru" ? "Закрыть" : "Close"}
          </button>
        </div>
      </div>
    </div>
  );
}
