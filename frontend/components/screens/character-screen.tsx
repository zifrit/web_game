"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type DragEvent } from "react";
import { createPortal } from "react-dom";
import { useMutation, useQuery, useQueryClient, type InfiniteData } from "@tanstack/react-query";
import { CircleHelp, Zap } from "lucide-react";
import { canOpenMiniGame, DungeonMiniGameDifficultyModal, DungeonMiniGameModal, DungeonMiniGameResultModal } from "@/components/dungeon-mini-game-modal";
import { useI18n } from "@/components/providers";
import { DungeonRewardModal } from "@/components/dungeon-reward-modal";
import { CharacterScreenSkeleton, ErrorNotice, LoadingLine } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDuration, type Locale, type TranslationKey } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import type { Character, ClaimResponse, Dungeon, DungeonMiniGameAttempt, EquipmentSlot, Inventory, InventoryCard, InventoryMutationResponse } from "@/lib/types";

/* ── Rarity helpers ── */
const RARITY_COLOR: Record<string, string> = {
  f: "#94A3B8",
  e: "#22C55E",
  d: "#38BDF8",
  c: "#3B82F6",
  b: "#A855F7",
  a: "#F59E0B",
  s: "#EF4444",
  ex:"#F8FAFC",
};
const RARITY_GLOW: Record<string, string> = {
  f: "rgba(148,163,184,0.25)",
  e: "rgba(34,197,94,0.30)",
  d: "rgba(56,189,248,0.32)",
  c: "rgba(59,130,246,0.35)",
  b: "rgba(168,85,247,0.35)",
  a: "rgba(245,158,11,0.35)",
  s: "rgba(239,68,68,0.35)",
  ex:"rgba(248,250,252,0.35)",
};
function rc(rarity?: string) { return RARITY_COLOR[(rarity ?? "f").toLowerCase()] ?? RARITY_COLOR.f; }
function rg(rarity?: string) { return RARITY_GLOW[(rarity ?? "f").toLowerCase()]  ?? RARITY_GLOW.f;  }

function setStableDragImage(event: DragEvent<HTMLDivElement>) {
  const node = event.currentTarget;
  const rect = node.getBoundingClientRect();
  const ghost = node.cloneNode(true) as HTMLElement;

  ghost.style.position = "fixed";
  ghost.style.top = "-1000px";
  ghost.style.left = "-1000px";
  ghost.style.width = `${rect.width}px`;
  ghost.style.height = `${rect.height}px`;
  ghost.style.pointerEvents = "none";
  ghost.style.opacity = "0.95";
  ghost.style.transform = "translateZ(0)";
  ghost.style.zIndex = "-1";

  document.body.appendChild(ghost);
  event.dataTransfer.setDragImage(ghost, rect.width / 2, rect.height / 2);
  window.setTimeout(() => ghost.remove(), 0);
}

const EQUIPMENT_SLOTS: Array<{
  slot: EquipmentSlot;
  label: TranslationKey;
  glyph: string;
  row: "top" | "bottom";
}> = [
  { slot: "helmet", label: "slot.helmet", glyph: "H", row: "top" },
  { slot: "armor", label: "slot.armor", glyph: "A", row: "top" },
  { slot: "weapon", label: "slot.weapon", glyph: "W", row: "bottom" },
  { slot: "ring", label: "slot.ring", glyph: "R", row: "bottom" },
  { slot: "boots", label: "slot.boots", glyph: "B", row: "bottom" },
];
const INVENTORY_PAGE_SIZE = 24;

type DragState = {
  item: InventoryCard;
  source: "inventory" | "equipment";
};

function addUniqueItem(items: InventoryCard[], item: InventoryCard) {
  return items.some((candidate) => candidate.id === item.id) ? items : [...items, item];
}

function mergeInventoryMutation(data: Inventory, result: InventoryMutationResponse) {
  const items = addUniqueItem(data.items, result.item);
  const withReplacement = result.replaced_item ? addUniqueItem(items, result.replaced_item) : items;
  return {
    ...data,
    equipment_summary: result.equipment_summary,
    equipped: result.equipment,
    items: withReplacement,
  };
}

function mergeInfiniteInventoryMutation(data: InfiniteData<Inventory>, result: InventoryMutationResponse) {
  return {
    ...data,
    pages: data.pages.map((page) => mergeInventoryMutation(page, result)),
  };
}

function packItemCount(items: InventoryCard[], equipment: InventoryMutationResponse["equipment"]) {
  const equippedIds = new Set(
    Object.values(equipment)
      .map((item) => item?.id)
      .filter((id): id is number => typeof id === "number")
  );
  return items.filter((item) => !equippedIds.has(item.id)).length;
}

