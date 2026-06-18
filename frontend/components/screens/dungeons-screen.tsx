"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ChevronRight, Coins, Flag, Info, LayoutGrid, List, MapPin, ShieldPlus, Sparkles, Sprout, Square, Swords, Zap } from "lucide-react";
import type React from "react";
import { useEffect, useMemo, useState } from "react";
import { AutoRunSummaryModal } from "@/components/auto-run-summary-modal";
import { canOpenMiniGame, DungeonMiniGameDifficultyModal, DungeonMiniGameModal, DungeonMiniGameResultModal } from "@/components/dungeon-mini-game-modal";
import { DungeonLootModal } from "@/components/dungeon-loot-modal";
import { DungeonResourceModal } from "@/components/dungeon-resource-modal";
import { useI18n } from "@/components/providers";
import { DungeonRewardModal } from "@/components/dungeon-reward-modal";
import { CopperDisplay, LoadingLine } from "@/components/ui";
import { api } from "@/lib/api";
import { resolveDungeonActionState, type DungeonActionContext, type DungeonBlockerCode } from "@/lib/dungeon-actions";
import { formatDuration, formatNumber, formatTime } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import { useIsMobile } from "@/lib/use-is-mobile";
import type { AutoRunState, ClaimResponse, CurrentRunResponse, Dungeon, DungeonMiniGameAttempt, DungeonRun } from "@/lib/types";

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

