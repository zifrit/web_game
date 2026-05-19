"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useI18n } from "@/components/providers";
import { ErrorNotice, LoadingLine } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDuration } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import type { DungeonRun } from "@/lib/types";

/* ── Timer hook ── */
function useRemainingSeconds(run?: DungeonRun | null) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!run?.ends_at || run.status !== "IN_PROGRESS") return;
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, [run?.ends_at, run?.status]);
  return useMemo(() => {
    if (!run || run.status !== "IN_PROGRESS") return 0;
    if (run.ends_at) return Math.max(0, Math.ceil((new Date(run.ends_at).getTime() - now) / 1000));
    return Math.max(0, run.remaining_seconds ?? 0);
  }, [now, run]);
}

function formatTime(secs: number) {
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h > 0) return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/* ── Active run banner ── */
function ActiveRunBanner({ run }: { run: DungeonRun }) {
  const queryClient = useQueryClient();
  const { t } = useI18n();
  const remaining   = useRemainingSeconds(run);

  const totalSecs = useMemo(() => {
    if (run.ends_at && run.started_at) {
      return Math.max(1, Math.ceil((new Date(run.ends_at).getTime() - new Date(run.started_at).getTime()) / 1000));
    }
    return run.remaining_seconds ?? 1;
  }, [run]);

  const progress = run.status === "IN_PROGRESS"
    ? Math.round(((totalSecs - remaining) / totalSecs) * 100)
    : 100;

  const claimMutation = useMutation({
    mutationFn: (id: number) => api.claimRun(id),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["current-run"] }),
        queryClient.invalidateQueries({ queryKey: ["character"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory"] }),
        queryClient.invalidateQueries({ queryKey: ["me"] }),
      ]);
    },
  });

  const waitingClaim = run.status === "SUCCESS_WAITING_CLAIM" || run.status === "FAILED_WAITING_CLAIM";
  const inProgress   = run.status === "IN_PROGRESS";
  const isSuccess    = run.result_preview?.is_success;
  const done         = waitingClaim;

  return (
    <div className="card active-strip animate-pulse-glow" style={{
      borderColor: done ? "var(--warning)" : "var(--primary)",
      marginBottom: 0,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "16px 20px", flexWrap: "wrap" }}>
        {/* Dungeon art placeholder */}
        <div style={{
          width: 90, height: 90, minWidth: 90, borderRadius: 10, flexShrink: 0,
          background: "linear-gradient(180deg, rgba(59,130,246,0.22), var(--bg-2)), repeating-linear-gradient(135deg, rgba(0,0,0,0.25) 0 6px, transparent 6px 12px)",
          border: "1px solid var(--line-soft)",
        }} />

        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="mono" style={{
            fontSize: 10, letterSpacing: "0.20em", textTransform: "uppercase",
            color: done ? "var(--warning)" : "var(--primary-bright)",
          }}>
            {done ? `◆ ${t("dungeons.activeReward")}` : `◷ ${t("dungeons.inProgress")}`}
          </div>
          <div style={{
            fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
            fontSize: 22, fontWeight: 600, letterSpacing: "0.04em",
            textTransform: "uppercase", marginTop: 2, color: "var(--bone)",
          }}>
            {run.location.name}
          </div>

          {inProgress && (
            <div style={{ marginTop: 10 }}>
              <div className="bar" style={{ height: 8 }}>
                <i style={{
                  width: `${progress}%`,
                  background: "linear-gradient(90deg, var(--primary-deep), var(--primary-bright))",
                  transition: "width 1s linear",
                }} />
              </div>
              <div className="mono" style={{
                fontSize: 11, color: "var(--text-mute)", marginTop: 6,
                display: "flex", justifyContent: "space-between",
              }}>
                <span>{t("dungeons.complete", { progress })}</span>
                <span style={{ color: "var(--bone)" }}>{t("dungeons.left", { time: formatTime(remaining) })}</span>
              </div>
            </div>
          )}

          {waitingClaim && run.result_preview && (
            <div style={{ marginTop: 10, display: "flex", gap: 12, flexWrap: "wrap" }}>
              <div style={{
                padding: "6px 12px", borderRadius: 8,
                background: isSuccess ? "rgba(34,197,94,0.12)" : "rgba(239,68,68,0.12)",
                border: `1px solid ${isSuccess ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
                fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)", fontSize: 12,
                color: isSuccess ? "var(--success)" : "var(--error)", fontWeight: 600,
              }}>
                {isSuccess ? t("dungeons.success") : t("dungeons.failed")}
              </div>
              <div style={{
                padding: "6px 12px", borderRadius: 8,
                background: "var(--bg-3)", border: "1px solid var(--line-soft)",
                fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)", fontSize: 12,
                color: "var(--primary-bright)",
              }}>
                +{run.result_preview.experience} XP
              </div>
              <div style={{
                padding: "6px 12px", borderRadius: 8,
                background: "var(--bg-3)", border: "1px solid var(--line-soft)",
                fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)", fontSize: 12,
                color: "var(--gold)",
              }}>
                +{run.result_preview.money_copper}c
              </div>
              {run.result_preview.items_count > 0 && (
                <div style={{
                  padding: "6px 12px", borderRadius: 8,
                  background: "rgba(168,85,247,0.12)", border: "1px solid rgba(168,85,247,0.3)",
                  fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)", fontSize: 12,
                  color: "#A855F7",
                }}>
                  {t("common.items", { count: run.result_preview.items_count })}
                </div>
              )}
            </div>
          )}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 8, flexShrink: 0 }}>
          {waitingClaim && (
            <button
              className="btn btn-primary"
              disabled={claimMutation.isPending}
              onClick={() => claimMutation.mutate(run.id)}
            >
              {claimMutation.isPending ? t("dungeons.claiming") : t("dungeons.claim")}
            </button>
          )}
          {inProgress && remaining === 0 && (
            <button
              className="btn"
              onClick={() => void queryClient.invalidateQueries({ queryKey: ["current-run"] })}
            >
              {t("dungeons.checkResult")}
            </button>
          )}
        </div>
      </div>
      <ErrorNotice message={(claimMutation.error as Error | null)?.message} />
    </div>
  );
}

/* ── Dungeon tier helpers ── */
const TIER_GRADIENT: Record<number, string> = {
  1: "linear-gradient(180deg, rgba(34,197,94,0.18), var(--bg-2)), repeating-linear-gradient(135deg, rgba(0,0,0,0.25) 0 6px, transparent 6px 12px)",
  2: "linear-gradient(180deg, rgba(59,130,246,0.22), var(--bg-2)), repeating-linear-gradient(135deg, rgba(0,0,0,0.25) 0 6px, transparent 6px 12px)",
  3: "linear-gradient(180deg, rgba(168,85,247,0.25), var(--bg-2)), repeating-linear-gradient(135deg, rgba(0,0,0,0.25) 0 6px, transparent 6px 12px)",
  4: "linear-gradient(180deg, rgba(245,158,11,0.28), var(--bg-2)), repeating-linear-gradient(135deg, rgba(0,0,0,0.25) 0 6px, transparent 6px 12px)",
};
function getTier(required_power: number) {
  if (required_power <= 50)  return 1;
  if (required_power <= 150) return 2;
  if (required_power <= 300) return 3;
  return 4;
}

/* ═══════════════════════════════════════
   DungeonsScreen
═══════════════════════════════════════ */
export function DungeonsScreen() {
  const queryClient   = useQueryClient();
  const { locale, t } = useI18n();
  const dungeonsQuery = useQuery({ queryKey: ["dungeons"],     queryFn: api.dungeons  });
  const currentRun    = useQuery({
    queryKey: ["current-run"],
    queryFn: api.currentRun,
    refetchInterval: (q) => q.state.data?.status === "IN_PROGRESS" ? 5000 : false,
  });

  const startMutation = useMutation({
    mutationFn: (id: number) => api.startRun(id),
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: ["current-run"] }),
  });

  const isRunning = currentRun.data?.status === "IN_PROGRESS";
  const hasRun    = Boolean(currentRun.data && currentRun.data.status !== "CLAIMED");

  return (
    <div className="col animate-fade-in">

      {/* Active run banner */}
      {hasRun && currentRun.data && <ActiveRunBanner run={currentRun.data} />}

      <ErrorNotice message={
        (dungeonsQuery.error as Error | null)?.message ??
        (startMutation.error as Error | null)?.message
      } />
      {dungeonsQuery.isLoading && <LoadingLine label={t("dungeons.loading")} />}

      {/* Dungeon card grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
        gap: 18,
      }}>
        {dungeonsQuery.data?.map((dungeon, idx) => {
          const tier       = getTier(dungeon.required_power);
          const isActive   = currentRun.data?.location?.id === dungeon.id && isRunning;
          const disabled   = isRunning || startMutation.isPending;
          const dungeonImage = bestMediaUrl(dungeon.media, ["large_url", "medium_url", "small_url", "icon_url", "original_url"]);

          const durLabel = formatDuration(dungeon.duration_seconds, locale);

          return (
            <div
              key={dungeon.id}
              className={`dungeon${isActive ? " active" : ""}`}
            >
              {/* Artwork placeholder */}
              <div style={{
                height: 130, position: "relative",
                background: dungeonImage ? undefined : TIER_GRADIENT[tier] ?? TIER_GRADIENT[1],
                borderBottom: "1px solid var(--line-soft)",
                display: "flex", alignItems: "flex-end", padding: 12,
                overflow: "hidden",
              }}>
                {dungeonImage && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={dungeonImage}
                    alt={dungeon.name}
                    style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
                  />
                )}
                <span style={{
                  position: "absolute", top: 10, right: 10,
                  fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)", fontSize: 10,
                  padding: "3px 8px", background: "var(--bg-1)",
                  border: "1px solid var(--line)", borderRadius: 2,
                  color: "var(--text-dim)", letterSpacing: "0.12em",
                }}>T{tier}</span>
                <span style={{
                  fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)", fontSize: 9,
                  letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--text-mute)",
                  background: "var(--bg-1)", padding: "3px 6px", borderRadius: 2,
                  zIndex: 1,
                }}>
                  {dungeon.name.toUpperCase()}
                </span>
              </div>

              {/* Body */}
              <div style={{
                padding: 16, display: "flex", flexDirection: "column",
                gap: 10, flex: 1,
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                  <h3 style={{
                    fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                    fontSize: 20, fontWeight: 600, margin: 0,
                    lineHeight: 1.2, letterSpacing: "0.03em",
                    textWrap: "balance" as React.CSSProperties["textWrap"],
                    minWidth: 0, flex: 1, color: "var(--bone)",
                  }}>
                    {dungeon.name}
                  </h3>
                  <span className="mono" style={{
                    fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.12em",
                    whiteSpace: "nowrap", paddingTop: 6, flexShrink: 0,
                  }}>
                    {t("common.power")} {dungeon.required_power}+
                  </span>
                </div>

                {dungeon.description && (
                  <p style={{
                    color: "var(--text-dim)", fontSize: 12, margin: 0, lineHeight: 1.5,
                    overflow: "hidden", display: "-webkit-box",
                    WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as React.CSSProperties["WebkitBoxOrient"],
                  }}>
                    {dungeon.description}
                  </p>
                )}

                <div style={{
                  display: "flex", gap: 14,
                  fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                  fontSize: 11, color: "var(--text-mute)",
                }}>
                  <span>⏱ <strong style={{ color: "var(--bone)", fontWeight: 500 }}>{durLabel}</strong></span>
                  <span>XP <strong style={{ color: "var(--bone)", fontWeight: 500 }}>{dungeon.rewards_preview?.experience?.max ?? "?"}</strong></span>
                  <span>◈ <strong style={{ color: "var(--bone)", fontWeight: 500 }}>{dungeon.rewards_preview?.money_copper?.max ?? "?"}</strong></span>
                  <span>{t("common.loot")} <strong style={{ color: "var(--success)", fontWeight: 500 }}>{dungeon.item_drop_chance}%</strong></span>
                </div>

                {/* CTA button */}
                <div style={{ marginTop: "auto", paddingTop: 4 }}>
                  <button
                    disabled={disabled}
                    onClick={() => !disabled && startMutation.mutate(dungeon.id)}
                    className="btn btn-primary"
                    style={{ width: "100%", opacity: isActive ? 0.7 : undefined }}
                  >
                    {startMutation.isPending ? t("dungeons.sending") : isActive ? t("dungeons.inProgressButton") : isRunning ? t("dungeons.heroBusy") : t("dungeons.sendHero")}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