/* ── Equipment Slot Cell ── */
function SlotCell({
  label,
  glyph,
  rarity,
  iconUrl,
  broken,
  durability,
  canDrop,
  dropActive,
  draggable,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDragLeave,
  onDrop,
}: {
  label: string;
  glyph: string;
  rarity?: string;
  iconUrl?: string;
  broken?: boolean;
  durability?: InventoryCard["durability"];
  canDrop?: boolean;
  dropActive?: boolean;
  draggable?: boolean;
  onDragStart?: (event: DragEvent<HTMLDivElement>) => void;
  onDragEnd?: () => void;
  onDragOver?: (event: DragEvent<HTMLDivElement>) => void;
  onDragLeave?: () => void;
  onDrop?: (event: DragEvent<HTMLDivElement>) => void;
}) {
  const color   = rarity ? rc(rarity) : undefined;
  const hasItem = Boolean(rarity);

  return (
    <div
      className={`slot${hasItem ? " filled" : ""}${draggable ? " draggable" : ""}${dropActive ? (canDrop ? " drop-ok" : " drop-blocked") : ""}`}
      draggable={draggable}
      onDragEnd={onDragEnd}
      onDragLeave={onDragLeave}
      onDragOver={onDragOver}
      onDragStart={onDragStart}
      onDrop={onDrop}
      style={hasItem && !dropActive ? {
        borderColor: color + "80",
        boxShadow: `0 0 14px ${rg(rarity)}`,
      } : {}}
    >
      {hasItem && (
        <>
          {iconUrl && (
            <img
              src={iconUrl}
              alt={label}
              loading="eager"
              decoding="async"
              draggable={false}
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                objectFit: "cover",
                backfaceVisibility: "hidden",
                pointerEvents: "none",
                transform: "translateZ(0)",
              }}
            />
          )}
          <div className="slot-rare" style={{ background: color }} />
          {durability && (
            <span className="slot-durability-number">
              {durability.current}/{durability.max}
            </span>
          )}
        </>
      )}
      <span className="slot-glyph" style={{ color: hasItem ? (color ?? "var(--text)") : "var(--text-mute)" }}>
        {glyph}
      </span>
      <span className="slot-name">{label}</span>
      {broken && (
        <div style={{
          position: "absolute", inset: 0, background: "rgba(239,68,68,0.12)",
          display: "flex", alignItems: "center", justifyContent: "center",
          borderRadius: 10,
        }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: "#EF4444" }}>!</span>
        </div>
      )}
    </div>
  );
}

/* ── Inventory mini cell ── */
function InvCell({
  item,
  onDragStart,
  onDragEnd,
}: {
  item?: InventoryCard;
  onDragStart?: (item: InventoryCard, event: DragEvent<HTMLDivElement>) => void;
  onDragEnd?: () => void;
}) {
  const rarity = item?.rarity;
  const broken = item?.is_broken;
  const color   = rarity ? rc(rarity) : undefined;
  const hasItem = Boolean(rarity);
  const iconUrl = bestMediaUrl(item?.media, ["small_url", "medium_url", "large_url"]);
  const itemName = item?.name ?? "";
  return (
    <div
      className={`inv-cell${hasItem ? "" : " empty"}${hasItem && !broken ? " draggable" : ""}`}
      draggable={Boolean(item && !broken)}
      onDragEnd={onDragEnd}
      onDragStart={item && !broken ? (event) => onDragStart?.(item, event) : undefined}
      style={hasItem ? { borderColor: color, boxShadow: `inset 0 0 14px ${rg(rarity)}` } : {}}
      title={item ? `${item.slot} item #${item.id}` : undefined}
    >
      {hasItem && (
        iconUrl ? (
          <img
            src={iconUrl}
            alt={itemName}
            className="inv-icon"
            loading="eager"
            decoding="async"
            draggable={false}
          />
        ) : (
          <div className="inv-icon" />
        )
      )}
      {hasItem && broken && <div className="broken-tag">!</div>}
    </div>
  );
}

/* ── Quick expedition row ── */
function QuickDungeonRow({
  dungeon, canRun, onRun, isPending, locale, runLabel,
}: {
  dungeon: Pick<Dungeon, "id" | "name" | "required_power" | "duration_seconds" | "item_drop_chance" | "rewards_preview" | "media">;
  canRun: boolean;
  onRun: (id: number) => void;
  isPending: boolean;
  locale: Locale;
  runLabel: string;
}) {
  // Derive a tier (1–4) from required_power for the artwork gradient
  const tier = dungeon.required_power <= 50 ? 1 : dungeon.required_power <= 150 ? 2 : dungeon.required_power <= 300 ? 3 : 4;
  const artGradients: Record<number, string> = {
    1: "linear-gradient(135deg, rgba(34,197,94,0.30), var(--bg-2))",
    2: "linear-gradient(135deg, rgba(59,130,246,0.30), var(--bg-2))",
    3: "linear-gradient(135deg, rgba(168,85,247,0.32), var(--bg-2))",
    4: "linear-gradient(135deg, rgba(245,158,11,0.35), var(--bg-2))",
  };

  const durLabel = formatDuration(dungeon.duration_seconds, locale);
  const dungeonImage = bestMediaUrl(dungeon.media, ["small_url", "medium_url", "large_url"]);

  return (
    <div className="quick-d" onClick={() => canRun && !isPending && onRun(dungeon.id)}>
      <div className="quick-d-art" style={{ background: dungeonImage ? undefined : artGradients[tier], overflow: "hidden", position: "relative" }}>
        {dungeonImage && (
          <img
            src={dungeonImage}
            alt={dungeon.name}
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
          />
        )}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
          fontSize: 15, fontWeight: 600, letterSpacing: "0.04em", textTransform: "uppercase",
          color: "var(--bone)",
        }}>{dungeon.name}</div>
        <div className="mono" style={{ fontSize: 11, color: "var(--text-mute)", marginTop: 4 }}>
          PWR {dungeon.required_power}+ · {durLabel} · {dungeon.rewards_preview?.experience?.max ?? "?"} XP · Loot {dungeon.item_drop_chance}%
        </div>
      </div>
      <button
        className="btn btn-primary"
        disabled={!canRun || isPending}
        style={{ padding: "8px 14px", fontSize: 13 }}
        onClick={(e) => { e.stopPropagation(); if (canRun && !isPending) onRun(dungeon.id); }}
      >
        {isPending ? "…" : runLabel}
      </button>
    </div>
  );
}

