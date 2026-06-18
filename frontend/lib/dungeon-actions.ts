import type { Dungeon, DungeonActionState } from "@/lib/types";

export type DungeonBlockerCode = DungeonActionState["blocker_code"];

export type DungeonActionLabels = {
  sending: string;
  autoRunning: string;
  autoSummary: string;
  inProgress: string;
  heroBusy: string;
  claimFirst: string;
  categoryLimitReached: string;
  dailyLimitReached: string;
  repairGear: string;
  lowHp: string;
  gather: string;
  sendHero: string;
};

export type DungeonActionContext = {
  startPending: boolean;
  currentRunBlockerCode: DungeonBlockerCode;
  activeLocationId: number | null;
  hpTooLow: boolean;
  labels: DungeonActionLabels;
};

export type DungeonResolvedActionState = {
  actionLabel: string;
  blockerCode: DungeonBlockerCode;
  categoryExhausted: boolean;
  dailyRemaining: Dungeon["daily_remaining"];
  disabled: boolean;
  exhausted: boolean;
  isActive: boolean;
  isResource: boolean;
};

export function fallbackDungeonBlockerCode(
  location: Dungeon,
  context: Pick<DungeonActionContext, "currentRunBlockerCode" | "hpTooLow">,
): DungeonBlockerCode {
  if (context.currentRunBlockerCode) return context.currentRunBlockerCode;
  if (location.limit_category.is_exhausted) return "category_limit_reached";
  if (location.daily_remaining !== null && location.daily_remaining <= 0) return "daily_limit_reached";
  if (location.location_type !== "resource" && context.hpTooLow) return "hp_too_low";
  return null;
}

export function dungeonActionLabel({
  blockerCode,
  isActive,
  isResource,
  labels,
}: {
  blockerCode: DungeonBlockerCode;
  isActive: boolean;
  isResource: boolean;
  labels: DungeonActionLabels;
}) {
  if (blockerCode === "auto_run_active") return labels.autoRunning;
  if (blockerCode === "auto_run_summary_unread") return labels.autoSummary;
  if (blockerCode === "active_run_exists") return isActive ? labels.inProgress : labels.heroBusy;
  if (blockerCode === "unclaimed_run_exists") return labels.claimFirst;
  if (blockerCode === "category_limit_reached") return labels.categoryLimitReached;
  if (blockerCode === "daily_limit_reached") return labels.dailyLimitReached;
  if (blockerCode === "broken_items_block_run") return labels.repairGear;
  if (blockerCode === "hp_too_low") return labels.lowHp;
  if (blockerCode === "no_character") return labels.heroBusy;
  return isResource ? labels.gather : labels.sendHero;
}

export function resolveDungeonActionState(
  location: Dungeon,
  context: DungeonActionContext,
): DungeonResolvedActionState {
  const isResource = location.location_type === "resource";
  const blockerCode = context.currentRunBlockerCode
    ?? location.action_state?.blocker_code
    ?? fallbackDungeonBlockerCode(location, context);
  const dailyRemaining = location.action_state?.daily_remaining ?? location.daily_remaining;
  const limitCategory = location.action_state?.limit_category ?? location.limit_category;
  const exhausted = dailyRemaining !== null && dailyRemaining <= 0;
  const categoryExhausted = limitCategory.is_exhausted;
  const fallbackActive = context.activeLocationId === location.id;
  const isActive = context.currentRunBlockerCode
    ? fallbackActive
    : location.action_state?.is_active_location ?? fallbackActive;
  const canStart = !context.currentRunBlockerCode && (location.action_state?.can_start ?? blockerCode === null);
  const disabled = context.startPending || !canStart;
  const actionLabel = context.startPending
    ? context.labels.sending
    : dungeonActionLabel({
        blockerCode,
        isActive,
        isResource,
        labels: context.labels,
      });

  return {
    actionLabel,
    blockerCode,
    categoryExhausted,
    dailyRemaining,
    disabled,
    exhausted,
    isActive,
    isResource,
  };
}
