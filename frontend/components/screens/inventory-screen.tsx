"use client";

import { useInfiniteQuery, useMutation, useQuery, useQueryClient, type InfiniteData } from "@tanstack/react-query";
import { Check, ChevronDown, Filter, FlaskConical, Leaf, ListChecks, Minus, Plus, ShieldCheck, Wrench, X } from "lucide-react";
import { useEffect, useMemo, useState, type CSSProperties, type ReactNode, type UIEvent } from "react";
import { useI18n } from "@/components/providers";
import { CopperDisplay, ErrorNotice, InventoryScreenSkeleton, LoadingLine } from "@/components/ui";
import { api } from "@/lib/api";
import type { TranslationKey } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import { RARITY_COLOR, rarityColor as rc, rarityGlow as rg } from "@/lib/rarity";
import type { Character, CraftRecipe, DestroyPreview, Ingredient, Inventory, InventoryCard, InventoryMutationResponse, ItemDetail, Potion, RepairPreview } from "@/lib/types";
import { useModalScrollLock, useSwipeToClose } from "@/lib/use-modal-scroll-lock";
import { useIsMobile } from "@/lib/use-is-mobile";

/** Делит общее количество на визуальные стаки по `size` (например 6 → [5, 1]). */
function splitToStacks(count: number, size = 5): number[] {
  if (count <= 0) return [];
  const stacks: number[] = [];
  let left = count;
  while (left > 0) {
    stacks.push(Math.min(left, size));
    left -= size;
  }
  return stacks;
}

const INVENTORY_PAGE_SIZE = 24;

/** Rarity ranks low→high; used as the equipment filter "icons". */
const RARITY_RANKS = ["f", "e", "d", "c", "b", "a", "s", "ex"] as const;

type FilterOption = { value: string | null; label: string; color?: string };