/* ── Bar block ── */
function BarBlock({ label, cur, max, kind }: { label: string; cur: number; max: number; kind: "xp" | "hp" }) {
  const pct = Math.min(1, cur / Math.max(1, max));
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6, gap: 8 }}>
        <span className="mono" style={{ fontSize: 10, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--text-mute)", whiteSpace: "nowrap" }}>
          {label}
        </span>
        <span className="mono" style={{ fontSize: 11, color: "var(--bone)", whiteSpace: "nowrap" }}>
          {cur} / {max}
        </span>
      </div>
      <div className={`bar ${kind}`} style={{ height: 8 }}>
        <i style={{ width: `${pct * 100}%` }} />
      </div>
    </div>
  );
}

const POWER_WEIGHTS = {
  attack: 2,
  defense: 1.7,
  health: 0.25,
  critical_chance: 1,
  evasion: 1,
} as const;

function PowerHelp({ stats, power }: { stats: Character["stats"]; power: number }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [placement, setPlacement] = useState<"top" | "right" | "bottom" | "left">("bottom");
  const [popoverPosition, setPopoverPosition] = useState({
    left: 0,
    top: 0,
    arrowLeft: 0,
    arrowTop: 0,
    ready: false,
  });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLSpanElement>(null);
  const rows = [
    { key: "attack", label: t("common.attack"), value: stats?.attack ?? 0, weight: POWER_WEIGHTS.attack },
    { key: "defense", label: t("common.defense"), value: stats?.defense ?? 0, weight: POWER_WEIGHTS.defense },
    { key: "health", label: t("common.health"), value: stats?.health ?? 0, weight: POWER_WEIGHTS.health },
    { key: "critical_chance", label: t("common.crit"), value: stats?.critical_chance ?? 0, weight: POWER_WEIGHTS.critical_chance },
    { key: "evasion", label: t("common.evasion"), value: stats?.evasion ?? 0, weight: POWER_WEIGHTS.evasion },
  ];

  const updatePopoverPosition = useCallback(() => {
    const button = buttonRef.current;
    const popover = popoverRef.current;
    if (!button || !popover) return;

    const margin = 12;
    const gap = 12;
    const trigger = button.getBoundingClientRect();
    const { width, height } = popover.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const space = {
      top: trigger.top - margin,
      right: viewportWidth - trigger.right - margin,
      bottom: viewportHeight - trigger.bottom - margin,
      left: trigger.left - margin,
    };
    const fits = {
      bottom: space.bottom >= height + gap,
      top: space.top >= height + gap,
      right: space.right >= width + gap,
      left: space.left >= width + gap,
    };
    const nextPlacement =
      (fits.bottom && "bottom") ||
      (fits.top && "top") ||
      (fits.right && "right") ||
      (fits.left && "left") ||
      (Object.entries(space).sort((a, b) => b[1] - a[1])[0][0] as "top" | "right" | "bottom" | "left");

    const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(value, max));
    const centeredLeft = trigger.left + trigger.width / 2 - width / 2;
    const centeredTop = trigger.top + trigger.height / 2 - height / 2;
    const maxLeft = Math.max(margin, viewportWidth - width - margin);
    const maxTop = Math.max(margin, viewportHeight - height - margin);
    const positionByPlacement = {
      bottom: {
        left: clamp(centeredLeft, margin, maxLeft),
        top: clamp(trigger.bottom + gap, margin, maxTop),
      },
      top: {
        left: clamp(centeredLeft, margin, maxLeft),
        top: clamp(trigger.top - height - gap, margin, maxTop),
      },
      right: {
        left: clamp(trigger.right + gap, margin, maxLeft),
        top: clamp(centeredTop, margin, maxTop),
      },
      left: {
        left: clamp(trigger.left - width - gap, margin, maxLeft),
        top: clamp(centeredTop, margin, maxTop),
      },
    };
    const nextPosition = positionByPlacement[nextPlacement];
    const arrowInset = 14;
    const triggerCenterX = trigger.left + trigger.width / 2;
    const triggerCenterY = trigger.top + trigger.height / 2;
    const arrowLeft = clamp(triggerCenterX - nextPosition.left, arrowInset, width - arrowInset);
    const arrowTop = clamp(triggerCenterY - nextPosition.top, arrowInset, height - arrowInset);

    setPlacement(nextPlacement);
    setPopoverPosition({ ...nextPosition, arrowLeft, arrowTop, ready: true });
  }, []);

  useEffect(() => {
    setMounted(true);
  }, []);

  useLayoutEffect(() => {
    if (!open) return;
    updatePopoverPosition();
  }, [open, updatePopoverPosition]);

  useEffect(() => {
    if (!open) return;
    window.addEventListener("resize", updatePopoverPosition);
    window.addEventListener("scroll", updatePopoverPosition, true);
    return () => {
      window.removeEventListener("resize", updatePopoverPosition);
      window.removeEventListener("scroll", updatePopoverPosition, true);
    };
  }, [open, updatePopoverPosition]);

  const popover = mounted && open ? createPortal(
    <span
      ref={popoverRef}
      className={`power-help-popover open${popoverPosition.ready ? " positioned" : ""}`}
      data-placement={placement}
      role="tooltip"
      style={{
        left: popoverPosition.left,
        top: popoverPosition.top,
        "--power-help-arrow-left": `${popoverPosition.arrowLeft}px`,
        "--power-help-arrow-top": `${popoverPosition.arrowTop}px`,
      } as CSSProperties}
    >
      <strong>{t("powerHelp.title")}</strong>
      <span className="power-help-formula">{t("powerHelp.formula")}</span>
      {rows.map((row) => (
        <span key={row.key} className="power-help-row">
          <span>{row.label}</span>
          <span>{row.value} x {row.weight} = {(row.value * row.weight).toFixed(2)}</span>
        </span>
      ))}
      <span className="power-help-total">{t("powerHelp.total", { value: power.toFixed(2) })}</span>
    </span>,
    document.body
  ) : null;

  return (
    <>
      <span
        className={`power-help${open ? " open" : ""}`}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => {
          if (!pinned) setOpen(false);
        }}
        onFocus={() => setOpen(true)}
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) {
            setPinned(false);
            setOpen(false);
          }
        }}
      >
        <button
          ref={buttonRef}
          type="button"
          className="power-help-btn"
          aria-label={t("powerHelp.title")}
          aria-expanded={open}
          onClick={() => {
            setPinned((current) => {
              setOpen(!current);
              return !current;
            });
          }}
        >
          <CircleHelp size={14} strokeWidth={2} />
        </button>
      </span>
      {popover}
    </>
  );
}

