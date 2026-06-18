"use client";

import { useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import type React from "react";
import { api } from "@/lib/api";
import type { Dungeon, DungeonResourceDrop } from "@/lib/types";
import { useI18n } from "@/components/providers";
import { LoadingLine } from "@/components/ui";
import { formatDuration } from "@/lib/i18n";
import type { TranslationKey } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import { useModalScrollLock, useSwipeToClose } from "@/lib/use-modal-scroll-lock";

/* Категория ингредиента → акцентный цвет (не только цвет — рядом всегда текст-метка). */
const CATEGORY_COLOR: Record<DungeonResourceDrop["category"], string> = {
  basic: "var(--text-mute)",
  regional: "#60a5fa",
  rare: "#fbbf24",
};

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

export function DungeonResourceModal({
  location,
  onClose,
  actions,
}: {
  location: Dungeon;
  onClose: () => void;
  actions?: React.ReactNode;
}) {
  useModalScrollLock();
  const swipeToClose = useSwipeToClose(onClose);

  const { locale, t } = useI18n();
  const resourcesQuery = useQuery({
    queryKey: ["dungeon-resources", location.id],
    queryFn: () => api.dungeonResources(location.id),
    staleTime: 60_000,
  });

  const durLabel = formatDuration(location.duration_seconds, locale);
  const dailyRemaining = location.daily_remaining ?? location.daily_limit;
  const dailyUsed = location.daily_limit - dailyRemaining;

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
          background: "linear-gradient(135deg, rgba(34,197,94,0.08), rgba(15,23,42,0))",
        }}>
          <div style={{ flex: 1, minWidth: 0, paddingRight: 16 }}>
            <h2 style={{
              fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
              fontSize: 19, fontWeight: 600, margin: 0,
              letterSpacing: "0.04em", color: "var(--bone)",
            }}>
              {location.name}
            </h2>
            <div className="mono" style={{
              fontSize: 9, letterSpacing: "0.22em", color: "var(--success)",
              marginTop: 5, textTransform: "uppercase",
            }}>
              {t("dungeons.resourceOverview")}
            </div>
            {location.description && (
              <p style={{
                margin: "10px 0 0",
                color: "var(--text-dim)",
                fontSize: 13,
                lineHeight: 1.5,
                maxWidth: 520,
              }}>
                {location.description}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            aria-label={locale === "ru" ? "Закрыть" : "Close"}
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
          {/* Время сбора */}
          <StatCard label={locale === "ru" ? "Время сбора" : "Gathering"} color="var(--bone)">
            <span style={{ whiteSpace: "nowrap" }}>{durLabel}</span>
          </StatCard>

          {/* Успех */}
          <StatCard label={locale === "ru" ? "Успех" : "Success"} color="var(--success)">
            <span style={{ whiteSpace: "nowrap" }}>{t("dungeons.guaranteedSuccess")}</span>
          </StatCard>

          {/* Дневной лимит */}
          {location.daily_limit > 0 && (
            <StatCard label={locale === "ru" ? "Заходы" : "Runs"} color="var(--bone)">
              <span style={{ whiteSpace: "nowrap" }}>{dailyUsed}/{location.daily_limit}</span>
            </StatCard>
          )}

          {/* Лимит категории */}
          {location.limit_category.limit_count > 0 && (
            <StatCard label={location.limit_category.name} color="var(--bone)">
              <span style={{ whiteSpace: "nowrap" }}>
                {location.limit_category.used}/{location.limit_category.limit_count}
              </span>
            </StatCard>
          )}
        </div>

        {/* Resource drop table */}
        <div style={{ overflowY: "auto", padding: "16px 24px", maxHeight: 340 }}>
          <div className="mono" style={{
            fontSize: 9, letterSpacing: "0.22em", color: "var(--text-mute)",
            marginBottom: 12, textTransform: "uppercase",
          }}>
            {t("dungeons.possibleResources")}
          </div>

          {resourcesQuery.isLoading && <LoadingLine />}

          {resourcesQuery.data?.length === 0 && (
            <div className="mono" style={{
              fontSize: 13, color: "var(--text-mute)", textAlign: "center",
              padding: "40px 0",
            }}>
              {t("dungeons.noResources")}
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {resourcesQuery.data?.map((drop) => {
              const color = CATEGORY_COLOR[drop.category] ?? CATEGORY_COLOR.basic;
              const iconUrl = bestMediaUrl(drop.media, ["small_url", "medium_url", "large_url"]);
              const qtyLabel = drop.min_quantity === drop.max_quantity
                ? `×${drop.min_quantity}`
                : `×${drop.min_quantity}–${drop.max_quantity}`;

              return (
                <div
                  key={drop.id}
                  style={{
                    background: `color-mix(in srgb, ${color} 7%, transparent)`,
                    border: `1px solid color-mix(in srgb, ${color} 24%, transparent)`,
                    borderRadius: 10, padding: "12px 14px",
                    display: "flex", alignItems: "center", gap: 12,
                  }}
                >
                  {/* Icon */}
                  <div style={{
                    width: 44, height: 44, minWidth: 44, borderRadius: 8,
                    background: "var(--bg-3)",
                    border: "1px solid var(--line-soft)",
                    overflow: "hidden", position: "relative", flexShrink: 0,
                  }}>
                    {iconUrl && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={iconUrl}
                        alt={drop.name}
                        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
                      />
                    )}
                  </div>

                  {/* Name + meta */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
                      <span style={{
                        fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                        fontSize: 15, fontWeight: 600, color: "var(--bone)",
                      }}>
                        {drop.name}
                      </span>
                      <span className="mono" style={{
                        fontSize: 9, letterSpacing: "0.14em",
                        padding: "2px 8px", borderRadius: 4,
                        background: `color-mix(in srgb, ${color} 14%, transparent)`,
                        border: `1px solid color-mix(in srgb, ${color} 34%, transparent)`,
                        color, textTransform: "uppercase",
                      }}>
                        {t(`dungeons.resourceCategory.${drop.category}` as TranslationKey)}
                      </span>
                    </div>
                    {drop.description && (
                      <p style={{
                        margin: 0, color: "var(--text-mute)", fontSize: 11, lineHeight: 1.4,
                        overflow: "hidden", display: "-webkit-box",
                        WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as React.CSSProperties["WebkitBoxOrient"],
                      }}>
                        {drop.description}
                      </p>
                    )}
                  </div>

                  {/* Chance + quantity */}
                  <div style={{
                    display: "flex", flexDirection: "column", alignItems: "flex-end",
                    gap: 4, flexShrink: 0,
                    fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                  }}>
                    <span style={{ fontSize: 14, fontWeight: 600, color: "var(--success)" }}>
                      {drop.chance_percent}%
                    </span>
                    <span className="mono" style={{ fontSize: 11, color: "var(--text-mute)", letterSpacing: "0.04em" }}>
                      {qtyLabel}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: "12px 24px",
          borderTop: "1px solid var(--line-soft)",
          display: "flex", justifyContent: "space-between", alignItems: "center",
          gap: 12, flexWrap: "wrap",
        }}>
          {actions ?? <span />}
          <button className="btn btn-secondary" onClick={onClose}>
            {locale === "ru" ? "Закрыть" : "Close"}
          </button>
        </div>
      </div>
    </div>
  );
}
