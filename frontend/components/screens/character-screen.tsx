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
import { useSwipeToClose } from "@/lib/use-modal-scroll-lock";
import { rarityColor as rc, rarityGlow as rg } from "@/lib/rarity";
import { useIsMobile } from "@/lib/use-is-mobile";
import type { Character, ClaimResponse, Dungeon, DungeonMiniGameAttempt, EquipmentSlot, Inventory, InventoryCard, InventoryMutationResponse, ItemDetail, Potion, StatKey } from "@/lib/types";

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
  onClick,
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
  onClick?: () => void;
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
      className={`slot${hasItem ? " filled" : ""}${draggable ? " draggable" : ""}${onClick ? " tappable" : ""}${dropActive ? (canDrop ? " drop-ok" : " drop-blocked") : ""}`}
      draggable={draggable}
      onClick={onClick}
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
  intellect: 1.5,
  critical_chance: 1.5,
  evasion: 1.5,
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
    { key: "intellect", label: t("common.intellect"), value: stats?.intellect ?? 0, weight: POWER_WEIGHTS.intellect },
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
  const isMobile = useIsMobile();
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

  if (isMobile) {
    const accent = done ? "var(--warning)" : "var(--primary)";
    return (
      <div style={{
        padding: 12, borderRadius: 16,
        background: "linear-gradient(135deg, rgba(59,130,246,0.14), rgba(22,30,49,0.5))",
        border: `1px solid ${accent}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
          <div style={{ width: 46, height: 46, minWidth: 46, borderRadius: 11, flexShrink: 0, overflow: "hidden", position: "relative", background: "linear-gradient(135deg,#2c3a5e,#19223a)" }}>
            {imageUrl && <img src={imageUrl} alt={run.location.name} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />}
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
            <button className="btn btn-primary" style={{ flexShrink: 0, padding: "9px 14px", fontSize: 12 }} disabled={speedUpPending} onClick={onSpeedUp}>
              {speedUpPending ? t("miniGame.starting") : t("miniGame.speedUp")}
            </button>
          )}
          {done && (
            <button className="btn btn-primary" style={{ flexShrink: 0, padding: "9px 14px", fontSize: 12 }} disabled={claimMut.isPending} onClick={() => claimMut.mutate(run.id)}>
              {claimMut.isPending ? t("dungeons.claiming") : t("dungeons.claim")}
            </button>
          )}
        </div>
        <div style={{ marginTop: 11, height: 7, borderRadius: 4, background: "rgba(8,11,20,0.7)", overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${progress * 100}%`, borderRadius: 4, background: done ? "var(--warning)" : "linear-gradient(90deg, var(--primary-deep), var(--primary-bright))", transition: "width 1s linear" }} />
        </div>
        <div className="mono" style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 9, color: "#7c89a3" }}>
          <span>{t("dungeons.complete", { progress: Math.round(progress * 100) })}</span>
          {inProgress && <span>{t("dungeons.left", { time: timeLabel })}</span>}
        </div>
        <ErrorNotice message={(claimMut.error as Error | null)?.message} />
      </div>
    );
  }

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
   PotionsPanel — минимальный UI Этапа 3