/* ── Active expedition strip ── */
function ActiveExpeditionStrip({ run, imageUrl, onClaimed, onSpeedUp, speedUpPending }: {
  run: NonNullable<Awaited<ReturnType<typeof api.currentRun>>>;
  imageUrl?: string;
  onClaimed: (result: ClaimResponse) => void;
  onSpeedUp: () => void;
  speedUpPending: boolean;
}) {
  const queryClient = useQueryClient();
  const { t } = useI18n();
  const [localNow, setLocalNow] = useState(Date.now());

  useEffect(() => {
    if (run.status !== "IN_PROGRESS") return;
    const t = window.setInterval(() => setLocalNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [run.status]);

  const claimMut = useMutation({
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

  const waitingClaim = run.status === "SUCCESS_WAITING_CLAIM" || run.status === "FAILED_WAITING_CLAIM";
  const inProgress   = run.status === "IN_PROGRESS";
  const canStartMiniGame = canOpenMiniGame(run);

  let remaining  = 0;
  let totalSecs  = 1;
  let progress   = 0;

  if (inProgress && run.ends_at) {
    totalSecs = run.started_at
      ? Math.max(1, Math.ceil((new Date(run.ends_at).getTime() - new Date(run.started_at).getTime()) / 1000))
      : (run.remaining_seconds ?? 60);
    remaining = Math.max(0, Math.ceil((new Date(run.ends_at).getTime() - localNow) / 1000));
    progress  = Math.min(1, (totalSecs - remaining) / totalSecs);
  } else if (waitingClaim) {
    progress = 1;
  }

  const mins = Math.floor(remaining / 60);
  const secs = remaining % 60;
  const timeLabel = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;

  const done = waitingClaim;

  useEffect(() => {
    if (inProgress && remaining === 0) {
      void queryClient.invalidateQueries({ queryKey: ["current-run"] });
    }
  }, [inProgress, queryClient, remaining]);

  return (
    <div className="card active-strip" style={{
      borderColor: done ? "var(--warning)" : "var(--primary)",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "16px 20px" }}>
        <div style={{
          width: 90, height: 90, minWidth: 90, borderRadius: 10,
          background: "var(--bg-3)",
          border: "1px solid var(--line-soft)",
          flexShrink: 0, overflow: "hidden", position: "relative",
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
          <div style={{ marginTop: 10 }}>
            <div className="bar" style={{ height: 8 }}>
              <i style={{
                width: `${progress * 100}%`,
                background: done ? "var(--warning)" : "linear-gradient(90deg, var(--primary-deep), var(--primary-bright))",
                transition: "width 1s linear",
              }} />
            </div>
            <div className="mono" style={{
              fontSize: 11, color: "var(--text-mute)", marginTop: 6,
              display: "flex", justifyContent: "space-between",
            }}>
              <span>{t("dungeons.complete", { progress: Math.round(progress * 100) })}</span>
              {inProgress && <span style={{ color: "var(--bone)" }}>{t("dungeons.left", { time: timeLabel })}</span>}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, flexShrink: 0 }}>
          {canStartMiniGame && (
            <button
              className="btn btn-secondary"
              disabled={speedUpPending}
              onClick={onSpeedUp}
            >
              <Zap size={16} />
              {speedUpPending ? t("miniGame.starting") : t("miniGame.speedUp")}
            </button>
          )}
          {done && (
            <button
              className="btn btn-primary"
              onClick={() => claimMut.mutate(run.id)}
              disabled={claimMut.isPending}
            >
              {claimMut.isPending ? t("dungeons.claiming") : t("dungeons.claim")}
            </button>
          )}
        </div>
      </div>
      <ErrorNotice message={(claimMut.error as Error | null)?.message} />
    </div>
  );
}

/* ═══════════════════════════════════════
   CharacterScreen
═══════════════════════════════════════ */
export function CharacterScreen({
  onOpenDungeons,
  onOpenInventory,
}: {
  onOpenDungeons?: () => void;
  onOpenInventory?: () => void;
}) {
  const queryClient = useQueryClient();
  const { locale, t } = useI18n();
  const [dragState, setDragState] = useState<DragState | null>(null);
  const [dragOverSlot, setDragOverSlot] = useState<EquipmentSlot | null>(null);
  const [inventoryDropActive, setInventoryDropActive] = useState(false);
  const [dropError, setDropError] = useState<string | null>(null);
  const [rewardResult, setRewardResult] = useState<ClaimResponse | null>(null);
  const [miniGameAttempt, setMiniGameAttempt] = useState<DungeonMiniGameAttempt | null>(null);
  const [miniGameResult, setMiniGameResult] = useState<DungeonMiniGameAttempt | null>(null);
  const [choosingDifficulty, setChoosingDifficulty] = useState(false);
  const characterQuery  = useQuery({ queryKey: ["character"],    queryFn: api.character });
  const dungeonsQuery   = useQuery({ queryKey: ["dungeons"],     queryFn: api.dungeons  });
  const currentRunQuery = useQuery({
    queryKey: ["current-run"],
    queryFn: api.currentRun,
    refetchInterval: (q) => q.state.data?.status === "IN_PROGRESS" ? 5000 : false,
  });
  const inventoryQuery  = useQuery({ queryKey: ["inventory"],    queryFn: () => api.inventory() });

  const startMutation = useMutation({
    mutationFn: (id: number) => api.startRun(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["current-run"] });
    },
  });

  const startMiniGameMutation = useMutation({
    mutationFn: ({ runId, configId }: { runId: number; configId: number }) => api.startMiniGame(runId, configId),
    onSuccess: (attempt) => {
      setChoosingDifficulty(false);
      setMiniGameAttempt(attempt);
    },
  });

  const patchInventoryCaches = (result: InventoryMutationResponse) => {
    queryClient.setQueryData<Character>(["character"], (current) => current ? ({
      ...current,
      equipment: result.equipment,
      stats: result.stats,
    }) : current);
    queryClient.setQueryData<Inventory>(["inventory"], (current) => current ? mergeInventoryMutation(current, result) : current);
    queryClient.setQueriesData<InfiniteData<Inventory>>(
      {
        predicate: (query) => (
          query.queryKey[0] === "inventory" &&
          Array.isArray((query.state.data as { pages?: unknown[] } | undefined)?.pages)
        ),
      },
      (current) => current ? mergeInfiniteInventoryMutation(current, result) : current
    );
  };

  const ensureMiniInventoryFilled = async (result: InventoryMutationResponse) => {
    let current = queryClient.getQueryData<Inventory>(["inventory"]);
    if (!current) return;

    while (packItemCount(current.items, result.equipment) < INVENTORY_PAGE_SIZE) {
      // Используем pagination из кеша чтобы не зависеть от длины массива items
      // (массив может содержать экипированные предметы, что смещает счёт страниц)
      if (!current.pagination.has_next) return;
      const pageSize = current.pagination.page_size || INVENTORY_PAGE_SIZE;
      const nextPage = current.pagination.page + 1;

      const nextInventory = await api.inventory(nextPage, pageSize);
      const existingIds = new Set(current.items.map((item) => item.id));
      const additions: InventoryCard[] = [];
      for (const item of nextInventory.items) {
        if (existingIds.has(item.id)) continue;
        additions.push(item);
        existingIds.add(item.id);
        if (packItemCount([...current.items, ...additions], result.equipment) >= INVENTORY_PAGE_SIZE) break;
      }
      if (additions.length === 0) return;

      queryClient.setQueryData<Inventory>(["inventory"], (cached) => cached ? ({
        ...cached,
        pagination: nextInventory.pagination,
        items: [...cached.items, ...additions],
      }) : cached);
      current = queryClient.getQueryData<Inventory>(["inventory"]);
      if (!current) return;
    }
  };

  const applyInventoryMutation = async (result: InventoryMutationResponse, shouldFillMiniInventory = false) => {
    setDragState(null);
    setDragOverSlot(null);
    setInventoryDropActive(false);
    setDropError(null);
    patchInventoryCaches(result);
    if (shouldFillMiniInventory) {
      await ensureMiniInventoryFilled(result);
    }
  };

  const equipMutation = useMutation({
    mutationFn: (itemId: number) => api.equip(itemId),
    onSuccess: async (result) => {
      await applyInventoryMutation(result, !result.replaced_item);
    },
  });

  const unequipMutation = useMutation({
    mutationFn: (itemId: number) => api.unequip(itemId),
    onSuccess: async (result) => {
      await applyInventoryMutation(result);
    },
  });

  const visibleIconKey = Array.from(
    new Set([
      ...Object.values(characterQuery.data?.equipment ?? {}).map((item) => bestMediaUrl(item?.media, ["medium_url", "small_url", "large_url"])),
      ...(inventoryQuery.data?.items ?? []).map((item) => bestMediaUrl(item.media, ["small_url", "medium_url", "large_url"])),
    ].filter((url): url is string => Boolean(url)))
  ).join("\n");

  useEffect(() => {
    if (!visibleIconKey || typeof window === "undefined") return;

    const preloadedImages = visibleIconKey.split("\n").map((url) => {
      const image = new window.Image();
      image.decoding = "async";
      image.src = url;
      return image;
    });

    return () => {
      preloadedImages.forEach((image) => {
        image.onload = null;
        image.onerror = null;
      });
    };
  }, [visibleIconKey]);

  if (characterQuery.isLoading) {
    return <CharacterScreenSkeleton />;
  }
  if (characterQuery.error || !characterQuery.data) {
    return <ErrorNotice message={(characterQuery.error as Error | null)?.message ?? t("character.failedLoad")} />;
  }

  const character = characterQuery.data;
  const portraitUrl =
    bestMediaUrl(character.avatar, ["large_url", "medium_url", "small_url"]) ||
    bestMediaUrl(character.class?.media, ["large_url", "medium_url", "small_url"]);
  const xpMax = character.experience_to_next_level ?? 1000;
  const xp    = character.experience;
  const hpMax = character.stats?.health ?? 220;
  const hpCur = hpMax;

  const invItems = inventoryQuery.data?.items ?? [];
  const inventoryCount = inventoryQuery.data?.items_count ?? invItems.length;
  const inventoryLimit = inventoryQuery.data?.slots_limit ?? null;
  const equippedItemIds = new Set(
    Object.values(character.equipment ?? {})
      .map((item) => item?.id)
      .filter((id): id is number => typeof id === "number")
  );
  const packItems = invItems.filter((item) => !equippedItemIds.has(item.id));
  const packCells = Array.from(
    { length: INVENTORY_PAGE_SIZE },
    (_, i) => packItems[i],
  );

  const canRun  = !currentRunQuery.data || currentRunQuery.data.status !== "IN_PROGRESS";
  const dungeons = dungeonsQuery.data ?? [];
  const activeRunImage = currentRunQuery.data
    ? bestMediaUrl(
        dungeons.find((dungeon) => dungeon.id === currentRunQuery.data?.location.id)?.media,
        ["small_url", "medium_url", "large_url"],
      )
    : undefined;

  // Compute combat power (sum stats)
  const stats = character.stats ?? {};
  const cp = stats.power ?? (
    (stats.attack ?? 0) * POWER_WEIGHTS.attack +
    (stats.defense ?? 0) * POWER_WEIGHTS.defense +
    (stats.health ?? 0) * POWER_WEIGHTS.health +
    (stats.critical_chance ?? 0) * POWER_WEIGHTS.critical_chance +
    (stats.evasion ?? 0) * POWER_WEIGHTS.evasion
  );

  const resetDragState = () => {
    setDragState(null);
    setDragOverSlot(null);
    setInventoryDropActive(false);
  };

  const handleDragStart = (item: InventoryCard, source: DragState["source"], event: DragEvent<HTMLDivElement>) => {
    setDragState({ item, source });
    setDropError(null);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(item.id));
    event.dataTransfer.setData("application/x-rpg-drag-source", source);
    setStableDragImage(event);
  };

  const handleSlotDrop = (slot: EquipmentSlot, event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const itemId = Number(event.dataTransfer.getData("text/plain"));
    const item = dragState?.item ?? invItems.find((candidate) => candidate.id === itemId);

    setDragOverSlot(null);
    setInventoryDropActive(false);

    if (!item) return;
    if (item.is_broken) {
      setDropError(t("equipment.brokenDrop"));
      return;
    }
    if (item.slot !== slot) {
      setDropError(t("equipment.wrongSlot", { slot: t(`slot.${item.slot}` as TranslationKey) }));
      return;
    }

    equipMutation.mutate(item.id);
  };

  const handleInventoryDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setInventoryDropActive(false);

    if (!dragState || dragState.source !== "equipment") return;

    unequipMutation.mutate(dragState.item.id);
  };

  return (
    <div className="dashboard animate-fade-in">

      {/* ════════ LEFT: Character Panel ════════ */}
      <div className="card">
        <div className="card-h">
          <div>
            <div className="card-title">{t("character.panelTitle")}</div>
            <div className="card-sub">{t("character.order")}</div>
          </div>
        </div>
        <div className="card-body">

          {/* Portrait */}
          <div className="portrait" style={{ overflow: "hidden", position: "relative" }}>
            {portraitUrl && (
              <img
                src={portraitUrl}
                alt={character.name}
                style={{
                  position: "absolute",
                  inset: 0,
                  width: "100%",
                  height: "100%",
                }}
              />
            )}
            {!portraitUrl && <span className="ph-label">{t("character.portrait")}</span>}
          </div>

          {/* Name + class */}
          <div style={{ marginTop: 16, textAlign: "center" }}>
            <div style={{
              fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
              fontSize: 21, fontWeight: 600, textTransform: "uppercase",
              letterSpacing: "0.04em", lineHeight: 1.2, color: "var(--bone)",
            }}>
              {character.name}
            </div>
            <div className="mono" style={{
              fontSize: 13, letterSpacing: "0.18em", textTransform: "uppercase",
              color: "var(--text-dim)", marginTop: 4,
            }}>
              <span style={{ color: "var(--primary-bright)" }}>{character.class?.name ?? "—"}</span>
              {" · "}{t("common.levelShort")} {character.level}
              {" · "}{t("common.rank")} {character.rank ?? "F"}
            </div>
          </div>

          {/* XP + HP bars */}
          <div style={{ marginTop: 20 }}>
            <BarBlock label={t("common.experience")} cur={xp} max={xpMax} kind="xp" />
            <BarBlock label={t("common.vitality")}   cur={hpCur} max={hpMax} kind="hp" />
          </div>

          <div className="divider" />

          {/* Combat stats */}
          <div className="card-sub" style={{ marginBottom: 10 }}>{t("character.combatStats")}</div>
          <div className="stat-list" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div className="sl-row">
              <span className="lbl">{t("common.power")}</span>
              <span className="val power-value" style={{ color: "var(--primary-bright)" }}>
                {cp}
                <PowerHelp stats={stats} power={cp} />
              </span>
            </div>
            <div className="sl-row">
              <span className="lbl">{t("common.attack")}</span>
              <span className="val">{stats.attack ?? 0}</span>
            </div>
            <div className="sl-row">
              <span className="lbl">{t("common.defense")}</span>
              <span className="val">{stats.defense ?? 0}</span>
            </div>
            <div className="sl-row">
              <span className="lbl">{t("common.crit")}</span>
              <span className="val">{stats.critical_chance ?? 0}%</span>
            </div>
            <div className="sl-row">
              <span className="lbl">{t("common.evasion")}</span>
              <span className="val">{stats.evasion ?? 0}%</span>
            </div>
            <div className="sl-row">
              <span className="lbl">{t("common.health")}</span>
              <span className="val">{stats.health ?? 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ════════ CENTER: Equipment + Quick Expeditions ════════ */}
      <div className="col">

        {/* Active expedition strip */}
        {currentRunQuery.data && currentRunQuery.data.status !== "CLAIMED" && (
          <ActiveExpeditionStrip
            run={currentRunQuery.data}
            imageUrl={activeRunImage}
            onClaimed={setRewardResult}
            onSpeedUp={() => setChoosingDifficulty(true)}
            speedUpPending={startMiniGameMutation.isPending}
          />
        )}

        {/* Equipment paperdoll */}
        <div className="card">
          <div className="card-h">
            <div>
              <div className="card-title">{t("equipment.title")}</div>
              <div className="card-sub">{t("equipment.slots")}</div>
            </div>
          </div>
          <div className="card-body">
            <ErrorNotice message={
              dropError ??
              (equipMutation.error as Error | null)?.message ??
              (unequipMutation.error as Error | null)?.message
            } />
            <div className="equipment-layout">
              {EQUIPMENT_SLOTS.map((cell, i) => {
                const item = character.equipment?.[cell.slot] ?? null;
                const dropActive = dragOverSlot === cell.slot && Boolean(dragState);
                return (
                  <SlotCell
                    key={i}
                    label={t(cell.label)}
                    glyph={cell.glyph}
                    rarity={item?.rarity}
                    iconUrl={bestMediaUrl(item?.media, ["medium_url", "small_url", "large_url"])}
                    broken={item?.is_broken}
                    durability={item?.durability}
                    canDrop={dragState?.item.slot === cell.slot}
                    draggable={Boolean(item)}
                    dropActive={dropActive}
                    onDragEnd={resetDragState}
                    onDragLeave={() => setDragOverSlot((current) => current === cell.slot ? null : current)}
                    onDragOver={(event) => {
                      if (!dragState || equipMutation.isPending || unequipMutation.isPending) return;
                      event.preventDefault();
                      event.dataTransfer.dropEffect = dragState.item.slot === cell.slot ? "move" : "none";
                      setDragOverSlot(cell.slot);
                    }}
                    onDragStart={item ? (event) => handleDragStart(item, "equipment", event) : undefined}
                    onDrop={(event) => handleSlotDrop(cell.slot, event)}
                  />
                );
              })}
            </div>
          </div>
        </div>

        {/* Quick expeditions */}
        <div className="card">
          <div className="card-h">
            <div>
              <div className="card-title">{t("dungeons.quickTitle")}</div>
              <div className="card-sub">{canRun ? t("dungeons.sendRun") : t("dungeons.heroAway")}</div>
            </div>
            <button
              className="btn"
              style={{ padding: "8px 12px", fontSize: 12, whiteSpace: "nowrap" }}
              onClick={onOpenDungeons}
            >
              {t("dungeons.all")} →
            </button>
          </div>
          <div className="card-body">
            <ErrorNotice message={(startMutation.error as Error | null)?.message} />
            <div className="quick-dungeons">
              {dungeonsQuery.isLoading && <LoadingLine label={t("dungeons.loading")} />}
              {dungeons.slice(0, 3).map((d) => (
                <QuickDungeonRow
                  key={d.id}
                  dungeon={d}
                  canRun={canRun}
                  onRun={(id) => startMutation.mutate(id)}
                  isPending={startMutation.isPending}
                  locale={locale}
                  runLabel={t("dungeons.run")}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ════════ RIGHT: Inventory mini-grid + Journal ════════ */}
      <div
        className={`card inventory-card${inventoryDropActive ? " inventory-drop-ok" : ""}`}
        onDragLeave={() => setInventoryDropActive(false)}
        onDragOver={(event) => {
          if (!dragState || dragState.source !== "equipment" || unequipMutation.isPending) return;
          event.preventDefault();
          event.dataTransfer.dropEffect = "move";
          setInventoryDropActive(true);
        }}
        onDrop={handleInventoryDrop}
      >
        <div className="card-h">
          <div>
            <div className="card-title">{t("nav.inventory")}</div>
            <div className="card-sub">
              {inventoryLimit === null ? t("inventory.inPack", { count: packItems.length }) : `${inventoryCount} / ${inventoryLimit}`} · {t("inventory.dragItem")}
            </div>
          </div>
          <button
            className="btn"
            style={{ padding: "6px 10px", fontSize: 12 }}
            title={t("inventory.open")}
            onClick={onOpenInventory}
          >
            ↗
          </button>
        </div>
        <div className="card-body">
          <div className="inv-grid">
            {packCells.map((item, i) => {
              return (
                <InvCell
                  key={item?.id ?? `empty-${i}`}
                  item={item}
                  onDragEnd={resetDragState}
                  onDragStart={(dragged, event) => handleDragStart(dragged, "inventory", event)}
                />
              );
            })}
          </div>

          <div className="divider" />

          {/* Journal */}
          <div className="card-sub" style={{ marginBottom: 10 }}>{t("inventory.recentJournal")}</div>
          {currentRunQuery.data?.result_preview ? (
            <div className="log-line" style={{ color: currentRunQuery.data.result_preview.is_success ? "var(--success)" : "var(--error)" }}>
              <span className="t">{t("inventory.now")}</span>
              <span className="m">
                {currentRunQuery.data.result_preview.is_success
                  ? `+${currentRunQuery.data.result_preview.experience} XP · +${currentRunQuery.data.result_preview.money_copper}c ${t("inventory.gold")}`
                  : t("inventory.failed")}
              </span>
            </div>
          ) : (
            <>
              <div className="log-line">
                <span className="t">—:—</span>
                <span className="m" style={{ color: "var(--text-mute)", fontStyle: "italic" }}>{t("inventory.noActivity")}</span>
              </div>
              <div className="log-line">
                <span className="t">—:—</span>
                <span className="m" style={{ color: "var(--text-mute)", fontStyle: "italic" }}>{t("inventory.sendExpedition")}</span>
              </div>
            </>
          )}
        </div>
      </div>

      {rewardResult && (
        <DungeonRewardModal
          result={rewardResult}
          onClose={() => setRewardResult(null)}
        />
      )}
      {choosingDifficulty && !miniGameAttempt && currentRunQuery.data && (
        <DungeonMiniGameDifficultyModal
          pending={startMiniGameMutation.isPending}
          onClose={() => setChoosingDifficulty(false)}
          onSelect={(configId) => startMiniGameMutation.mutate({ runId: currentRunQuery.data!.id, configId })}
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
      <ErrorNotice message={(startMiniGameMutation.error as Error | null)?.message} />

    </div>
  );
}