/** Compact chip row used for the equipment (rarity) and consumables filters. */
function FilterChips({ options, active, onSelect }: {
  options: FilterOption[];
  active: string | null;
  onSelect: (value: string | null) => void;
}) {
  return (
    <div className="filter-chips" role="group">
      {options.map((opt) => {
        const isActive = active === opt.value;
        return (
          <button
            key={opt.value ?? "all"}
            type="button"
            className={`filter-chip${isActive ? " active" : ""}`}
            aria-pressed={isActive}
            title={opt.label}
            onClick={() => onSelect(opt.value)}
            style={opt.color ? ({ "--chip-color": opt.color } as CSSProperties) : undefined}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

function MobileFilterDropdown({ options, active, onSelect, menuLayout = "grid" }: {
  options: FilterOption[];
  active: string | null;
  onSelect: (value: string | null) => void;
  menuLayout?: "grid" | "list";
}) {
  const { t } = useI18n();
  const [filterOpen, setFilterOpen] = useState(false);
  const activeLabel = options.find((o) => o.value === active)?.label ?? t("inventory.filterAll");

  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setFilterOpen((v) => !v)}
        style={{
          display: "flex", alignItems: "center", gap: 8, padding: "9px 13px", borderRadius: 11, cursor: "pointer",
          border: `1px solid ${filterOpen ? "rgba(96,165,250,0.4)" : "rgba(110,140,190,0.18)"}`,
          background: "rgba(11,16,28,0.5)", color: "#cdd6e6", fontWeight: 600, fontSize: 12,
          whiteSpace: "nowrap",
        }}
      >
        <Filter size={14} />{t("inventory.filter")}
        <span style={{ color: "#6f9bff" }}>{activeLabel}</span>
        <ChevronDown size={13} style={{ opacity: 0.6 }} />
      </button>
      {filterOpen && (
        <>
          <div style={{ position: "fixed", inset: 0, zIndex: 14 }} onClick={() => setFilterOpen(false)} />
          <div className="animate-pop-in" style={{
            position: "absolute", right: 0, top: 46, zIndex: 15, width: menuLayout === "list" ? 204 : 180, padding: 6, borderRadius: 13,
            background: "#0e1424", border: "1px solid rgba(110,140,190,0.18)", boxShadow: "0 18px 40px -12px rgba(0,0,0,0.8)",
          }}>
            <div style={{ display: "grid", gridTemplateColumns: menuLayout === "list" ? "1fr" : "1fr 1fr 1fr", gap: 4 }}>
              {options.map((opt) => {
                const selected = active === opt.value;
                const color = opt.color ?? "#9aa6bd";
                return (
                  <button
                    key={opt.value ?? "all"}
                    type="button"
                    onClick={() => { onSelect(opt.value); setFilterOpen(false); }}
                    className="mono"
                    style={{
                      padding: menuLayout === "list" ? "10px 12px" : "9px 0", borderRadius: 8, cursor: "pointer", fontWeight: 600, fontSize: 11,
                      border: `1px solid ${selected ? color : "rgba(110,140,190,0.15)"}`,
                      background: selected ? `${color}1f` : "rgba(11,16,28,0.5)",
                      color: selected ? color : "#9aa6bd",
                      textAlign: menuLayout === "list" ? "left" : "center",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function MobileSectionToolbar({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle: string;
  action?: ReactNode;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
      <div style={{ minWidth: 0 }}>
        <div className="card-title" style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {title}
        </div>
        <div className="card-sub" style={{ marginTop: 4 }}>
          {subtitle}
        </div>
      </div>
      {action && <div style={{ flexShrink: 0 }}>{action}</div>}
    </div>
  );
}

/* ── Pack grid cell ── */
function PackCell({
  item,
  selected,
  multiSelected,
  equipped,
  onClick,
}: {
  item?: InventoryCard;
  selected?: boolean;
  multiSelected?: boolean;
  equipped?: boolean;
  onClick?: () => void;
}) {
  const color   = item ? rc(item.rarity) : undefined;
  const hasItem = Boolean(item);
  const iconUrl = bestMediaUrl(item?.media, ["medium_url", "small_url", "large_url"]);
  const itemName = item?.name ?? "";
  return (
    <button
      type="button"
      disabled={!hasItem}
      onClick={onClick}
      className={`inv-cell${hasItem ? "" : " empty"}`}
      style={hasItem ? {
        borderColor: multiSelected ? "var(--success)" : selected ? "var(--primary)" : undefined,
        boxShadow: multiSelected
          ? "0 0 0 2px rgba(34,197,94,0.9), 0 0 18px rgba(34,197,94,0.45)"
          : selected
          ? "0 0 10px rgba(59,130,246,0.4)"
          : `inset 0 0 14px ${rg(item?.rarity)}`,
        cursor: "pointer",
      } : {}}
    >
      {hasItem && (
        iconUrl ? (
          <img
            src={iconUrl}
            alt={itemName}
            className="inv-icon"
          />
        ) : (
          <div className="inv-icon" />
        )
      )}
      {equipped && <div className="equipped-tag"><ShieldCheck size={9} strokeWidth={2.5} /></div>}
      {item?.is_broken && <div className="broken-tag"><Wrench size={9} strokeWidth={2.5} /></div>}
      {multiSelected && (
        <div style={{
          position: "absolute", right: 5, bottom: 5, width: 18, height: 18,
          borderRadius: 999, background: "var(--success)", color: "#fff",
          display: "grid", placeItems: "center",
          border: "1px solid rgba(255,255,255,0.5)",
        }}><Check size={11} strokeWidth={3} /></div>
      )}
    </button>
  );
}

/* ── helpers (inventory-screen) ── */
function addUniqueInvItem(items: InventoryCard[], item: InventoryCard): InventoryCard[] {
  return items.some((c) => c.id === item.id) ? items : [...items, item];
}

function patchInfiniteInventory(
  data: InfiniteData<Inventory>,
  result: InventoryMutationResponse,
): InfiniteData<Inventory> {
  return {
    ...data,
    pages: data.pages.map((page, idx) => {
      // Добавляем item и replaced_item только в первую страницу (они уже могут быть там)
      let items = addUniqueInvItem(page.items, result.item);
      if (result.replaced_item) items = addUniqueInvItem(items, result.replaced_item);
      return {
        ...page,
        equipment_summary: result.equipment_summary,
        equipped: result.equipment,
        items: idx === 0 ? items : page.items,
      };
    }),
  };
}

/* ── Destroy Confirm ── */
function DestroyConfirmContent({
  data,
  isPending,
  locale,
  onCancel,
  onConfirm,
}: {
  data: DestroyPreview;
  isPending: boolean;
  locale: import("@/lib/i18n").Locale;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const { t } = useI18n();
  return (
    <div style={{
      padding: 18, borderRadius: 12,
      background: "rgba(239,68,68,0.08)",
      border: "1px solid rgba(239,68,68,0.28)",
    }}>
      <div className="mono" style={{ fontSize: 10, letterSpacing: "0.18em", color: "var(--error)", marginBottom: 10, textTransform: "uppercase" }}>
        {t("inventory.destroyPreview")}
      </div>
      <div className="mono" style={{ fontSize: 11, color: "var(--text-mute)", marginBottom: 8 }}>
        {t("inventory.destroyRefund", { count: data.items_count })}{" "}<CopperDisplay value={data.refund_copper} locale={locale} />
      </div>
      <div style={{ fontSize: 11, color: "var(--error)", marginBottom: 12 }}>
        {t("inventory.destroyIrreversible")}
      </div>
      <div style={{ display: "flex", justifyContent: "center", gap: 8 }}>
        <button className="btn" style={{ flex: 1 }} disabled={isPending} onClick={onCancel}>
          {t("common.cancel")}
        </button>
        <button
          className="btn btn-danger"
          style={{ flex: 1 }}
          disabled={isPending || !data.can_destroy}
          onClick={onConfirm}
        >
          {isPending ? t("common.destroying") : t("common.confirm")}
        </button>
      </div>
    </div>
  );
}

function DestroyConfirmModal({
  isLoading,
  data,
  isPending,
  locale,
  onCancel,
  onConfirm,
}: {
  isLoading: boolean;
  data?: DestroyPreview;
  isPending: boolean;
  locale: import("@/lib/i18n").Locale;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  useModalScrollLock();
  const swipeToClose = useSwipeToClose(onCancel);
  const { t } = useI18n();

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal" {...swipeToClose}>
        <div className="card-h">
          <div className="card-title">{t("inventory.destroyPreview")}</div>
        </div>
        <div className="card-body">
          {isLoading ? (
            <LoadingLine label={t("inventory.calculating")} />
          ) : data ? (
            <DestroyConfirmContent
              data={data}
              isPending={isPending}
              locale={locale}
              onCancel={onCancel}
              onConfirm={onConfirm}
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}

/* ── Item Detail Panel ── */
function ItemDetailPanel({
  itemId,
  onChanged,
  compactImage = false,
}: {
  itemId: number | null;
  onChanged: (removedItemId?: number) => void;
  compactImage?: boolean;
}) {
  const [confirmAction, setConfirmAction] = useState<"repair" | "destroy" | null>(null);
  const queryClient = useQueryClient();
  const { t, locale } = useI18n();
  const isMobile = useIsMobile();

  useEffect(() => {
    setConfirmAction(null);
  }, [itemId]);

  const itemQ   = useQuery({ queryKey: ["inventory-item", itemId], queryFn: () => api.item(itemId!), enabled: !!itemId });
  const repairQ = useQuery({
    queryKey: ["repair-preview", [itemId]],
    queryFn: () => api.repairPreview([itemId!]),
    enabled: !!(itemId && confirmAction === "repair"),
  });
  const destroyQ = useQuery({
    queryKey: ["destroy-preview", [itemId]],
    queryFn: () => api.destroyPreview([itemId!]),
    enabled: !!(itemId && confirmAction === "destroy"),
  });

  const applyEquipResult = (result: InventoryMutationResponse) => {
    // Патчим character кеш
    queryClient.setQueryData<Character>(["character"], (current) =>
      current ? { ...current, equipment: result.equipment, stats: result.stats } : current,
    );
    // Патчим infinite inventory кеш (inventory-screen использует InfiniteQuery)
    queryClient.setQueriesData<InfiniteData<Inventory>>(
      {
        predicate: (query) =>
          query.queryKey[0] === "inventory" &&
          Array.isArray((query.state.data as { pages?: unknown[] } | undefined)?.pages),
      },
      (current) => (current ? patchInfiniteInventory(current, result) : current),
    );
    // Патчим plain inventory кеш (character-screen использует useQuery)
    queryClient.setQueryData<Inventory>(["inventory"], (current) =>
      current
        ? {
            ...current,
            equipment_summary: result.equipment_summary,
            equipped: result.equipment,
            items: result.replaced_item
              ? addUniqueInvItem(addUniqueInvItem(current.items, result.item), result.replaced_item)
              : addUniqueInvItem(current.items, result.item),
          }
        : current,
    );
    // Инвалидируем детальную карточку предмета (статус is_equipped мог измениться)
    void queryClient.invalidateQueries({ queryKey: ["inventory-item", itemId] });
    setConfirmAction(null);
    onChanged();
  };

  const invalidateAfterRepair = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["inventory"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-item", itemId] }),
      queryClient.invalidateQueries({ queryKey: ["character"] }),
      queryClient.invalidateQueries({ queryKey: ["me"] }),
    ]);
    setConfirmAction(null);
    onChanged();
  };

  const invalidateAfterDestroy = async (result: { item_ids: number[] }) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["inventory"] }),
      queryClient.invalidateQueries({ queryKey: ["character"] }),
      queryClient.invalidateQueries({ queryKey: ["me"] }),
    ]);
    setConfirmAction(null);
    onChanged(result.item_ids[0]);
  };

  const equipM  = useMutation({
    mutationFn: (item: ItemDetail) => item.is_equipped ? api.unequip(item.id) : api.equip(item.id),
    onSuccess: applyEquipResult,
  });
  const repairM = useMutation({ mutationFn: (ids: number[]) => api.repair(ids), onSuccess: invalidateAfterRepair });
  const destroyM = useMutation({ mutationFn: (ids: number[]) => api.destroy(ids), onSuccess: invalidateAfterDestroy });

  if (!itemId) return (
    <div style={{
      borderRadius: 14, border: "1px dashed var(--line)",
      background: "rgba(17,24,39,0.6)", padding: 24, textAlign: "center",
    }}>
      <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>{t("inventory.noItem")}</div>
      <div style={{ marginTop: 6, fontSize: 12, color: "var(--text-mute)" }}>
        {t("inventory.noItemBody")}
      </div>
    </div>
  );

  if (itemQ.isLoading) return (
    <div className="card card-body"><LoadingLine label={t("inventory.loadingItem")} /></div>
  );
  if (!itemQ.data) return (
    <div className="card card-body"><ErrorNotice message={(itemQ.error as Error | null)?.message} /></div>
  );

  const item   = itemQ.data;
  const color  = rc(item.rarity);
  const durPct = item.durability.current / item.durability.max;
  const itemImage = bestMediaUrl(item.media, ["large_url", "medium_url", "small_url"]);

  return (
    <div className="card animate-fade-in">
      {/* Header image */}
      <div style={{ padding: compactImage ? "48px 16px 0" : "16px 16px 0" }}>
      <div style={{
        width: compactImage ? "85%" : "100%", aspectRatio: "1", flexShrink: 0,
        margin: compactImage ? "0 auto" : undefined,
        background: "var(--bg-3)",
        borderRadius: 8,
        overflow: "hidden",
        position: "relative",
      }}>
        {itemImage ? (
          <img
            src={itemImage}
            alt={item.name}
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", fontSize: 40, opacity: 0.15 }}>⚔</div>
        )}
      </div>
      </div>

      {/* Item identity */}
      <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--line-soft)", textAlign: "center" }}>
        <span className={`tag rare-${item.rarity.toLowerCase()}`}>{t(`rarity.${item.rarity}` as TranslationKey)}</span>
        <div style={{
          fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
          fontSize: 21, fontWeight: 600, marginTop: 6,
          color, letterSpacing: "0.03em", lineHeight: 1.2,
        }}>
          {item.name}
        </div>
        <div className="mono" style={{
          fontSize: 10, letterSpacing: "0.18em", textTransform: "uppercase",
          color: "var(--text-mute)", marginTop: 4,
        }}>
          {t(`slot.${item.slot}` as TranslationKey)} · {t("inventory.forged")}
        </div>
        {item.is_equipped && (
          <span className="mono" style={{
            display: "inline-flex", marginTop: 8,
            background: "rgba(34,197,94,0.15)", padding: "2px 10px",
            borderRadius: 2, fontSize: 10, letterSpacing: "0.12em",
            color: "var(--success)", border: "1px solid rgba(34,197,94,0.25)",
          }}>{t("common.equipped").toUpperCase()}</span>
        )}
      </div>

      {/* Body */}
      <div style={{ padding: 24 }}>
        {/* Stats */}
        <div className="stat-list" style={{ gridTemplateColumns: "1fr", marginBottom: 26 }}>
          {Object.entries(item.stats).map(([k, v]) => (
            <div key={k} className="sl-row" style={{ padding: "8px 0" }}>
              <span className="lbl" style={{ textTransform: "capitalize" }}>{t(`stats.${k}` as TranslationKey)}</span>
              <span className="val">+{v}</span>
            </div>
          ))}
        </div>

        {/* Durability */}
        <div style={{ marginBottom: 26 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <span className="mono" style={{ fontSize: 10, letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--text-mute)" }}>
              {t("common.durability")}
            </span>
            <span className="mono" style={{ fontSize: 11, color: "var(--bone)" }}>
              {item.durability.current} / {item.durability.max}
            </span>
          </div>
          <div className={`bar dur${durPct < 0.20 ? " crit" : durPct < 0.45 ? " warn" : ""}`} style={{ height: 8 }}>
            <i style={{ width: `${durPct * 100}%` }} />
          </div>
          {item.is_broken && (
            <div className="mono" style={{ fontSize: 11, color: "var(--error)", marginTop: 8 }}>
              ⚠ {t("inventory.criticalWear")}
            </div>
          )}
        </div>

        {/* Level + type */}
        <div className="stat-list" style={{ gridTemplateColumns: "1fr", marginBottom: 26 }}>
          <div className="sl-row" style={{ padding: "8px 0" }}>
            <span className="lbl">{t("common.itemLevel")}</span>
            <span className="val">{item.item_level}</span>
          </div>
          <div className="sl-row" style={{ padding: "8px 0" }}>
            <span className="lbl">{t("common.type")}</span>
            <span className="val">{t(`itemType.${item.item_type}` as Parameters<typeof t>[0])}</span>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Primary CTA — equip */}
          <button
            className={`btn${item.is_equipped ? "" : " btn-primary"}`}
            style={{ width: "100%" }}
            disabled={equipM.isPending || (!item.is_equipped && (!item.can_equip || item.is_broken))}
            onClick={() => equipM.mutate(item)}
          >
            {item.is_equipped ? t("common.unequip") : t("common.equip")}
          </button>
          {/* Secondary row — repair + destroy */}
          <div style={{ display: "flex", gap: 14 }}>
            <button
              className="btn btn-primary"
              style={{ flex: 1 }}
              disabled={repairM.isPending || item.durability.current >= item.durability.max}
              onClick={() => setConfirmAction("repair")}
            >
              {t("common.repair")} ◈
            </button>
            <button
              className="btn btn-danger"
              style={{ flex: 1 }}
              disabled={destroyM.isPending}
              onClick={() => setConfirmAction("destroy")}
            >
              {t("common.destroy")}
            </button>
          </div>
        </div>

        {/* Repair / destroy preview */}
        {confirmAction === "repair" && (
          <div style={{ marginTop: 14 }}>
            {repairQ.isLoading ? (
              <LoadingLine label={t("inventory.calculating")} />
            ) : repairQ.data ? (
              <div style={{
                padding: 18, borderRadius: 12,
                background: "rgba(59,130,246,0.08)",
                border: "1px solid rgba(59,130,246,0.25)",
              }}>
                <div className="mono" style={{ fontSize: 10, letterSpacing: "0.18em", color: "var(--primary-bright)", marginBottom: 8, textTransform: "uppercase" }}>
                  {t("inventory.repairPreview")}
                </div>
                <div className="mono" style={{ fontSize: 11, color: "var(--text-mute)", marginBottom: 14 }}>
                  {t("inventory.missingCost", { missing: repairQ.data.durability_missing, cost: repairQ.data.repair_cost_copper })}
                </div>
                <div style={{ display: "flex", justifyContent: "center", gap: 8 }}>
                  <button className="btn" style={{ flex: 1 }} disabled={repairM.isPending} onClick={() => setConfirmAction(null)}>
                    {t("common.cancel")}
                  </button>
                  <button
                    className="btn btn-primary"
                    style={{ flex: 1 }}
                    disabled={repairM.isPending || !repairQ.data.can_repair}
                    onClick={() => repairM.mutate([item.id])}
                  >
                    {repairM.isPending ? t("common.repairing") : t("common.confirm")}
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        )}
        {confirmAction === "destroy" && isMobile && (
          <DestroyConfirmModal
            isLoading={destroyQ.isLoading}
            data={destroyQ.data}
            isPending={destroyM.isPending}
            locale={locale}
            onCancel={() => setConfirmAction(null)}
            onConfirm={() => destroyM.mutate([item.id])}
          />
        )}
        {confirmAction === "destroy" && !isMobile && (
          <div style={{ marginTop: 14 }}>
            {destroyQ.isLoading ? (
              <LoadingLine label={t("inventory.calculating")} />
            ) : destroyQ.data ? (
              <DestroyConfirmContent
                data={destroyQ.data}
                isPending={destroyM.isPending}
                locale={locale}
                onCancel={() => setConfirmAction(null)}
                onConfirm={() => destroyM.mutate([item.id])}
              />
            ) : null}
          </div>
        )}

        <ErrorNotice message={(equipM.error as Error | null)?.message ?? (repairM.error as Error | null)?.message ?? (destroyM.error as Error | null)?.message} />
      </div>
    </div>
  );
}

function BulkActionModal({
  action,
  repairPreview,
  destroyPreview,
  selectedCount,
  isLoading,
  isPending,
  error,
  onCancel,
  onConfirm,
}: {
  action: "repair" | "destroy";
  repairPreview?: RepairPreview;
  destroyPreview?: DestroyPreview;
  selectedCount?: number;
  isLoading: boolean;
  isPending: boolean;
  error?: string;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  useModalScrollLock();
  const swipeToClose = useSwipeToClose(onCancel);

  const { t } = useI18n();
  const isRepair = action === "repair";
  const canConfirm = isRepair ? repairPreview?.can_repair : destroyPreview?.can_destroy;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal" {...swipeToClose}>
        <div className="card-h">
          <div className="card-title">{isRepair ? t("inventory.repairSelected") : t("inventory.destroySelected")}</div>
          <div className="card-sub">{isRepair ? t("inventory.repairSelectedSub") : t("inventory.destroySelectedSub")}</div>
        </div>
        <div className="card-body">
          {isLoading ? (
            <LoadingLine label={t("inventory.calculating")} />
          ) : isRepair && repairPreview ? (
            <div className="stat-list" style={{ gridTemplateColumns: "1fr", marginBottom: 16 }}>
              <div className="sl-row"><span className="lbl">{t("inventory.selectedItems")}</span><span className="val">{selectedCount ?? repairPreview.items_count}</span></div>
              {selectedCount !== undefined && selectedCount !== repairPreview.items_count && (
                <div className="sl-row"><span className="lbl">{t("inventory.itemsToRepair")}</span><span className="val">{repairPreview.items_count}</span></div>
              )}
              <div className="sl-row"><span className="lbl">{t("inventory.repairCost")}</span><span className="val">{repairPreview.repair_cost_copper}c</span></div>
            </div>
          ) : destroyPreview ? (
            <>
              <div className="stat-list" style={{ gridTemplateColumns: "1fr", marginBottom: 12 }}>
                <div className="sl-row"><span className="lbl">{t("inventory.selectedItems")}</span><span className="val">{destroyPreview.items_count}</span></div>
                <div className="sl-row"><span className="lbl">{t("inventory.refund")}</span><span className="val">{destroyPreview.refund_copper}c</span></div>
              </div>
              <div style={{
                padding: 12, borderRadius: 8, border: "1px solid rgba(239,68,68,0.28)",
                background: "rgba(239,68,68,0.08)", color: "var(--error)", fontSize: 12,
              }}>
                {t("inventory.destroyIrreversible")}
              </div>
            </>
          ) : null}
          <ErrorNotice message={error} />
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 18 }}>
            <button className="btn" disabled={isPending} onClick={onCancel}>{t("common.cancel")}</button>
            <button
              className={`btn ${isRepair ? "btn-primary" : "btn-danger"}`}
              disabled={isPending || !canConfirm}
              onClick={onConfirm}
            >
              {isPending ? (isRepair ? t("common.repairing") : t("common.destroying")) : (isRepair ? t("common.repair") : t("common.destroy"))}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════
   Mobile inventory toolbar (count + select toggle + filter dropdown)
═══════════════════════════════════════ */
function MobileInvToolbar({
  itemsCount, slotsLimit, freeSlots, hasItems,
  selectMode, selectedCount, onToggleSelect, onCancelSelect, onRepair, onDestroy,
  filterOptions, rarityFilter, setRarityFilter,
}: {
  itemsCount: number;
  slotsLimit: number | null;
  freeSlots: number | null;
  hasItems: boolean;
  selectMode: boolean;
  selectedCount: number;
  onToggleSelect: () => void;
  onCancelSelect: () => void;
  onRepair: () => void;
  onDestroy: () => void;
  filterOptions: FilterOption[];
  rarityFilter: string | null;
  setRarityFilter: (v: string | null) => void;
}) {
  const { t } = useI18n();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {selectMode && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 12px", borderRadius: 13, background: "rgba(16,22,38,0.75)", border: "1px solid rgba(110,140,190,0.16)" }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="mono" style={{ fontSize: 10, letterSpacing: "0.18em", textTransform: "uppercase", color: "#5d6b86" }}>{t("inventory.quickAction")}</div>
            <div style={{ fontWeight: 600, fontSize: 12, color: "#cdd6e6", marginTop: 1 }}>{t("inventory.selectedCount", { count: selectedCount })}</div>
          </div>
          <button className="btn" style={{ padding: "6px 10px", fontSize: 11 }} onClick={onCancelSelect}>{t("common.cancel")}</button>
          <button className="btn btn-primary" style={{ padding: "6px 10px", fontSize: 11 }} disabled={selectedCount === 0} onClick={onRepair}>{t("common.repair")}</button>
          <button className="btn btn-danger" style={{ padding: "6px 10px", fontSize: 11 }} disabled={selectedCount === 0} onClick={onDestroy}>{t("common.destroy")}</button>
        </div>
      )}

      <MobileSectionToolbar
        title={t("nav.inventory")}
        subtitle={`${slotsLimit === null ? itemsCount : `${itemsCount} / ${slotsLimit}`} ${freeSlots === null ? t("common.noLimit") : t("common.free", { count: freeSlots })}`}
        action={(
          <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <button
              onClick={onToggleSelect}
              disabled={!hasItems && !selectMode}
              aria-label={t("common.select")}
              style={{
                width: 36, height: 36, borderRadius: 10, flexShrink: 0, cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                border: `1px solid ${selectMode ? "rgba(96,165,250,0.4)" : "rgba(110,140,190,0.18)"}`,
                background: selectMode ? "rgba(59,130,246,0.14)" : "rgba(11,16,28,0.5)",
                color: selectMode ? "#9cc0ff" : "#cdd6e6",
              }}
            >
              <ListChecks size={15} />
            </button>
            <MobileFilterDropdown options={filterOptions} active={rarityFilter} onSelect={setRarityFilter} />
          </div>
        )}
      />
    </div>
  );
}

/* ═══════════════════════════════════════
   EquipmentSection (8-col pack + detail pane)
═══════════════════════════════════════ */
function EquipmentSection() {
  const isMobile = useIsMobile();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectMode, setSelectMode] = useState(false);
  const [selectedBulkIds, setSelectedBulkIds] = useState<number[]>([]);
  const [bulkAction, setBulkAction] = useState<"repair" | "destroy" | null>(null);
  const [rarityFilter, setRarityFilter] = useState<string | null>(null);
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const invQ = useInfiniteQuery({
    queryKey: ["inventory", { pageSize: INVENTORY_PAGE_SIZE }],
    queryFn: ({ pageParam }) => api.inventory(pageParam, INVENTORY_PAGE_SIZE),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => (
      lastPage.pagination.has_next ? lastPage.pagination.page + 1 : undefined
    ),
  });

  const inv    = invQ.data?.pages[0];
  const items  = invQ.data?.pages.flatMap((page) => page.items) ?? [];
  const equippedItemIds = new Set(
    Object.values(inv?.equipped ?? {})
      .map((item) => item?.id)
      .filter((id): id is number => typeof id === "number")
  );

  const brokenItems  = items.filter((i) => i.is_broken);
  const itemsCount   = inv?.items_count ?? items.length;
  const slotsLimit   = inv?.slots_limit ?? null;
  const freeSlots    = inv?.free_slots ?? (slotsLimit === null ? null : Math.max(slotsLimit - itemsCount, 0));
  const filteredItems = rarityFilter
    ? items.filter((i) => (i.rarity ?? "").toLowerCase() === rarityFilter)
    : items;
  const packCells    = Array.from(
    { length: Math.max(INVENTORY_PAGE_SIZE, filteredItems.length) },
    (_, i) => filteredItems[i],
  );
  const rarityOptions: FilterOption[] = [
    { value: null, label: t("inventory.filterAll") },
    ...RARITY_RANKS.map((rank) => ({ value: rank, label: rank.toUpperCase(), color: RARITY_COLOR[rank] })),
  ];
  const selectedBulkSet = new Set(selectedBulkIds);
  const itemSheetSwipe = useSwipeToClose(() => setSelectedId(null));

  const repairPreviewQ = useQuery({
    queryKey: ["repair-preview", selectedBulkIds],
    queryFn: () => api.repairPreview(selectedBulkIds),
    enabled: bulkAction === "repair" && selectedBulkIds.length > 0,
  });
  const destroyPreviewQ = useQuery({
    queryKey: ["destroy-preview", selectedBulkIds],
    queryFn: () => api.destroyPreview(selectedBulkIds),
    enabled: bulkAction === "destroy" && selectedBulkIds.length > 0,
  });

  const finishBulkAction = async (removedIds: number[] = []) => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["inventory"] }),
      queryClient.invalidateQueries({ queryKey: ["character"] }),
      queryClient.invalidateQueries({ queryKey: ["me"] }),
    ]);
    if (selectedId !== null && removedIds.includes(selectedId)) {
      setSelectedId(null);
    } else if (selectedId !== null) {
      await queryClient.invalidateQueries({ queryKey: ["inventory-item", selectedId] });
    }
    setSelectedBulkIds([]);
    setSelectMode(false);
    setBulkAction(null);
  };

  const repairBulkM = useMutation({
    mutationFn: (ids: number[]) => api.repair(ids),
    onSuccess: () => finishBulkAction(),
  });
  const destroyBulkM = useMutation({
    mutationFn: (ids: number[]) => api.destroy(ids),
    onSuccess: (result) => finishBulkAction(result.item_ids),
  });

  const toggleBulkItem = (id: number) => {
    setSelectedBulkIds((current) => (
      current.includes(id) ? current.filter((itemId) => itemId !== id) : [...current, id]
    ));
  };

  const cancelSelectMode = () => {
    setSelectMode(false);
    setSelectedBulkIds([]);
    setBulkAction(null);
  };

  const handlePackScroll = (event: UIEvent<HTMLDivElement>) => {
    const node = event.currentTarget;
    const nearBottom = node.scrollHeight - node.scrollTop - node.clientHeight < 120;
    if (nearBottom && invQ.hasNextPage && !invQ.isFetchingNextPage) {
      void invQ.fetchNextPage();
    }
  };

  useEffect(() => {
    if (selectedId !== null && !invQ.isLoading && !invQ.isFetching && !items.some((item) => item.id === selectedId)) {
      setSelectedId(null);
    }
  }, [selectedId, invQ.isLoading, invQ.isFetching, items]);

  if (invQ.isLoading) {
    return <InventoryScreenSkeleton />;
  }

  return (
    <div className="col animate-fade-in">

      {/* ── Left column (cards + grid) + Right column (detail pane) ── */}
      <div style={{
        display: "grid",
        gridTemplateColumns: isMobile ? "1fr" : "minmax(0, 1fr) minmax(320px, 0.42fr)",
        gap: 18, alignItems: "start",
      }}>

        {/* Left column */}
        <div className="col" style={{ gap: 18 }}>

          {/* ── Top stat cards (mobile: compact toolbar) ── */}
          {isMobile ? (
            <MobileInvToolbar
              itemsCount={itemsCount}
              slotsLimit={slotsLimit}
              freeSlots={freeSlots}
              hasItems={items.length > 0}
              selectMode={selectMode}
              selectedCount={selectedBulkIds.length}
              onToggleSelect={() => (selectMode ? cancelSelectMode() : setSelectMode(true))}
              onCancelSelect={cancelSelectMode}
              onRepair={() => setBulkAction("repair")}
              onDestroy={() => setBulkAction("destroy")}
              filterOptions={rarityOptions}
              rarityFilter={rarityFilter}
              setRarityFilter={setRarityFilter}
            />
          ) : (
          <div className="grid-2">
            {/* Pack */}
            <div className="card">
              <div style={{ padding: "15px 16px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <div className="card-sub">{t("nav.inventory")}</div>
                  <div style={{
                    fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                    fontSize: 20, fontWeight: 500, color: "var(--bone)",
                  }}>
                    {slotsLimit === null ? itemsCount : `${itemsCount} / ${slotsLimit}`}
                  </div>
                </div>
                <div className="mono" style={{ fontSize: 11, color: "var(--text-dim)" }}>
                  {freeSlots === null ? t("common.noLimit") : t("common.free", { count: freeSlots })}
                </div>
              </div>
            </div>

            {/* Quick action */}
            <div className="card" style={{ background: "linear-gradient(180deg, rgba(59,130,246,0.12), var(--bg-2))" }}>
              <div style={{ padding: "15px 16px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
                <div style={{ minWidth: 0 }}>
                  <div className="card-sub">{t("inventory.quickAction")}</div>
                  <div style={{
                    fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                    fontSize: 15, fontWeight: 500, color: "var(--bone)",
                  }}>
                    {selectMode ? t("inventory.selectedCount", { count: selectedBulkIds.length }) : t("inventory.selectionMode")}
                  </div>
                </div>
                {selectMode ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
                    <button
                      className="btn btn-ghost"
                      style={{ padding: "8px 12px", color: "var(--text-dim)", fontSize: 13 }}
                      onClick={cancelSelectMode}
                    >
                      {t("common.cancel")}
                    </button>
                    <button
                      className="btn btn-primary"
                      style={{ padding: "8px 14px", fontSize: 13 }}
                      disabled={selectedBulkIds.length === 0}
                      onClick={() => setBulkAction("repair")}
                    >
                      {t("common.repair")}
                    </button>
                    <button
                      className="btn btn-danger"
                      style={{ padding: "8px 14px", fontSize: 13 }}
                      disabled={selectedBulkIds.length === 0}
                      onClick={() => setBulkAction("destroy")}
                    >
                      {t("common.destroy")}
                    </button>
                  </div>
                ) : (
                  <button
                    className="btn btn-primary"
                    disabled={items.length === 0}
                    onClick={() => setSelectMode(true)}
                  >
                    {t("common.select")}
                  </button>
                )}
              </div>
            </div>
          </div>
          )}

          <ErrorNotice message={(invQ.error as Error | null)?.message} />

          {/* ── Pack grid ── */}
          <div className="card">
            {!isMobile && (
            <div className="card-h">
              <div style={{ display: "flex", alignItems: "center", gap: 14, width: "100%", minWidth: 0 }}>
                <div>
                  <div className="card-title">{t("nav.inventory")}</div>
                  <div className="card-sub">{t("inventory.stored")}</div>
                </div>
                <div style={{ marginLeft: "auto" }}>
                  <FilterChips options={rarityOptions} active={rarityFilter} onSelect={setRarityFilter} />
                </div>
              </div>
            </div>
            )}
            <div className="card-body">
              <div
                onScroll={handlePackScroll}
                style={{ maxHeight: 760, overflowY: "auto", paddingRight: 4 }}
              >
                <div className="inv-grid inventory-pack-grid">
                  {packCells.map((item, i) => {
                    return (
                      <PackCell
                        key={item?.id ?? `empty-${i}`}
                        item={item}
                        selected={item?.id === selectedId}
                        multiSelected={item ? selectedBulkSet.has(item.id) : false}
                        equipped={item ? equippedItemIds.has(item.id) : false}
                        onClick={item ? () => (selectMode ? toggleBulkItem(item.id) : setSelectedId(item.id)) : undefined}
                      />
                    );
                  })}
                </div>
                {invQ.isFetchingNextPage && <LoadingLine label={t("inventory.loadingMore")} />}
              </div>

              {items.length === 0 && !invQ.isLoading && (
                <div style={{
                  textAlign: "center", padding: "40px 20px",
                  border: "1px dashed var(--line)", borderRadius: 10,
                }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-dim)" }}>{t("inventory.empty")}</div>
                  <div style={{ fontSize: 12, color: "var(--text-mute)", marginTop: 6 }}>
                    {t("inventory.emptyBody")}
                  </div>
                </div>
              )}
            </div>
          </div>

        </div>{/* end left column */}

        {/* Right column — item detail (desktop only; mobile uses bottom sheet) */}
        {!isMobile && (
          <aside className="inventory-detail-pane" style={{ marginTop: 94 }}>
            <ItemDetailPanel
              itemId={selectedId}
              onChanged={(removedItemId) => {
                if (removedItemId && removedItemId === selectedId) {
                  setSelectedId(null);
                }
              }}
            />
          </aside>
        )}

      </div>

      {/* Mobile: selected item detail as a bottom sheet */}
      {isMobile && selectedId !== null && (
        <>
          <div className="mobile-sheet-overlay" onClick={() => setSelectedId(null)} />
          <div className="mobile-sheet animate-sheet-up mobile-noscroll" style={{
            maxHeight: "85%", overflowY: "auto", position: "fixed",
            padding: "0 0 calc(env(safe-area-inset-bottom, 0px) + 16px)",
          }} {...itemSheetSwipe}>
          <div className="mobile-sheet-grabber" />
          <button
            type="button"
            onClick={() => setSelectedId(null)}
            aria-label={t("miniGame.close")}
            style={{
              position: "absolute", top: 14, right: 14, zIndex: 2,
              width: 34, height: 34, borderRadius: 10,
              display: "flex", alignItems: "center", justifyContent: "center",
              border: "1px solid rgba(110,140,190,0.18)",
              background: "rgba(11,16,28,0.72)",
              color: "#aeb9cc", cursor: "pointer",
            }}
          >
            <X size={17} strokeWidth={2.2} />
          </button>
            <ItemDetailPanel
              itemId={selectedId}
              compactImage
              onChanged={(removedItemId) => {
                if (removedItemId && removedItemId === selectedId) {
                  setSelectedId(null);
                }
              }}
            />
          </div>
        </>
      )}
      {bulkAction && (
        <BulkActionModal
          action={bulkAction}
          repairPreview={repairPreviewQ.data}
          destroyPreview={destroyPreviewQ.data}
          selectedCount={selectedBulkIds.length}
          isLoading={bulkAction === "repair" ? repairPreviewQ.isLoading : destroyPreviewQ.isLoading}
          isPending={bulkAction === "repair" ? repairBulkM.isPending : destroyBulkM.isPending}
          error={
            bulkAction === "repair"
              ? ((repairPreviewQ.error as Error | null)?.message ?? (repairBulkM.error as Error | null)?.message)
              : ((destroyPreviewQ.error as Error | null)?.message ?? (destroyBulkM.error as Error | null)?.message)
          }
          onCancel={() => setBulkAction(null)}
          onConfirm={() => {
            if (bulkAction === "repair") {
              repairBulkM.mutate(selectedBulkIds);
            } else {
              destroyBulkM.mutate(selectedBulkIds);
            }
          }}
        />
      )}
    </div>
  );
}

/* ── Consumables grid cell ── */
type ConsumableCell =
  | { kind: "ingredient"; data: Ingredient; stack: number }
  | { kind: "potion"; data: Potion; stack: number };

function ConsumableGridCell({ cell, disabled, onUse }: { cell: ConsumableCell; disabled?: boolean; onUse?: () => void }) {
  const media = cell.data.media;
  const iconUrl = bestMediaUrl(media, ["medium_url", "small_url", "large_url"]);
  const isPotion = cell.kind === "potion";
  return (
    <button
      type="button"
      className={`consumable-cell${isPotion ? " is-potion" : ""}`}
      disabled={!isPotion || disabled}
      onClick={isPotion ? onUse : undefined}
      title={cell.data.name}
      aria-label={`${cell.data.name} ×${cell.stack}`}
    >
      {iconUrl ? (
        <img src={iconUrl} alt={cell.data.name} className="inv-icon" />
      ) : (
        <span className="cc-fallback">{cell.data.name}</span>
      )}
      <span className={`consumable-kind ${cell.kind}`}>
        {isPotion ? <FlaskConical size={9} strokeWidth={2.5} /> : <Leaf size={9} strokeWidth={2.5} />}
      </span>
      <span className="consumable-count">×{cell.stack}</span>
    </button>
  );
}

/* ── Craft panel (circular layout, batch stepper) ── */
function ringPosition(index: number, total: number, radius: number) {
  // Старт сверху (-90°), по часовой стрелке; центр контейнера = 50%/50%.
  const angle = (-90 + (360 / total) * index) * (Math.PI / 180);
  return {
    left: `calc(50% + ${Math.cos(angle) * radius}px)`,
    top: `calc(50% + ${Math.sin(angle) * radius}px)`,
  };
}

function CraftPanel({ ownedByIngredientId }: { ownedByIngredientId: Map<number, number> }) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [difficulty, setDifficulty] = useState<CraftRecipe["difficulty"]>("small");
  const [batch, setBatch] = useState(1);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const recipesQ = useQuery({ queryKey: ["craft-recipes"], queryFn: () => api.craftRecipes() });
  const recipes = recipesQ.data ?? [];
  const recipe = recipes.find((r) => r.difficulty === difficulty) ?? null;

  const maxBatch = useMemo(() => {
    if (!recipe || recipe.ingredients.length === 0) return 0;
    return recipe.ingredients.reduce((min, ing) => {
      const owned = ownedByIngredientId.get(ing.ingredient_id) ?? 0;
      return Math.min(min, Math.floor(owned / ing.quantity));
    }, Infinity);
  }, [recipe, ownedByIngredientId]);

  // При смене рецепта/запасов держим batch в допустимом диапазоне.
  useEffect(() => {
    setBatch((b) => Math.min(Math.max(b, 1), Math.max(maxBatch, 1)));
  }, [maxBatch, difficulty]);

  const craftM = useMutation({
    mutationFn: (body: { recipe_id: number; quantity: number }) => api.craftPotions(body),
    onSuccess: (res) => {
      void queryClient.invalidateQueries({ queryKey: ["ingredients"] });
      void queryClient.invalidateQueries({ queryKey: ["potions"] });
      void queryClient.invalidateQueries({ queryKey: ["character"] });
      setSuccessMsg(t("craft.success", { count: res.crafted, name: recipe?.potion.name ?? res.potion_code }));
    },
  });

  const difficulties: { key: CraftRecipe["difficulty"]; label: string }[] = [
    { key: "small", label: t("craft.difficultySmall") },
    { key: "medium", label: t("craft.difficultyMedium") },
    { key: "large", label: t("craft.difficultyLarge") },
  ];

  const centerIcon = bestMediaUrl(recipe?.potion.media, ["medium_url", "large_url", "small_url"]);

  return (
    <div className="card animate-fade-in">
      <div className="card-h">
        <div className="card-title">{t("craft.title")}</div>
        <div className="card-sub">{t("craft.subtitle")}</div>
      </div>
      <div className="card-body">
        {recipesQ.isLoading ? (
          <LoadingLine label={t("craft.title")} />
        ) : recipes.length === 0 ? (
          <div style={{ fontSize: 12, color: "var(--text-mute)", textAlign: "center", padding: "24px 0" }}>
            {t("craft.noRecipes")}
          </div>
        ) : (
          <>
            <div className="craft-difficulty-tabs" role="tablist">
              {difficulties.map((d) => (
                <button
                  key={d.key}
                  role="tab"
                  aria-selected={difficulty === d.key}
                  className="craft-difficulty-tab"
                  disabled={!recipes.some((r) => r.difficulty === d.key)}
                  onClick={() => { setDifficulty(d.key); setSuccessMsg(null); craftM.reset(); }}
                >
                  {d.label}
                </button>
              ))}
            </div>

            {recipe && (
              <>
                {/* Круговая раскладка: центр (зелье) + N ингредиентов по кольцу */}
                <div className="craft-circle">
                  <div className="craft-node center" title={recipe.potion.name}>
                    {centerIcon
                      ? <img src={centerIcon} alt={recipe.potion.name} />
                      : <FlaskConical size={30} strokeWidth={1.5} color="var(--success)" />}
                  </div>
                  {recipe.ingredients.map((ing, i) => {
                    const icon = bestMediaUrl(ing.media, ["small_url", "medium_url", "large_url"]);
                    return (
                      <div
                        key={ing.ingredient_id}
                        className="craft-node ingredient"
                        style={ringPosition(i, recipe.ingredients.length, 96)}
                        title={ing.name}
                      >
                        {icon ? <img src={icon} alt={ing.name} /> : <span className="cn-fallback">{ing.name}</span>}
                      </div>
                    );
                  })}
                </div>

                {/* Требования по ингредиентам (recipe_qty × batch vs запас) */}
                <div className="craft-ing-rows">
                  {recipe.ingredients.map((ing) => {
                    const owned = ownedByIngredientId.get(ing.ingredient_id) ?? 0;
                    const need = ing.quantity * batch;
                    return (
                      <div key={ing.ingredient_id} className={`craft-ing-row${owned < need ? " short" : ""}`}>
                        <span className="name">{ing.name}</span>
                        <span className="req">{t("craft.requires", { quantity: need, owned })}</span>
                      </div>
                    );
                  })}
                </div>

                {/* Батч-степпер */}
                <div className="craft-batch">
                  <span className="craft-batch-label">{t("craft.batch")}</span>
                  <div className="craft-batch-stepper">
                    <button
                      type="button"
                      className="craft-step-btn"
                      aria-label="-"
                      disabled={batch <= 1}
                      onClick={() => setBatch((b) => Math.max(1, b - 1))}
                    >
                      <Minus size={16} strokeWidth={2.5} />
                    </button>
                    <span className="craft-batch-value">{batch}</span>
                    <button
                      type="button"
                      className="craft-step-btn"
                      aria-label="+"
                      disabled={batch >= maxBatch}
                      onClick={() => setBatch((b) => Math.min(maxBatch, b + 1))}
                    >
                      <Plus size={16} strokeWidth={2.5} />
                    </button>
                  </div>
                </div>

                {recipe.required_hero_level > 1 && (
                  <div style={{ fontSize: 11, color: "var(--text-mute)", marginBottom: 12 }}>
                    {t("craft.requiredLevel", { level: recipe.required_hero_level })}
                  </div>
                )}

                <button
                  className="btn btn-primary"
                  style={{ width: "100%" }}
                  disabled={maxBatch === 0 || craftM.isPending}
                  onClick={() => { setSuccessMsg(null); craftM.mutate({ recipe_id: recipe.id, quantity: batch }); }}
                >
                  {craftM.isPending ? t("craft.crafting") : maxBatch === 0 ? t("craft.notEnough") : t("craft.create")}
                </button>

                {successMsg && (
                  <div style={{
                    marginTop: 12, padding: "10px 12px", borderRadius: 8,
                    background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.3)",
                    color: "var(--success)", fontSize: 12, textAlign: "center",
                  }}>
                    {successMsg}
                  </div>
                )}
                <ErrorNotice message={(craftM.error as Error | null)?.message} />
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════
   ConsumablesSection (7-col grid + craft panel)
═══════════════════════════════════════ */
function ConsumablesSection() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const isMobile = useIsMobile();
  const [consumableFilter, setConsumableFilter] = useState<string | null>(null);
  const ingredientsQ = useQuery({ queryKey: ["ingredients"], queryFn: () => api.ingredients() });
  const potionsQ = useQuery({ queryKey: ["potions"], queryFn: () => api.potions() });

  const ingredients = ingredientsQ.data ?? [];
  const potions = potionsQ.data ?? [];

  const ownedByIngredientId = useMemo(() => {
    const map = new Map<number, number>();
    for (const ing of ingredients) map.set(ing.id, ing.count);
    return map;
  }, [ingredients]);

  const cells: ConsumableCell[] = [
    ...ingredients.flatMap((ing) =>
      splitToStacks(ing.count).map((stack) => ({ kind: "ingredient" as const, data: ing, stack })),
    ),
    ...potions.flatMap((pot) =>
      splitToStacks(pot.count).map((stack) => ({ kind: "potion" as const, data: pot, stack })),
    ),
  ];
  const filteredCells = consumableFilter ? cells.filter((cell) => cell.kind === consumableFilter) : cells;
  const consumableOptions: FilterOption[] = [
    { value: null, label: t("inventory.filterAll") },
    { value: "ingredient", label: t("inventory.filterIngredients") },
    { value: "potion", label: t("inventory.filterPotions") },
  ];

  const useM = useMutation({
    mutationFn: (potionId: number) => api.usePotion({ potion_id: potionId, quantity: 1 }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["potions"] });
      void queryClient.invalidateQueries({ queryKey: ["character"] });
    },
  });

  const isLoading = ingredientsQ.isLoading || potionsQ.isLoading;

  return (
    <div className="inventory-main-layout">
      <div className="col" style={{ gap: isMobile ? 18 : 0 }}>
        {isMobile && (
          <MobileSectionToolbar
            title={t("inventory.consumables")}
            subtitle={t("inventory.consumablesSub")}
            action={(
              <MobileFilterDropdown
                options={consumableOptions}
                active={consumableFilter}
                onSelect={setConsumableFilter}
                menuLayout="list"
              />
            )}
          />
        )}

        <div className="card">
          {!isMobile && (
          <div className="card-h">
            <div style={{ display: "flex", alignItems: "center", gap: 14, width: "100%", minWidth: 0 }}>
              <div>
                <div className="card-title">{t("inventory.consumables")}</div>
                <div className="card-sub">{t("inventory.consumablesSub")}</div>
              </div>
              <div style={{ marginLeft: "auto", flexShrink: 0 }}>
                <FilterChips options={consumableOptions} active={consumableFilter} onSelect={setConsumableFilter} />
              </div>
            </div>
          </div>
          )}
          <div className="card-body">
            {isLoading ? (
              <LoadingLine label={t("inventory.consumables")} />
            ) : cells.length === 0 ? (
              <div style={{
                textAlign: "center", padding: "40px 20px",
                border: "1px dashed var(--line)", borderRadius: 10,
              }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-dim)" }}>{t("inventory.consumablesEmpty")}</div>
                <div style={{ fontSize: 12, color: "var(--text-mute)", marginTop: 6 }}>{t("inventory.consumablesEmptyBody")}</div>
              </div>
            ) : (
              <div className="consumables-grid">
                {filteredCells.map((cell, i) => (
                  <ConsumableGridCell
                    key={`${cell.kind}-${cell.data.id}-${i}`}
                    cell={cell}
                    disabled={useM.isPending}
                    onUse={cell.kind === "potion" ? () => useM.mutate(cell.data.id) : undefined}
                  />
                ))}
              </div>
            )}
            <ErrorNotice message={(useM.error as Error | null)?.message ?? (ingredientsQ.error as Error | null)?.message ?? (potionsQ.error as Error | null)?.message} />
          </div>
        </div>
      </div>

      <aside className="inventory-detail-pane">
        <CraftPanel ownedByIngredientId={ownedByIngredientId} />
      </aside>
    </div>
  );
}

/* ═══════════════════════════════════════
   InventoryScreen (section switcher)
═══════════════════════════════════════ */
export function InventoryScreen() {
  const { t } = useI18n();
  const [section, setSection] = useState<"equipment" | "consumables">("equipment");

  return (
    <div className="col animate-fade-in" style={{ gap: 16 }}>
      <div className="inv-section-tabs" role="tablist">
        <button
          role="tab"
          aria-selected={section === "equipment"}
          className="inv-section-tab"
          onClick={() => setSection("equipment")}
        >
          {t("inventory.sectionEquipment")}
        </button>
        <button
          role="tab"
          aria-selected={section === "consumables"}
          className="inv-section-tab"
          onClick={() => setSection("consumables")}
        >
          {t("inventory.sectionConsumables")}
        </button>
      </div>

      {section === "equipment" ? <EquipmentSection /> : <ConsumablesSection />}
    </div>
  );
}