═══════════════════════════════════════ */
function PotionsPanel({ hpFull }: { hpFull: boolean }) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const potionsQuery = useQuery({ queryKey: ["potions"], queryFn: api.potions });
  const useMut = useMutation({
    mutationFn: (potionId: number) => api.usePotion({ potion_id: potionId, quantity: 1 }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["character"] }),
        queryClient.invalidateQueries({ queryKey: ["potions"] }),
      ]);
    },
  });

  const potions = potionsQuery.data ?? [];

  return (
    <div style={{ marginTop: 16 }}>
      <div className="card-sub" style={{ marginBottom: 10 }}>{t("potions.title")}</div>
      {potions.length === 0 ? (
        <div style={{ color: "var(--bone)", fontSize: 13 }}>{t("potions.empty")}</div>
      ) : (
        <div className="stat-list" style={{ gridTemplateColumns: "1fr" }}>
          {potions.map((potion: Potion) => (
            <div key={potion.id} className="sl-row" style={{ alignItems: "center", gap: 10 }}>
              <span className="lbl" style={{ minWidth: 0, flexDirection: "column", alignItems: "flex-start", gap: 2 }}>
                <span style={{ maxWidth: "100%", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {potion.name}
                </span>
                <span className="mono" style={{ fontSize: 11, color: "var(--text-mute)", whiteSpace: "nowrap" }}>
                  +{potion.heal_percent}% · ×{potion.count}
                </span>
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={hpFull || useMut.isPending}
                onClick={() => useMut.mutate(potion.id)}
                style={{ flexShrink: 0, minWidth: 42, padding: "7px 10px", whiteSpace: "nowrap", fontSize: 12 }}
              >
                {t("potions.useShort")}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════
   Mobile: equip-select sheet + compare modal
═══════════════════════════════════════ */
const COMPARE_STATS: StatKey[] = ["attack", "defense", "critical_chance", "evasion", "intellect", "max_hp"];
const PERCENT_STATS = new Set<StatKey>(["critical_chance", "evasion"]);

function EquipCompareModal({ candidate, currentItem, slotLabel, onCancel, onConfirm, pending }: {
  candidate: InventoryCard;
  currentItem: InventoryCard | null;
  slotLabel: string;
  onCancel: () => void;
  onConfirm: () => void;
  pending: boolean;
}) {
  const { t } = useI18n();
  const swipeToClose = useSwipeToClose(onCancel);
  const color = rc(candidate.rarity);
  const candQ = useQuery({ queryKey: ["item", candidate.id], queryFn: () => api.item(candidate.id) });
  const curQ = useQuery({
    queryKey: ["item", currentItem?.id],
    queryFn: () => api.item(currentItem!.id),
    enabled: Boolean(currentItem),
  });

  const newStats: ItemDetail["stats"] = candQ.data?.stats ?? {};
  const oldStats: ItemDetail["stats"] = curQ.data?.stats ?? {};
  const rows = COMPARE_STATS.filter((k) => (newStats[k] ?? 0) !== 0 || (oldStats[k] ?? 0) !== 0);
  const dur = candQ.data?.durability ?? candidate.durability;
  const iconUrl = bestMediaUrl(candidate.media, ["medium_url", "small_url", "large_url"]);

  return (
    <>
      <div className="mobile-sheet-overlay" style={{ zIndex: 70 }} onClick={onCancel} />
      <div className="equip-compare-modal" {...swipeToClose} style={{
        position: "fixed", left: 16, right: 16, top: "50%", transform: "translateY(-50%)", zIndex: 71,
        borderRadius: 22, overflow: "hidden", display: "flex", flexDirection: "column", maxHeight: "80%",
        background: "linear-gradient(180deg, #121a2d, #0b1120)", border: "1px solid rgba(110,140,190,0.2)",
      }}>
        {/* header */}
        <div style={{ flex: "none", padding: "14px 16px 12px", borderBottom: "1px solid rgba(110,140,190,0.1)", display: "flex", alignItems: "flex-start", gap: 11 }}>
          <div style={{ position: "relative", width: 52, height: 52, borderRadius: 12, flexShrink: 0, background: "linear-gradient(150deg,#2b3a5e,#161f36)", overflow: "hidden" }}>
            {iconUrl && <img src={iconUrl} alt={candidate.name} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />}
            <div style={{ position: "absolute", top: 5, left: 5, width: 7, height: 7, borderRadius: "50%", background: color, boxShadow: `0 0 8px ${color}` }} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap" }}>
              <span style={{ fontFamily: "var(--font-cinzel, 'Cinzel', serif)", fontWeight: 600, fontSize: 16, color: "#eef2f8" }}>{candidate.name ?? slotLabel}</span>
              <span className="mono" style={{ fontSize: 8, fontWeight: 600, padding: "2px 6px", borderRadius: 5, color, background: `${color}1f` }}>{t(`rarity.${candidate.rarity}` as TranslationKey)}</span>
            </div>
            <div className="mono" style={{ fontSize: 9, color: "#7c89a3", marginTop: 3 }}>
              {slotLabel}{dur ? ` · ${t("common.durability")} ${dur.current}/${dur.max}` : ""}
            </div>
          </div>
          <button onClick={onCancel} aria-label={t("common.cancel")} style={{ width: 28, height: 28, borderRadius: 9, flexShrink: 0, border: "1px solid rgba(110,140,190,0.16)", background: "rgba(11,16,28,0.5)", color: "#9aa6bd", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>✕</button>
        </div>

        {/* stat comparison */}
        <div className="mobile-noscroll" style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: "14px 16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
            <span className="mono" style={{ fontSize: 8, letterSpacing: "0.14em", textTransform: "uppercase", color: "#5d6b86" }}>{t("character.combatStats")}</span>
            <div style={{ display: "flex", gap: 20 }}>
              <span className="mono" style={{ fontSize: 8, letterSpacing: "0.08em", textTransform: "uppercase", color: "#5d6b86" }}>{t("equipment.now")}</span>
              <span className="mono" style={{ fontSize: 8, letterSpacing: "0.08em", textTransform: "uppercase", color: "#6f9bff" }}>{t("equipment.new")}</span>
            </div>
          </div>
          {(candQ.isLoading || (currentItem && curQ.isLoading)) ? (
            <LoadingLine label={t("inventory.loadingItem")} />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {rows.map((k) => {
                const oldV = oldStats[k] ?? 0;
                const newV = newStats[k] ?? 0;
                const delta = newV - oldV;
                const suffix = PERCENT_STATS.has(k) ? "%" : "";
                const deltaColor = delta > 0 ? "var(--success)" : delta < 0 ? "var(--error)" : "#6b7894";
                return (
                  <div key={k} style={{ display: "flex", alignItems: "center", padding: "9px 11px", borderRadius: 10, background: "rgba(11,16,28,0.5)", border: "1px solid rgba(110,140,190,0.07)" }}>
                    <span className="mono" style={{ flex: 1, fontSize: 9, textTransform: "uppercase", color: "#7c89a3", letterSpacing: "0.08em" }}>{t(`stats.${k}` as TranslationKey)}</span>
                    <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                      <span style={{ fontWeight: 600, fontSize: 13, color: "#6b7894", minWidth: 26, textAlign: "right" }}>{oldV}{suffix}</span>
                      <span style={{ color: "#3d4d68" }}>→</span>
                      <span style={{ fontWeight: 700, fontSize: 13, color: delta >= 0 ? "#eef2f8" : "#f87171", minWidth: 26, textAlign: "left" }}>{newV}{suffix}</span>
                      <span className="mono" style={{ fontSize: 10, fontWeight: 600, color: deltaColor, minWidth: 40, textAlign: "right" }}>
                        {delta > 0 ? "+" : ""}{delta}{suffix}
                      </span>
                    </div>
                  </div>
                );
              })}
              {!currentItem && (
                <div style={{ marginTop: 3, padding: "9px 11px", borderRadius: 10, background: "rgba(63,181,107,0.07)", border: "1px solid rgba(63,181,107,0.18)", fontSize: 11, lineHeight: 1.4, color: "#7fc99c" }}>
                  {t("equipment.slotEmptyNote")}
                </div>
              )}
            </div>
          )}
        </div>

        {/* actions */}
        <div style={{ flex: "none", padding: "12px 16px 16px", borderTop: "1px solid rgba(110,140,190,0.08)", display: "flex", gap: 8 }}>
          <button onClick={onCancel} className="btn" style={{ flex: 1 }}>{t("common.cancel")}</button>
          <button onClick={onConfirm} disabled={pending || candidate.is_broken} className="btn btn-primary" style={{ flex: 1.6 }}>
            {pending ? t("auth.working") : t("equipment.equip")}
          </button>
        </div>
      </div>
    </>
  );
}

function MobileEquipSheet({ slotLabel, currentItem, items, onClose, onEquip, onUnequip, equipPending, unequipPending }: {
  slotLabel: string;
  currentItem: InventoryCard | null;
  items: InventoryCard[];
  onClose: () => void;
  onEquip: (itemId: number) => void;
  onUnequip: (itemId: number) => void;
  equipPending: boolean;
  unequipPending: boolean;
}) {
  const { t } = useI18n();
  const swipeToClose = useSwipeToClose(onClose);
  const [candidate, setCandidate] = useState<InventoryCard | null>(null);

  return (
    <>
      <div className="mobile-sheet-overlay" style={{ zIndex: 60 }} onClick={onClose} />
      <div className="mobile-sheet animate-sheet-up" {...swipeToClose} style={{ zIndex: 61, top: 64, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div className="mobile-sheet-grabber" />
        <div style={{ padding: "6px 18px 14px", borderBottom: "1px solid rgba(110,140,190,0.10)" }}>
          <div className="mono" style={{ fontSize: 9, letterSpacing: "0.18em", textTransform: "uppercase", color: "#6f9bff" }}>{t("equipment.slot")} · {slotLabel}</div>
          <div style={{ fontFamily: "var(--font-cinzel, 'Cinzel', serif)", fontWeight: 600, fontSize: 20, color: "#eef2f8", marginTop: 3 }}>{t("equipment.choose")}</div>
          {currentItem && (
            <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 9, padding: "9px 11px", borderRadius: 12, background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.2)" }}>
              <span className="mono" style={{ fontSize: 8.5, letterSpacing: "0.12em", textTransform: "uppercase", color: "#7c89a3" }}>{t("equipment.current")}:</span>
              <span style={{ flex: 1, fontWeight: 600, fontSize: 12, color: "#dbe2ef", minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{currentItem.name ?? slotLabel}</span>
              <button onClick={() => onUnequip(currentItem.id)} disabled={unequipPending} className="btn btn-danger" style={{ padding: "6px 11px", fontSize: 11 }}>{t("equipment.unequip")}</button>
            </div>
          )}
        </div>
        <div className="mobile-noscroll" style={{ flex: 1, minHeight: 0, overflowY: "auto", padding: "14px 16px", display: "flex", flexDirection: "column", gap: 9 }}>
          {items.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px 20px", color: "#7c89a3", fontSize: 13 }}>{t("equipment.noItemsForSlot")}</div>
          ) : items.map((it) => {
            const color = rc(it.rarity);
            const iconUrl = bestMediaUrl(it.media, ["medium_url", "small_url", "large_url"]);
            return (
              <button key={it.id} onClick={() => setCandidate(it)} style={{
                display: "flex", alignItems: "center", gap: 12, padding: 11, borderRadius: 14, textAlign: "left", cursor: "pointer",
                border: "1px solid rgba(110,140,190,0.12)", background: "rgba(16,22,38,0.5)",
              }}>
                <div style={{ position: "relative", width: 52, height: 52, borderRadius: 11, flexShrink: 0, background: "linear-gradient(150deg,#2b3a5e,#161f36)", overflow: "hidden" }}>
                  {iconUrl && <img src={iconUrl} alt={it.name} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />}
                  <div style={{ position: "absolute", top: 5, left: 5, width: 7, height: 7, borderRadius: "50%", background: color, boxShadow: `0 0 7px ${color}` }} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontWeight: 700, fontSize: 13, color: "#e6ecf6" }}>{it.name ?? slotLabel}</span>
                    <span className="mono" style={{ fontSize: 8.5, fontWeight: 600, padding: "1px 5px", borderRadius: 5, color, background: `${color}1f` }}>{t(`rarity.${it.rarity}` as TranslationKey)}</span>
                  </div>
                  {it.durability && (
                    <div className="mono" style={{ fontSize: 8.5, color: "#6b7894", marginTop: 4 }}>{t("common.durability")} {it.durability.current}/{it.durability.max}</div>
                  )}
                  {it.is_broken && <div className="mono" style={{ fontSize: 8.5, color: "var(--error)", marginTop: 3 }}>{t("inventory.broken")}</div>}
                </div>
              </button>
            );
          })}
        </div>
      </div>
      {candidate && (
        <EquipCompareModal
          candidate={candidate}
          currentItem={currentItem}
          slotLabel={slotLabel}
          pending={equipPending}
          onCancel={() => setCandidate(null)}
          onConfirm={() => onEquip(candidate.id)}
        />
      )}
    </>
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
  const isMobile = useIsMobile();
  const [equipSlotOpen, setEquipSlotOpen] = useState<EquipmentSlot | null>(null);
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
    onMutate: (dungeonId: number) => {
      const prev = queryClient.getQueryData<Dungeon[]>(["dungeons"]);
      queryClient.setQueryData<Dungeon[]>(["dungeons"], (old) => {
        if (!old) return old;
        const target = old.find((d) => d.id === dungeonId);
        const catId = target?.limit_category?.id;
        return old.map((d) => {
          const newD = { ...d };
          if (d.id === dungeonId && d.daily_remaining !== null) {
            newD.daily_remaining = Math.max(0, d.daily_remaining - 1);
          }
          if (catId && d.limit_category?.id === catId && d.limit_category.limit_count > 0) {
            const newUsed = d.limit_category.used + 1;
            const newRemaining = d.limit_category.remaining !== null
              ? Math.max(0, d.limit_category.remaining - 1)
              : null;
            newD.limit_category = {
              ...d.limit_category,
              used: newUsed,
              remaining: newRemaining,
              is_exhausted: newRemaining !== null ? newRemaining <= 0 : false,
            };
          }
          return newD;
        });
      });
      return { prev };
    },
    onError: (_err, _id, context) => {
      if (context?.prev) queryClient.setQueryData(["dungeons"], context.prev);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["current-run"] });
      await queryClient.invalidateQueries({ queryKey: ["dungeons"] });
    },
  });

  const startMiniGameMutation = useMutation({
    mutationFn: ({ runId, configId }: { runId: number; configId?: number }) => api.startMiniGame(runId, configId),
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
  const hpMax = character.stats?.max_hp ?? 220;
  const hpCur = character.stats?.current_hp ?? hpMax;

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
    (stats.intellect ?? 0) * POWER_WEIGHTS.intellect +
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

          <PotionsPanel hpFull={hpCur >= hpMax} />

          <div className="divider" />

          {/* Combat stats */}
          <div className="card-sub" style={{ marginBottom: 10 }}>{t("character.combatStats")}</div>
          <div className="combat-stats-divider" aria-hidden="true" />
          <div className="stat-list stat-list--combat" style={{ gridTemplateColumns: "1fr 1fr" }}>
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
              <span className="lbl">{t("common.intellect")}</span>
              <span className="val">{stats.intellect ?? 0}</span>
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
            onSpeedUp={() => {
              const mg = currentRunQuery.data!.mini_game;
              if (mg?.started && mg.status === "IN_PROGRESS") {
                startMiniGameMutation.mutate({ runId: currentRunQuery.data!.id });
              } else {
                setChoosingDifficulty(true);
              }
            }}
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
                    draggable={!isMobile && Boolean(item)}
                    dropActive={dropActive}
                    onClick={isMobile ? () => setEquipSlotOpen(cell.slot) : undefined}
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

        {/* Quick expeditions — desktop only (hidden on mobile per design) */}
        {!isMobile && (
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
        )}
      </div>

      {/* ════════ RIGHT: Inventory mini-grid + Journal — desktop only ════════ */}
      {!isMobile && (
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
      )}

      {/* Mobile: equip-select sheet (tap a slot) */}
      {isMobile && equipSlotOpen && (
        <MobileEquipSheet
          slotLabel={t(`slot.${equipSlotOpen}` as TranslationKey)}
          currentItem={character.equipment?.[equipSlotOpen] ?? null}
          items={packItems.filter((it) => it.slot === equipSlotOpen)}
          equipPending={equipMutation.isPending}
          unequipPending={unequipMutation.isPending}
          onEquip={(itemId) => { equipMutation.mutate(itemId); setEquipSlotOpen(null); }}
          onUnequip={(itemId) => { unequipMutation.mutate(itemId); setEquipSlotOpen(null); }}
          onClose={() => setEquipSlotOpen(null)}
        />
      )}

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