/* ── Active run banner ── */
function ActiveRunBanner({
  run,
  imageUrl,
  onClaimed,
}: {
  run: DungeonRun;
  imageUrl?: string;
  onClaimed: (result: ClaimResponse) => void;
}) {
  const queryClient = useQueryClient();
  const { t } = useI18n();
  const isMobile    = useIsMobile();
  const remaining   = useRemainingSeconds(run);
  const [miniGameAttempt, setMiniGameAttempt] = useState<DungeonMiniGameAttempt | null>(null);
  const [miniGameResult, setMiniGameResult] = useState<DungeonMiniGameAttempt | null>(null);
  const [choosingDifficulty, setChoosingDifficulty] = useState(false);

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
    onSuccess: async (result) => {
      onClaimed(result);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["current-run"] }),
        queryClient.invalidateQueries({ queryKey: ["character"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory"] }),
        queryClient.invalidateQueries({ queryKey: ["me"] }),
      ]);
    },
  });

  const startMiniGame = useMutation({
    mutationFn: (configId?: number) => api.startMiniGame(run.id, configId),
    onSuccess: (attempt) => {
      setChoosingDifficulty(false);
      setMiniGameAttempt(attempt);
    },
  });

  const waitingClaim = run.status === "SUCCESS_WAITING_CLAIM" || run.status === "FAILED_WAITING_CLAIM";
  const inProgress   = run.status === "IN_PROGRESS";
  const done         = waitingClaim;
  const canStartMiniGame = canOpenMiniGame(run);
  const hasActiveAttempt = Boolean(run.mini_game?.started && run.mini_game.status === "IN_PROGRESS");

  const handleSpeedUp = () => {
    if (hasActiveAttempt) {
      startMiniGame.mutate(undefined);
    } else {
      setChoosingDifficulty(true);
    }
  };

  useEffect(() => {
    if (inProgress && remaining === 0) {
      void queryClient.invalidateQueries({ queryKey: ["current-run"] });
    }
  }, [inProgress, queryClient, remaining]);

  const accent    = done ? "var(--warning)" : "var(--primary)";
  const accentRgb = done ? "245,158,11" : "59,130,246";

  const miniGameModals = (
    <>
      {choosingDifficulty && !miniGameAttempt && (
        <DungeonMiniGameDifficultyModal
          pending={startMiniGame.isPending}
          onClose={() => setChoosingDifficulty(false)}
          onSelect={(configId) => startMiniGame.mutate(configId)}
        />
      )}
      {miniGameAttempt && (
        <DungeonMiniGameModal
          attempt={miniGameAttempt}
          onClose={() => setMiniGameAttempt(null)}
          onFinished={(attempt) => {
            setMiniGameAttempt(null);
            setMiniGameResult(attempt);
            void queryClient.invalidateQueries({ queryKey: ["current-run"] });
          }}
        />
      )}
      {miniGameResult && (
        <DungeonMiniGameResultModal
          attempt={miniGameResult}
          onClose={() => setMiniGameResult(null)}
        />
      )}
    </>
  );

  if (isMobile) {
    return (
      <>
        <div style={{
          padding: 12, borderRadius: 16,
          background: "linear-gradient(135deg, rgba(59,130,246,0.14), rgba(22,30,49,0.5))",
          border: `1px solid ${accent}`,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
            <div style={{ width: 46, height: 46, minWidth: 46, borderRadius: 11, flexShrink: 0, overflow: "hidden", position: "relative", background: "linear-gradient(135deg,#2c3a5e,#19223a)" }}>
              {imageUrl && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={imageUrl} alt={run.location.name} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
              )}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="mono" style={{ fontSize: 8, letterSpacing: "0.18em", textTransform: "uppercase", color: done ? "var(--warning)" : "var(--primary-bright)" }}>
                {done ? t("dungeons.activeReward") : t("dungeons.inProgress")}
              </div>
              <div style={{ fontFamily: "var(--font-cinzel, 'Cinzel', serif)", fontWeight: 600, fontSize: 15, color: "#eef2f8", textTransform: "uppercase", letterSpacing: "0.04em", marginTop: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {run.location.name}
              </div>
            </div>
            {canStartMiniGame && (
              <button className="btn btn-primary" style={{ flexShrink: 0, padding: "9px 14px", fontSize: 12 }} disabled={startMiniGame.isPending} onClick={handleSpeedUp}>
                {startMiniGame.isPending ? t("miniGame.starting") : t("miniGame.speedUp")}
              </button>
            )}
            {waitingClaim && (
              <button className="btn btn-primary" style={{ flexShrink: 0, padding: "9px 14px", fontSize: 12 }} disabled={claimMutation.isPending} onClick={() => claimMutation.mutate(run.id)}>
                {claimMutation.isPending ? t("dungeons.claiming") : t("dungeons.claim")}
              </button>
            )}
          </div>
          {inProgress && (
            <>
              <div style={{ marginTop: 11, height: 7, borderRadius: 4, background: "rgba(8,11,20,0.7)", overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${progress}%`, borderRadius: 4, background: "linear-gradient(90deg, var(--primary-deep), var(--primary-bright))", transition: "width 1s linear" }} />
              </div>
              <div className="mono" style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 9, color: "#7c89a3" }}>
                <span>{t("dungeons.complete", { progress })}</span>
                <span>{t("dungeons.left", { time: formatTime(remaining) })}</span>
              </div>
            </>
          )}
        </div>
        {miniGameModals}
      </>
    );
  }

  return (
    <div className="card active-strip animate-pulse-glow" style={{
      borderColor: accent,
      marginBottom: 0,
      "--strip-accent": accent,
      "--strip-rgb": accentRgb,
      "--glow-rgb": accentRgb,
    } as React.CSSProperties}>
      <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "16px 20px", flexWrap: "wrap" }}>
        {/* Dungeon art */}
        <div style={{
          width: 90, height: 90, minWidth: 90, borderRadius: 10, flexShrink: 0,
          background: "var(--bg-3)",
          border: "1px solid var(--line-soft)",
          overflow: "hidden", position: "relative",
        }}>
          {imageUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imageUrl}
              alt={run.location.name}
              style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
            />
          )}
        </div>

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

        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 8, flexShrink: 0 }}>
          {canStartMiniGame && (
            <button
              className="btn btn-secondary"
              disabled={startMiniGame.isPending}
              onClick={handleSpeedUp}
            >
              <Zap size={16} />
              {startMiniGame.isPending ? t("miniGame.starting") : t("miniGame.speedUp")}
            </button>
          )}
          {waitingClaim && (
            <button
              className="btn btn-primary"
              disabled={claimMutation.isPending}
              onClick={() => claimMutation.mutate(run.id)}
            >
              {claimMutation.isPending ? t("dungeons.claiming") : t("dungeons.claim")}
            </button>
          )}
        </div>
      </div>
      {miniGameModals}
    </div>
  );
}

const ARMED_AUTO_STORAGE_KEY = "armedAutoLocationId";

function readArmedAutoLocationId() {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(ARMED_AUTO_STORAGE_KEY);
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function AutoRunStatusBlock({
  autoRun,
  run,
  pending,
  onStop,
}: {
  autoRun: AutoRunState;
  run: DungeonRun | null;
  pending: boolean;
  onStop: () => void;
}) {
  const { locale, t } = useI18n();
  const remaining = useRemainingSeconds(run);
  const locationName = run?.location.name || autoRun.current_dungeon?.name || autoRun.location.name;
  const statusLabel = autoRun.status === "STOPPING" ? t("autoRun.stopping") : t("autoRun.running");
  const stopReason = autoRun.stop_reason_message || autoRun.reason;
  const errorText = autoRun.error_message || autoRun.error;
  const totalSecs = useMemo(() => {
    if (run?.ends_at && run.started_at) {
      return Math.max(1, Math.ceil((new Date(run.ends_at).getTime() - new Date(run.started_at).getTime()) / 1000));
    }
    return Math.max(1, run?.remaining_seconds ?? 1);
  }, [run]);
  const progress = run?.status === "IN_PROGRESS"
    ? Math.max(0, Math.min(100, Math.round(((totalSecs - remaining) / totalSecs) * 100)))
    : 100;
  const showProgress = Boolean(run && run.status === "IN_PROGRESS");
  const metricCards: Array<{
    key: string;
    label: string;
    value: React.ReactNode;
    variant: "blue" | "green" | "red" | "cyan" | "violet" | "gold";
    icon: React.ReactNode;
  }> = [
    {
      key: "runs",
      label: t("autoRun.runs"),
      value: formatNumber(autoRun.runs_claimed, locale),
      variant: "blue",
      icon: <Flag size={28} strokeWidth={1.7} />,
    },
    {
      key: "successes",
      label: t("autoRun.successes"),
      value: formatNumber(autoRun.success_count, locale),
      variant: "green",
      icon: <CheckCircle2 size={30} strokeWidth={1.8} />,
    },
    {
      key: "failures",
      label: t("autoRun.failures"),
      value: formatNumber(autoRun.failure_count, locale),
      variant: "red",
      icon: <Swords size={29} strokeWidth={1.8} />,
    },
    {
      key: "hp",
      label: t("common.hp"),
      value: `${formatNumber(autoRun.current_hp, locale)} / ${formatNumber(autoRun.max_hp, locale)}`,
      variant: "cyan",
      icon: <ShieldPlus size={30} strokeWidth={1.8} />,
    },
    {
      key: "experience",
      label: t("reward.experience"),
      value: `+${formatNumber(autoRun.experience_total, locale)} ${t("common.xp")}`,
      variant: "violet",
      icon: <Sparkles size={30} strokeWidth={1.75} />,
    },
    {
      key: "money",
      label: t("reward.money"),
      value: <CopperDisplay value={autoRun.money_total_copper} locale={locale} compact={false} />,
      variant: "gold",
      icon: <Coins size={30} strokeWidth={1.8} />,
    },
  ];

  return (
    <section className="auto-run-panel" aria-label={statusLabel}>
      <div className="auto-run-panel-top" aria-hidden="true" />
      <div className="auto-run-panel-bottom" aria-hidden="true" />

      <div className="auto-run-state-head">
        <div className="auto-run-state-heading">
          <div className="mono auto-run-state-kicker">
            <Sparkles size={19} strokeWidth={1.8} />
            {statusLabel}
          </div>
          <div className="auto-run-state-title">{locationName}</div>
        </div>
        {showProgress && (
          <div className="auto-run-progress-block" aria-label={t("dungeons.inProgress")}>
            <div className="bar auto-run-progress-bar">
              <i style={{ width: `${progress}%` }} />
            </div>
            <div className="auto-run-progress-meta">
              <span>{t("dungeons.complete", { progress })}</span>
              <span>{t("dungeons.left", { time: formatTime(remaining) })}</span>
            </div>
          </div>
        )}
        <button
          type="button"
          className="auto-run-stop-btn"
          disabled={pending || autoRun.status === "STOPPING"}
          onClick={onStop}
        >
          <span className="auto-run-stop-icon" aria-hidden="true">
            <Square size={12} fill="currentColor" strokeWidth={1.5} />
          </span>
          {t("autoRun.stop")}
        </button>
      </div>

      <div className="auto-run-state-grid">
        {metricCards.map((card) => (
          <article key={card.key} className={`auto-run-stat-card auto-run-stat-card-${card.variant}`}>
            <div className="auto-run-stat-icon" aria-hidden="true">
              {card.icon}
            </div>
            <div className="auto-run-stat-copy">
              <div className="auto-run-stat-label">{card.label}</div>
              <div className={`auto-run-stat-value${card.key === "money" ? " auto-run-money-value" : ""}`}>
                {card.value}
              </div>
            </div>
          </article>
        ))}
      </div>

      {(stopReason || errorText) && (
        <div className="auto-run-state-notes">
          {stopReason && (
            <div className="auto-run-summary-note">
              <div className="card-sub">{t("autoRun.stopReason")}</div>
              <div className="auto-run-summary-note-body">{stopReason}</div>
            </div>
          )}
          {errorText && (
            <div className="auto-run-summary-note auto-run-summary-note-error">
              <div className="card-sub">{t("autoRun.error")}</div>
              <div className="auto-run-summary-note-body">{errorText}</div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

/* ── Dungeon tier helpers ── */
const TIER_GRADIENT: Record<number, string> = {
  1: "var(--bg-3)",
  2: "var(--bg-3)",
  3: "var(--bg-3)",
  4: "var(--bg-3)",
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
export function DungeonsScreen({
  onOpenInventory,
  onOpenConsumables,
}: {
  onOpenInventory?: () => void;
  onOpenConsumables?: () => void;
}) {
  const queryClient   = useQueryClient();
  const { locale, t } = useI18n();
  const isMobile = useIsMobile();
  const [rewardResult, setRewardResult] = useState<ClaimResponse | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list" | "map">("grid");
  // Mobile always renders the list view (comp); the grid/list/map switcher is desktop-only.
  const effectiveView = isMobile ? "list" : viewMode;
  const [category, setCategory] = useState<"dungeon" | "resource">("dungeon");
  const [lootDungeon, setLootDungeon] = useState<Dungeon | null>(null);
  const [resourceLocation, setResourceLocation] = useState<Dungeon | null>(null);
  const [armedAutoLocationId, setArmedAutoLocationId] = useState<number | null>(null);
  const [showAutoSummary, setShowAutoSummary] = useState(false);
  const dungeonsQuery = useQuery({ queryKey: ["dungeons"],     queryFn: api.dungeons  });
  const characterQuery = useQuery({ queryKey: ["character"],   queryFn: api.character });
  const currentRun = useQuery<CurrentRunResponse>({
    queryKey: ["current-run"],
    queryFn: api.currentRun,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.current_run?.status === "IN_PROGRESS") return 5000;
      if (data?.auto_run?.status === "ACTIVE" || data?.auto_run?.status === "STOPPING") return 5000;
      return false;
    },
  });

  const currentRunData = currentRun.data?.current_run ?? null;
  const autoRun = currentRun.data?.auto_run ?? null;
  const isRunning = currentRunData?.status === "IN_PROGRESS";
  const hasRun = Boolean(currentRunData && currentRunData.status !== "CLAIMED");
  const awaitingClaim = currentRunData?.status === "SUCCESS_WAITING_CLAIM" || currentRunData?.status === "FAILED_WAITING_CLAIM";
  const autoBlocksStarts = Boolean(autoRun && (autoRun.status === "ACTIVE" || autoRun.status === "STOPPING" || autoRun.summary_unread));

  const hpPercent = characterQuery.data?.stats?.hp_percent ?? 100;
  const hpTooLow  = hpPercent < 10;

  const combatDungeons = useMemo(
    () => dungeonsQuery.data?.filter((d) => d.location_type !== "resource") ?? [],
    [dungeonsQuery.data],
  );
  const resourceLocations = useMemo(
    () => dungeonsQuery.data?.filter((d) => d.location_type === "resource") ?? [],
    [dungeonsQuery.data],
  );

  const setArmedAuto = (locationId: number | null) => {
    setArmedAutoLocationId(locationId);
    if (typeof window === "undefined") return;
    if (locationId == null) {
      window.localStorage.removeItem(ARMED_AUTO_STORAGE_KEY);
      return;
    }
    window.localStorage.setItem(ARMED_AUTO_STORAGE_KEY, String(locationId));
  };

  useEffect(() => {
    setArmedAutoLocationId(readArmedAutoLocationId());
  }, []);

  useEffect(() => {
    if (hasRun || autoBlocksStarts) {
      setArmedAuto(null);
    }
  }, [autoBlocksStarts, hasRun]);

  useEffect(() => {
    if (!autoRun?.summary_unread) {
      setShowAutoSummary(false);
    }
  }, [autoRun?.summary_unread]);

  const startMutation = useMutation({
    mutationFn: ({ id, auto }: { id: number; auto: boolean }) => api.startRun(id, auto),
    onSuccess: () => {
      setArmedAuto(null);
    },
    onSettled: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["current-run"] }),
        queryClient.invalidateQueries({ queryKey: ["dungeons"] }),
      ]);
    },
  });

  const stopAutoRun = useMutation({
    mutationFn: api.stopAutoRun,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["current-run"] }),
        queryClient.invalidateQueries({ queryKey: ["dungeons"] }),
      ]);
    },
  });

  const readAutoSummary = useMutation({
    mutationFn: api.markAutoRunSummaryRead,
    onSuccess: async () => {
      setShowAutoSummary(false);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["current-run"] }),
        queryClient.invalidateQueries({ queryKey: ["dungeons"] }),
      ]);
    },
  });

  const activeLocationId = autoBlocksStarts
    ? autoRun?.location.id ?? currentRunData?.location.id ?? null
    : currentRunData?.location.id ?? null;
  const activeRunImage = currentRunData
    ? bestMediaUrl(
        dungeonsQuery.data?.find((dungeon) => dungeon.id === currentRunData.location.id)?.media,
        ["large_url", "medium_url", "small_url"],
      )
    : undefined;
  const autoStatusLabel = autoRun?.summary_unread
    ? t("autoRun.summaryTitle")
    : autoRun?.status === "STOPPING"
      ? t("autoRun.stopping")
      : autoRun?.status === "ACTIVE"
        ? autoRun.current_run_id
          ? t("autoRun.running")
          : t("autoRun.processing")
        : null;

  const getCurrentRunBlockerCode = (): DungeonBlockerCode => {
    if (autoRun?.status === "ACTIVE" || autoRun?.status === "STOPPING") return "auto_run_active";
    if (autoRun?.summary_unread) return "auto_run_summary_unread";
    if (awaitingClaim) return "unclaimed_run_exists";
    if (isRunning) return "active_run_exists";
    return null;
  };

  const dungeonActionContext: DungeonActionContext = {
    startPending: startMutation.isPending,
    currentRunBlockerCode: getCurrentRunBlockerCode(),
    activeLocationId,
    hpTooLow,
    labels: {
      sending: t("dungeons.sending"),
      autoRunning: autoStatusLabel ?? t("autoRun.running"),
      autoSummary: autoStatusLabel ?? t("autoRun.summaryTitle"),
      inProgress: t("dungeons.inProgressButton"),
      heroBusy: t("dungeons.heroBusy"),
      claimFirst: t("dungeons.claimFirst"),
      categoryLimitReached: t("dungeons.categoryLimitReached"),
      dailyLimitReached: t("dungeons.dailyLimitReached"),
      repairGear: t("dungeons.repairGear"),
      lowHp: t("dungeons.lowHp"),
      gather: t("dungeons.gather"),
      sendHero: t("dungeons.sendHero"),
    },
  };

  const renderAutoButton = (locationId: number, disabled: boolean, stretch = false) => {
    const armed = armedAutoLocationId === locationId;
    return (
      <button
        type="button"
        title={t("autoRun.tooltip")}
        aria-label={t("autoRun.tooltip")}
        aria-pressed={armed}
        data-tooltip={t("autoRun.tooltip")}
        disabled={disabled || hasRun || autoBlocksStarts}
        onClick={(event) => {
          event.stopPropagation();
          setArmedAuto(armed ? null : locationId);
        }}
        className={`btn btn-secondary auto-run-btn${armed ? " armed" : ""}${stretch ? " full" : ""}`}
      >
        <span>{armed ? t("autoRun.on") : t("autoRun.off")}</span>
        <span className="auto-run-btn-track" aria-hidden="true">
          <span className="auto-run-btn-dot" />
        </span>
      </button>
    );
  };

  const getLocationActionState = (location: Dungeon) => resolveDungeonActionState(location, dungeonActionContext);

  const closeDetails = () => {
    setLootDungeon(null);
    setResourceLocation(null);
  };

  const openLocationDetails = (location: Dungeon) => {
    if (location.location_type === "resource") {
      setResourceLocation(location);
      setLootDungeon(null);
      return;
    }
    setLootDungeon(location);
    setResourceLocation(null);
  };

  const handleLocationKeyDown = (event: React.KeyboardEvent<HTMLElement>, location: Dungeon) => {
    if (event.currentTarget !== event.target) return;
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    openLocationDetails(location);
  };

  const startLocationRun = (locationId: number, disabled: boolean) => {
    if (disabled) return;
    startMutation.mutate({ id: locationId, auto: armedAutoLocationId === locationId });
    closeDetails();
  };

  const renderPrimaryRunButton = (
    location: Dungeon,
    disabled: boolean,
    actionLabel: string,
    isActive: boolean,
    style?: React.CSSProperties,
  ) => (
    <button
      disabled={disabled}
      onClick={(event) => {
        event.stopPropagation();
        startLocationRun(location.id, disabled);
      }}
      className="btn btn-primary"
      style={{ opacity: isActive ? 0.7 : undefined, ...style }}
    >
      <Swords size={15} strokeWidth={1.9} />
      {actionLabel}
    </button>
  );

  const renderDetailActions = (location: Dungeon) => {
    const { actionLabel, disabled, isActive } = getLocationActionState(location);
    return (
      <div className="dungeon-detail-actions">
        {renderPrimaryRunButton(location, disabled, actionLabel, isActive, {
          minWidth: 170,
          minHeight: 40,
        })}
        {renderAutoButton(location.id, disabled)}
      </div>
    );
  };

  const showAutoStatusBlock = Boolean(autoRun && (autoRun.status === "ACTIVE" || autoRun.status === "STOPPING"));
  const showAutoSummaryPrompt = Boolean(autoRun?.summary_unread);
  const showManualRunBanner = Boolean(currentRunData && hasRun && !autoBlocksStarts);
  const detailsHint = effectiveView === "list" ? t("dungeons.tapRowDetails") : t("dungeons.tapCardDetails");

  return (
    <div className="col animate-fade-in">

      {/* Active run banner */}
      {showAutoStatusBlock && autoRun && (
        <AutoRunStatusBlock
          autoRun={autoRun}
          run={currentRunData}
          pending={stopAutoRun.isPending}
          onStop={() => stopAutoRun.mutate()}
        />
      )}
      {showAutoSummaryPrompt && autoRun && (
        <section className="auto-run-panel" aria-label={t("autoRun.summaryTitle")}>
          <div className="auto-run-panel-top" aria-hidden="true" />
          <div className="auto-run-panel-bottom" aria-hidden="true" />
          <div className="auto-run-state-head" style={{ marginBottom: 0 }}>
            <div className="auto-run-state-heading">
              <div className="mono auto-run-state-kicker">
                <Sparkles size={19} strokeWidth={1.8} />
                {t("autoRun.summaryTitle")}
              </div>
              <div className="auto-run-state-title">{autoRun.location.name}</div>
              <div className="card-sub" style={{ marginTop: 4 }}>{t("autoRun.summaryRequired")}</div>
            </div>
            <button
              type="button"
              className="btn btn-primary"
              disabled={readAutoSummary.isPending}
              onClick={() => setShowAutoSummary(true)}
            >
              {t("autoRun.viewSummary")}
            </button>
          </div>
        </section>
      )}
      {showManualRunBanner && currentRunData && (
        <ActiveRunBanner run={currentRunData} imageUrl={activeRunImage} onClaimed={setRewardResult} />
      )}

      {dungeonsQuery.isLoading && <LoadingLine label={t("dungeons.loading")} />}

      {/* Toolbar: category tabs (left) + view toggle (right) */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        {/* Category switcher */}
        <div style={{
          display: isMobile ? "grid" : "flex",
          gridTemplateColumns: isMobile ? "repeat(2, minmax(0, 1fr))" : undefined,
          width: isMobile ? "100%" : undefined,
          background: isMobile ? "transparent" : "rgba(255,255,255,0.05)",
          borderRadius: 10,
          border: isMobile ? "none" : "1px solid rgba(255,255,255,0.08)",
          padding: isMobile ? 0 : 3,
          gap: isMobile ? 8 : 2,
        }}>
          {(["dungeon", "resource"] as const).map((cat) => {
            const Icon = cat === "dungeon" ? Swords : Sprout;
            const active = category === cat;
            return (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                aria-label={cat === "dungeon" ? t("dungeons.categoryDungeons") : t("dungeons.categoryResources")}
                aria-pressed={active}
                style={{
                  width: isMobile ? "100%" : 34,
                  height: isMobile ? 42 : 34,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  gap: isMobile ? 8 : 0,
                  border: isMobile
                    ? active ? "1px solid rgba(96,165,250,0.72)" : "1px solid rgba(46,59,90,0.62)"
                    : "none",
                  borderRadius: isMobile ? 11 : 7,
                  cursor: "pointer",
                  background: active
                    ? isMobile ? "rgba(37,99,235,0.22)" : "var(--primary)"
                    : isMobile ? "rgba(17,24,39,0.55)" : "transparent",
                  color: active ? "#dbeafe" : "rgba(226,232,240,0.48)",
                  boxShadow: active && !isMobile ? "0 0 12px color-mix(in srgb, var(--primary) 60%, transparent)" : "none",
                  transition: "all 0.18s ease",
                }}
              >
                <Icon size={15} strokeWidth={active ? 2.2 : 1.8} />
                {isMobile && (
                  <span style={{ fontSize: 13, fontWeight: 700, lineHeight: 1 }}>
                    {cat === "dungeon" ? t("dungeons.categoryDungeons") : t("dungeons.gather")}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* View toggle — hidden on mobile (comp shows grid only) */}
        <div style={{
          display: isMobile ? "none" : "flex",
          background: "rgba(255,255,255,0.05)",
          borderRadius: 10,
          border: "1px solid rgba(255,255,255,0.08)",
          padding: 3,
          gap: 2,
        }}>
          {(["grid", "list", "map"] as const).map((mode) => {
            const Icon = mode === "grid" ? LayoutGrid : mode === "list" ? List : MapPin;
            const active = viewMode === mode;
            return (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                aria-label={mode}
                style={{
                  width: 34, height: 34,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  border: "none", borderRadius: 7, cursor: "pointer",
                  background: active ? "var(--primary)" : "transparent",
                  color: active ? "#fff" : "rgba(255,255,255,0.35)",
                  boxShadow: active ? "0 0 12px color-mix(in srgb, var(--primary) 60%, transparent)" : "none",
                  transition: "all 0.18s ease",
                }}
              >
                <Icon size={15} strokeWidth={active ? 2.2 : 1.8} />
              </button>
            );
          })}
        </div>
      </div>

      <div className="dungeon-detail-hint">
        <Info size={14} strokeWidth={1.8} />
        <span>{detailsHint}</span>
      </div>

      {/* Dungeon grid view */}
      {effectiveView === "grid" && category === "dungeon" && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 18,
        }}>
          {combatDungeons.map((dungeon) => {
            const tier       = getTier(dungeon.required_power);
            const { actionLabel, categoryExhausted, dailyRemaining, disabled, exhausted: localExhausted, isActive } = getLocationActionState(dungeon);
            const localRemaining = dailyRemaining;
            const dungeonImage = bestMediaUrl(dungeon.media, ["large_url", "medium_url", "small_url"]);
            const durLabel = formatDuration(dungeon.duration_seconds, locale);
            const isSelected = lootDungeon?.id === dungeon.id;

            return (
              <div
                key={dungeon.id}
                className={`dungeon${isActive ? " active" : ""}${isSelected ? " selected" : ""}`}
                role="button"
                tabIndex={0}
                aria-label={t("dungeons.openDetails", { name: dungeon.name })}
                onClick={() => openLocationDetails(dungeon)}
                onKeyDown={(event) => handleLocationKeyDown(event, dungeon)}
              >
                {/* Artwork */}
                <div style={{
                  aspectRatio: "1 / 1", position: "relative",
                  background: dungeonImage ? undefined : TIER_GRADIENT[tier] ?? TIER_GRADIENT[1],
                  borderBottom: "1px solid var(--line-soft)",
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
                </div>

                {/* Body */}
                <div style={{
                  padding: 16, display: "flex", flexDirection: "column",
                  gap: 10, flex: 1,
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                    <h3 style={{
                      fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                      fontSize: 23, fontWeight: 600, margin: 0,
                      lineHeight: 1.2, letterSpacing: "0.03em",
                      textWrap: "balance" as React.CSSProperties["textWrap"],
                      minWidth: 0, flex: 1, color: "var(--bone)",
                    }}>
                      {dungeon.name}
                    </h3>
                    <span className="mono" style={{
                      fontSize: 12, color: "var(--text-mute)", letterSpacing: "0.12em",
                      whiteSpace: "nowrap", paddingTop: 6, flexShrink: 0,
                    }}>
                      {t("common.power")} {dungeon.required_power}+
                    </span>
                  </div>

                  {dungeon.description && (
                    <p style={{
                      color: "var(--text-dim)", fontSize: 14, margin: 0, lineHeight: 1.5,
                      overflow: "hidden", display: "-webkit-box",
                      WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as React.CSSProperties["WebkitBoxOrient"],
                    }}>
                      {dungeon.description}
                    </p>
                  )}

                  <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 24 }}>
                    <div style={{
                      display: "flex", flexWrap: "wrap", gap: 14,
                      fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                      fontSize: 13, color: "var(--text-mute)",
                    }}>
                      <span>⏱ <strong style={{ color: "var(--bone)", fontWeight: 500 }}>{durLabel}</strong></span>
                      <span>XP <strong style={{ color: "var(--bone)", fontWeight: 500 }}>{dungeon.rewards_preview?.experience?.max ?? "?"}</strong></span>
                      <span>◈ <strong style={{ color: "var(--bone)", fontWeight: 500 }}>{dungeon.rewards_preview?.money_copper?.max ?? "?"}</strong></span>
                      <span>{t("common.loot")} <strong style={{ color: "var(--success)", fontWeight: 500 }}>{dungeon.item_drop_chance}%</strong></span>
                      {dungeon.daily_limit > 0 && (
                        <span style={{ color: localExhausted ? "var(--warning)" : "var(--text-mute)" }}>
                          {t("dungeons.dailyRuns", { used: dungeon.daily_limit - (localRemaining ?? 0), limit: dungeon.daily_limit })}
                        </span>
                      )}
                      {dungeon.limit_category.limit_count > 0 && (
                        <span style={{ color: categoryExhausted ? "var(--warning)" : "var(--text-mute)" }}>
                          {t("dungeons.categoryRuns", {
                            name: dungeon.limit_category.name,
                            used: dungeon.limit_category.used,
                            limit: dungeon.limit_category.limit_count,
                          })}
                        </span>
                      )}
                    </div>

                    {/* CTA buttons */}
                    <div style={{ display: "flex", gap: 8 }}>
                      {renderPrimaryRunButton(dungeon, disabled, actionLabel, isActive, { flex: 1 })}
                      {renderAutoButton(dungeon.id, disabled)}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Dungeon list view */}
      {effectiveView === "list" && category === "dungeon" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {combatDungeons.map((dungeon) => {
            const tier         = getTier(dungeon.required_power);
            const { actionLabel, categoryExhausted, dailyRemaining, disabled, exhausted: localExhausted, isActive } = getLocationActionState(dungeon);
            const localRemaining = dailyRemaining;
            const dungeonImage = bestMediaUrl(dungeon.media, ["small_url", "medium_url", "large_url"]);
            const durLabel     = formatDuration(dungeon.duration_seconds, locale);
            const isSelected = lootDungeon?.id === dungeon.id;

            if (isMobile) {
              return (
                <div
                  key={dungeon.id}
                  className={`dungeon${isActive ? " active" : ""}${isSelected ? " selected" : ""}`}
                  role="button"
                  tabIndex={0}
                  aria-label={t("dungeons.openDetails", { name: dungeon.name })}
                  onClick={() => openLocationDetails(dungeon)}
                  onKeyDown={(event) => handleLocationKeyDown(event, dungeon)}
                  style={{
                    minHeight: 96,
                    padding: 10,
                    borderRadius: 14,
                    overflow: "hidden",
                  }}
                >
                  <div style={{ display: "flex", gap: 11, alignItems: "stretch" }}>
                    <div style={{
                      width: 62, height: 62, minWidth: 62,
                      position: "relative",
                      background: dungeonImage ? undefined : TIER_GRADIENT[tier] ?? TIER_GRADIENT[1],
                      borderRadius: 10,
                      flexShrink: 0, overflow: "hidden",
                    }}>
                      {dungeonImage && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={dungeonImage}
                          alt={dungeon.name}
                          style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
                        />
                      )}
                    </div>

                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 6, minWidth: 0 }}>
                        <h3 style={{
                          fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                          fontSize: 14, fontWeight: 700, margin: 0,
                          lineHeight: 1.1, letterSpacing: 0, color: "var(--bone)",
                          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                          minWidth: 0,
                        }}>
                          {dungeon.name}
                        </h3>
                        <span className="mono" style={{
                          flexShrink: 0,
                          fontSize: 8, color: "var(--text-mute)", letterSpacing: 0,
                          whiteSpace: "nowrap",
                        }}>
                          {t("common.power")} {dungeon.required_power}+
                        </span>
                      </div>

                      <div style={{
                        marginTop: 5,
                        display: "flex", flexWrap: "wrap", gap: "3px 8px",
                        fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                        fontSize: 9, lineHeight: 1.25, color: "var(--text-mute)",
                      }}>
                        <span>⏱ {durLabel}</span>
                        <span>HP {dungeon.hp_loss_fail_percent}</span>
                        <span>◆ {dungeon.rewards_preview?.money_copper?.max ?? "?"}</span>
                        <span style={{ color: "var(--success)" }}>{t("common.loot")} {dungeon.item_drop_chance}%</span>
                      </div>

                      <div style={{
                        marginTop: 8,
                        display: "grid",
                        gridTemplateColumns: "minmax(0, 1fr) minmax(0, 0.9fr) 30px",
                        gap: 8,
                        alignItems: "center",
                      }}>
                        {renderPrimaryRunButton(dungeon, disabled, actionLabel, isActive, {
                            minHeight: 32, height: 32, padding: "0 10px",
                            borderRadius: 8, fontSize: 12, fontWeight: 700,
                            background: isActive
                              ? "linear-gradient(180deg, rgba(31,58,103,0.95), rgba(29,49,87,0.95))"
                              : disabled
                                ? "rgba(24,34,55,0.92)"
                              : undefined,
                            borderColor: isActive || disabled ? "rgba(96,165,250,0.18)" : undefined,
                            boxShadow: isActive || disabled ? "none" : undefined,
                            color: !isActive && disabled ? "rgba(148,163,184,0.72)" : undefined,
                            opacity: isActive || disabled ? 1 : undefined,
                          })}
                        {renderAutoButton(dungeon.id, disabled)}
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            openLocationDetails(dungeon);
                          }}
                          className="dungeon-detail-arrow"
                          aria-label={t("dungeons.openDetails", { name: dungeon.name })}
                        >
                          <ChevronRight size={18} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            }

            return (
              <div
                key={dungeon.id}
                className={`dungeon${isActive ? " active" : ""}${isSelected ? " selected" : ""}`}
                role="button"
                tabIndex={0}
                aria-label={t("dungeons.openDetails", { name: dungeon.name })}
                onClick={() => openLocationDetails(dungeon)}
                onKeyDown={(event) => handleLocationKeyDown(event, dungeon)}
                style={{ flexDirection: "row", minHeight: 99, overflow: "hidden" }}
              >
                {/* Zone 1 — thumbnail */}
                <div style={{
                  width: 140, minWidth: 140,
                  position: "relative",
                  background: dungeonImage ? undefined : TIER_GRADIENT[tier] ?? TIER_GRADIENT[1],
                  borderRight: "1px solid var(--line-soft)",
                  flexShrink: 0, overflow: "hidden",
                }}>
                  {dungeonImage && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={dungeonImage}
                      alt={dungeon.name}
                      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
                    />
                  )}
                  {/* Gradient fade on right edge to blend into content */}
                  <div style={{
                    position: "absolute", inset: 0,
                    background: "linear-gradient(to right, transparent 60%, color-mix(in srgb, var(--bg-2, #111) 70%, transparent))",
                    pointerEvents: "none",
                  }} />
                </div>

                {/* Zone 2 — main info */}
                <div style={{
                  flex: 1, minWidth: 0,
                  padding: "14px 18px",
                  display: "flex", flexDirection: "column",
                  justifyContent: "center", gap: 7,
                }}>
                  {/* Name row */}
                  <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                    <h3 style={{
                      fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                      fontSize: 18, fontWeight: 600, margin: 0,
                      letterSpacing: "0.03em", color: "var(--bone)",
                      overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                    }}>
                      {dungeon.name}
                    </h3>
                    {/* Power badge */}
                    <span className="mono" style={{
                      fontSize: 10, letterSpacing: "0.14em",
                      padding: "2px 8px", borderRadius: 4, flexShrink: 0,
                      background: "rgba(255,255,255,0.06)",
                      border: "1px solid rgba(255,255,255,0.1)",
                      color: "var(--text-mute)",
                    }}>
                      {t("common.power")} {dungeon.required_power}+
                    </span>
                  </div>

                  {/* Stats chips */}
                  <div style={{
                    display: "flex", flexWrap: "wrap", gap: "4px 16px",
                    fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                    fontSize: 12, color: "var(--text-mute)",
                  }}>
                    <span>⏱&thinsp;<strong style={{ color: "var(--bone)", fontWeight: 500 }}>{durLabel}</strong></span>
                    <span>XP&thinsp;<strong style={{ color: "var(--bone)", fontWeight: 500 }}>{dungeon.rewards_preview?.experience?.max ?? "?"}</strong></span>
                    <span>◈&thinsp;<strong style={{ color: "var(--bone)", fontWeight: 500 }}>{dungeon.rewards_preview?.money_copper?.max ?? "?"}</strong></span>
                    <span>{t("common.loot")}&thinsp;<strong style={{ color: "var(--success)", fontWeight: 500 }}>{dungeon.item_drop_chance}%</strong></span>
                    {dungeon.daily_limit > 0 && (
                      <span style={{ color: localExhausted ? "var(--warning)" : "var(--text-mute)" }}>
                        {t("dungeons.dailyRuns", { used: dungeon.daily_limit - (localRemaining ?? 0), limit: dungeon.daily_limit })}
                      </span>
                    )}
                    {dungeon.limit_category.limit_count > 0 && (
                      <span style={{ color: categoryExhausted ? "var(--warning)" : "var(--text-mute)" }}>
                        {t("dungeons.categoryRuns", {
                          name: dungeon.limit_category.name,
                          used: dungeon.limit_category.used,
                          limit: dungeon.limit_category.limit_count,
                        })}
                      </span>
                    )}
                  </div>
                  {dungeon.description && (
                    <p style={{
                      color: "var(--text-dim)", fontSize: 13, margin: 0, lineHeight: 1.45,
                      overflow: "hidden", display: "-webkit-box",
                      WebkitLineClamp: 1, WebkitBoxOrient: "vertical" as React.CSSProperties["WebkitBoxOrient"],
                    }}>
                      {dungeon.description}
                    </p>
                  )}
                </div>

                {/* Zone 3 — action */}
                <div style={{
                  width: 360, minWidth: 360, flexShrink: 0,
                  borderLeft: "1px solid var(--line-soft)",
                  display: "flex", flexDirection: "row",
                  alignItems: "center", justifyContent: "center",
                  gap: 12, padding: "12px 18px",
                }}>
                  {renderPrimaryRunButton(dungeon, disabled, actionLabel, isActive, {
                    minWidth: 142, minHeight: 44, height: "auto", fontSize: 13,
                    whiteSpace: "normal", lineHeight: 1.2, textAlign: "center",
                    paddingTop: 8, paddingBottom: 8,
                  })}
                  {renderAutoButton(dungeon.id, disabled)}
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      openLocationDetails(dungeon);
                    }}
                    className="dungeon-detail-arrow"
                    aria-label={t("dungeons.openDetails", { name: dungeon.name })}
                  >
                    <ChevronRight size={20} />
                  </button>
                  {isActive && (
                    <div style={{ width: 42 }}>
                      <div className="bar" style={{ height: 5 }}>
                        <i style={{
                          width: "100%",
                          background: "linear-gradient(90deg, var(--primary-deep), var(--primary-bright))",
                        }} />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Map view — coming soon */}
      {effectiveView === "map" && (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
          padding: "80px 24px", gap: 16,
          border: "1px dashed rgba(255,255,255,0.1)",
          borderRadius: 14,
          background: "rgba(255,255,255,0.02)",
        }}>
          <MapPin size={36} strokeWidth={1.2} style={{ color: "rgba(255,255,255,0.15)" }} />
          <span style={{ color: "rgba(255,255,255,0.25)", fontSize: 13, letterSpacing: "0.12em" }}
            className="mono">
            COMING SOON
          </span>
        </div>
      )}
      {/* Resource grid view */}
      {effectiveView === "grid" && category === "resource" && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 18,
        }}>
          {resourceLocations.map((location) => {
            const { actionLabel, categoryExhausted, dailyRemaining, disabled, exhausted, isActive } = getLocationActionState(location);
            const remaining   = dailyRemaining ?? location.daily_limit;
            const used        = location.daily_limit - remaining;
            const locationImage = bestMediaUrl(location.media, ["large_url", "medium_url", "small_url"]);
            const durLabel    = formatDuration(location.duration_seconds, locale);
            const isSelected = resourceLocation?.id === location.id;

            return (
              <div
                key={location.id}
                className={`dungeon${isActive ? " active" : ""}${isSelected ? " selected" : ""}`}
                role="button"
                tabIndex={0}
                aria-label={t("dungeons.openDetails", { name: location.name })}
                onClick={() => openLocationDetails(location)}
                onKeyDown={(event) => handleLocationKeyDown(event, location)}
              >
                <div style={{
                  aspectRatio: "1 / 1", position: "relative",
                  background: locationImage ? undefined : "var(--bg-3)",
                  borderBottom: "1px solid var(--line-soft)",
                  overflow: "hidden",
                }}>
                  {locationImage && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={locationImage}
                      alt={location.name}
                      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
                    />
                  )}
                </div>

                <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 10, flex: 1 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                    <h3 style={{
                      fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                      fontSize: 23, fontWeight: 600, margin: 0,
                      lineHeight: 1.2, letterSpacing: "0.03em",
                      minWidth: 0, flex: 1, color: "var(--bone)",
                    }}>
                      {location.name}
                    </h3>
                    <span className="mono" style={{
                      fontSize: 11, color: "var(--success)", letterSpacing: "0.10em",
                      whiteSpace: "nowrap", paddingTop: 8, flexShrink: 0,
                    }}>
                      {t("dungeons.guaranteedSuccess")}
                    </span>
                  </div>

                  {location.description && (
                    <p style={{
                      color: "var(--text-dim)", fontSize: 14, margin: 0, lineHeight: 1.5,
                      overflow: "hidden", display: "-webkit-box",
                      WebkitLineClamp: 2, WebkitBoxOrient: "vertical" as React.CSSProperties["WebkitBoxOrient"],
                    }}>
                      {location.description}
                    </p>
                  )}

                  <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 24 }}>
                    <div style={{
                      display: "flex", flexWrap: "wrap", gap: 14,
                      fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                      fontSize: 13, color: "var(--text-mute)",
                    }}>
                      <span>⏱ <strong style={{ color: "var(--bone)", fontWeight: 500 }}>{durLabel}</strong></span>
                      {location.daily_limit > 0 && (
                        <span style={{ color: exhausted ? "var(--warning)" : "var(--text-mute)" }}>
                          {t("dungeons.dailyRuns", { used, limit: location.daily_limit })}
                        </span>
                      )}
                      {location.limit_category.limit_count > 0 && (
                        <span style={{ color: categoryExhausted ? "var(--warning)" : "var(--text-mute)" }}>
                          {t("dungeons.categoryRuns", {
                            name: location.limit_category.name,
                            used: location.limit_category.used,
                            limit: location.limit_category.limit_count,
                          })}
                        </span>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: 8 }}>
                      {renderPrimaryRunButton(location, disabled, actionLabel, isActive, { flex: 1 })}
                      {renderAutoButton(location.id, disabled)}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Resource list view */}
      {effectiveView === "list" && category === "resource" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {resourceLocations.map((location) => {
            const { actionLabel, categoryExhausted, dailyRemaining, disabled, exhausted, isActive } = getLocationActionState(location);
            const remaining     = dailyRemaining ?? location.daily_limit;
            const used          = location.daily_limit - remaining;
            const locationImage = bestMediaUrl(location.media, ["small_url", "medium_url", "large_url"]);
            const durLabel      = formatDuration(location.duration_seconds, locale);
            const isSelected = resourceLocation?.id === location.id;

            if (isMobile) {
              return (
                <div
                  key={location.id}
                  className={`dungeon${isActive ? " active" : ""}${isSelected ? " selected" : ""}`}
                  role="button"
                  tabIndex={0}
                  aria-label={t("dungeons.openDetails", { name: location.name })}
                  onClick={() => openLocationDetails(location)}
                  onKeyDown={(event) => handleLocationKeyDown(event, location)}
                  style={{
                    minHeight: 96,
                    padding: 10,
                    borderRadius: 14,
                    overflow: "hidden",
                  }}
                >
                  <div style={{ display: "flex", gap: 11, alignItems: "stretch" }}>
                    <div style={{
                      width: 62, height: 62, minWidth: 62,
                      position: "relative",
                      background: locationImage ? undefined : "var(--bg-3)",
                      borderRadius: 10,
                      flexShrink: 0, overflow: "hidden",
                    }}>
                      {locationImage && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={locationImage}
                          alt={location.name}
                          style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
                        />
                      )}
                    </div>

                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 6, minWidth: 0 }}>
                        <h3 style={{
                          fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                          fontSize: 14, fontWeight: 700, margin: 0,
                          lineHeight: 1.1, letterSpacing: 0, color: "var(--bone)",
                          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                          minWidth: 0,
                        }}>
                          {location.name}
                        </h3>
                        <span className="mono" style={{
                          flexShrink: 0,
                          fontSize: 8, color: "var(--success)", letterSpacing: 0,
                          whiteSpace: "nowrap",
                        }}>
                          {t("dungeons.guaranteedSuccess")}
                        </span>
                      </div>

                      <div style={{
                        marginTop: 5,
                        display: "flex", flexWrap: "wrap", gap: "3px 8px",
                        fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                        fontSize: 9, lineHeight: 1.25, color: "var(--text-mute)",
                      }}>
                        <span>⏱ {durLabel}</span>
                        {location.daily_limit > 0 && (
                          <span style={{ color: exhausted ? "var(--warning)" : "var(--text-mute)" }}>
                            {t("dungeons.dailyRuns", { used, limit: location.daily_limit })}
                          </span>
                        )}
                      </div>

                      <div style={{
                        marginTop: 8,
                        display: "grid",
                        gridTemplateColumns: "minmax(0, 1fr) minmax(0, 0.9fr) 30px",
                        gap: 8,
                        alignItems: "center",
                      }}>
                        {renderPrimaryRunButton(location, disabled, actionLabel, isActive, {
                            minHeight: 32, height: 32, padding: "0 10px",
                            borderRadius: 8, fontSize: 12, fontWeight: 700,
                            background: isActive
                              ? "linear-gradient(180deg, rgba(31,58,103,0.95), rgba(29,49,87,0.95))"
                              : disabled
                                ? "rgba(24,34,55,0.92)"
                              : undefined,
                            borderColor: isActive || disabled ? "rgba(96,165,250,0.18)" : undefined,
                            boxShadow: isActive || disabled ? "none" : undefined,
                            color: !isActive && disabled ? "rgba(148,163,184,0.72)" : undefined,
                            opacity: isActive || disabled ? 1 : undefined,
                          })}
                        {renderAutoButton(location.id, disabled)}
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            openLocationDetails(location);
                          }}
                          className="dungeon-detail-arrow"
                          aria-label={t("dungeons.openDetails", { name: location.name })}
                        >
                          <ChevronRight size={18} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            }

            return (
              <div
                key={location.id}
                className={`dungeon${isActive ? " active" : ""}${isSelected ? " selected" : ""}`}
                role="button"
                tabIndex={0}
                aria-label={t("dungeons.openDetails", { name: location.name })}
                onClick={() => openLocationDetails(location)}
                onKeyDown={(event) => handleLocationKeyDown(event, location)}
                style={{ flexDirection: "row", minHeight: 99, overflow: "hidden" }}
              >
                {/* Zone 1 — thumbnail */}
                <div style={{
                  width: 140, minWidth: 140,
                  position: "relative",
                  background: locationImage ? undefined : "var(--bg-3)",
                  borderRight: "1px solid var(--line-soft)",
                  flexShrink: 0, overflow: "hidden",
                }}>
                  {locationImage && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={locationImage}
                      alt={location.name}
                      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
                    />
                  )}
                  <div style={{
                    position: "absolute", inset: 0,
                    background: "linear-gradient(to right, transparent 60%, color-mix(in srgb, var(--bg-2, #111) 70%, transparent))",
                    pointerEvents: "none",
                  }} />
                </div>

                {/* Zone 2 — main info */}
                <div style={{
                  flex: 1, minWidth: 0,
                  padding: "14px 18px",
                  display: "flex", flexDirection: "column",
                  justifyContent: "center", gap: 7,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                    <h3 style={{
                      fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                      fontSize: 18, fontWeight: 600, margin: 0,
                      letterSpacing: "0.03em", color: "var(--bone)",
                      overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                    }}>
                      {location.name}
                    </h3>
                    <span className="mono" style={{
                      fontSize: 10, letterSpacing: "0.12em",
                      padding: "2px 8px", borderRadius: 4, flexShrink: 0,
                      background: "rgba(34,197,94,0.10)",
                      border: "1px solid rgba(34,197,94,0.25)",
                      color: "var(--success)",
                    }}>
                      {t("dungeons.guaranteedSuccess")}
                    </span>
                  </div>

                  <div style={{
                    display: "flex", flexWrap: "wrap", gap: "4px 16px",
                    fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                    fontSize: 12, color: "var(--text-mute)",
                  }}>
                    <span>⏱&thinsp;<strong style={{ color: "var(--bone)", fontWeight: 500 }}>{durLabel}</strong></span>
                    {location.daily_limit > 0 && (
                      <span style={{ color: exhausted ? "var(--warning)" : "var(--text-mute)" }}>
                        {t("dungeons.dailyRuns", { used, limit: location.daily_limit })}
                      </span>
                    )}
                    {location.limit_category.limit_count > 0 && (
                      <span style={{ color: categoryExhausted ? "var(--warning)" : "var(--text-mute)" }}>
                        {t("dungeons.categoryRuns", {
                          name: location.limit_category.name,
                          used: location.limit_category.used,
                          limit: location.limit_category.limit_count,
                        })}
                      </span>
                    )}
                  </div>
                  {location.description && (
                    <p style={{
                      color: "var(--text-dim)", fontSize: 13, margin: 0, lineHeight: 1.45,
                      overflow: "hidden", display: "-webkit-box",
                      WebkitLineClamp: 1, WebkitBoxOrient: "vertical" as React.CSSProperties["WebkitBoxOrient"],
                    }}>
                      {location.description}
                    </p>
                  )}
                </div>

                {/* Zone 3 — action */}
                <div style={{
                  width: 360, minWidth: 360, flexShrink: 0,
                  borderLeft: "1px solid var(--line-soft)",
                  display: "flex", flexDirection: "row",
                  alignItems: "center", justifyContent: "center",
                  gap: 12, padding: "12px 18px",
                }}>
                  {renderPrimaryRunButton(location, disabled, actionLabel, isActive, {
                    minWidth: 142, minHeight: 44, height: "auto", fontSize: 13,
                    whiteSpace: "normal", lineHeight: 1.2, textAlign: "center",
                    paddingTop: 8, paddingBottom: 8,
                  })}
                  {renderAutoButton(location.id, disabled)}
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      openLocationDetails(location);
                    }}
                    className="dungeon-detail-arrow"
                    aria-label={t("dungeons.openDetails", { name: location.name })}
                  >
                    <ChevronRight size={20} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showAutoSummary && autoRun?.summary_unread && (
        <AutoRunSummaryModal
          autoRun={autoRun}
          pending={readAutoSummary.isPending}
          onAcknowledge={() => readAutoSummary.mutate()}
          onOpenInventory={onOpenInventory}
          onOpenConsumables={onOpenConsumables}
        />
      )}

      {rewardResult && (
        <DungeonRewardModal
          result={rewardResult}
          onClose={() => setRewardResult(null)}
        />
      )}
      {lootDungeon && (
        <DungeonLootModal
          dungeon={lootDungeon}
          onClose={() => setLootDungeon(null)}
          actions={renderDetailActions(lootDungeon)}
        />
      )}
      {resourceLocation && (
        <DungeonResourceModal
          location={resourceLocation}
          onClose={() => setResourceLocation(null)}
          actions={renderDetailActions(resourceLocation)}
        />
      )}
    </div>
  );
}
