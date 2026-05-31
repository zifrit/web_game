"use client";

import { useInfiniteQuery, useMutation, useQuery, useQueryClient, type InfiniteData } from "@tanstack/react-query";
import { useEffect, useState, type UIEvent } from "react";
import { useI18n } from "@/components/providers";
import { ErrorNotice, InventoryScreenSkeleton, LoadingLine } from "@/components/ui";
import { api } from "@/lib/api";
import type { TranslationKey } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import type { Character, DestroyPreview, Inventory, InventoryCard, InventoryMutationResponse, ItemDetail, RepairPreview } from "@/lib/types";

const INVENTORY_PAGE_SIZE = 24;

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
      {equipped && <div className="equipped-tag">E</div>}
      {item?.is_broken && <div className="broken-tag">!</div>}
      {multiSelected && (
        <div style={{
          position: "absolute", right: 5, bottom: 5, width: 18, height: 18,
          borderRadius: 999, background: "var(--success)", color: "#fff",
          display: "grid", placeItems: "center", fontSize: 12, fontWeight: 800,
          border: "1px solid rgba(255,255,255,0.5)",
        }}>✓</div>
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

/* ── Item Detail Panel ── */
function ItemDetailPanel({ itemId, onChanged }: { itemId: number | null; onChanged: (removedItemId?: number) => void }) {
  const [confirmAction, setConfirmAction] = useState<"repair" | "destroy" | null>(null);
  const queryClient = useQueryClient();
  const { t } = useI18n();

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
      <div style={{ padding: "16px 16px 0" }}>
      <div style={{
        width: "100%", aspectRatio: "1", flexShrink: 0,
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
            borderRadius: 2, fontSize: 9, letterSpacing: "0.15em",
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
            <span className="val">{item.item_type}</span>
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
                <div className="mono" style={{ fontSize: 9, letterSpacing: "0.18em", color: "var(--primary-bright)", marginBottom: 8, textTransform: "uppercase" }}>
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
        {confirmAction === "destroy" && (
          <div style={{ marginTop: 14 }}>
            {destroyQ.isLoading ? (
              <LoadingLine label={t("inventory.calculating")} />
            ) : destroyQ.data ? (
              <div style={{
                padding: 18, borderRadius: 12,
                background: "rgba(239,68,68,0.08)",
                border: "1px solid rgba(239,68,68,0.28)",
              }}>
                <div className="mono" style={{ fontSize: 9, letterSpacing: "0.18em", color: "var(--error)", marginBottom: 10, textTransform: "uppercase" }}>
                  {t("inventory.destroyPreview")}
                </div>
                <div className="mono" style={{ fontSize: 11, color: "var(--text-mute)", marginBottom: 8 }}>
                  {t("inventory.destroyRefund", { count: destroyQ.data.items_count, refund: destroyQ.data.refund_copper })}
                </div>
                <div style={{ fontSize: 11, color: "var(--error)", marginBottom: 12 }}>
                  {t("inventory.destroyIrreversible")}
                </div>
                <div style={{ display: "flex", justifyContent: "center", gap: 8 }}>
                  <button className="btn" style={{ flex: 1 }} disabled={destroyM.isPending} onClick={() => setConfirmAction(null)}>
                    {t("common.cancel")}
                  </button>
                  <button
                    className="btn btn-danger"
                    style={{ flex: 1 }}
                    disabled={destroyM.isPending || !destroyQ.data.can_destroy}
                    onClick={() => destroyM.mutate([item.id])}
                  >
                    {destroyM.isPending ? t("common.destroying") : t("common.confirm")}
                  </button>
                </div>
              </div>
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
  isLoading,
  isPending,
  error,
  onCancel,
  onConfirm,
}: {
  action: "repair" | "destroy";
  repairPreview?: RepairPreview;
  destroyPreview?: DestroyPreview;
  isLoading: boolean;
  isPending: boolean;
  error?: string;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const { t } = useI18n();
  const isRepair = action === "repair";
  const canConfirm = isRepair ? repairPreview?.can_repair : destroyPreview?.can_destroy;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal">
        <div className="card-h">
          <div className="card-title">{isRepair ? t("inventory.repairSelected") : t("inventory.destroySelected")}</div>
          <div className="card-sub">{isRepair ? t("inventory.repairSelectedSub") : t("inventory.destroySelectedSub")}</div>
        </div>
        <div className="card-body">
          {isLoading ? (
            <LoadingLine label={t("inventory.calculating")} />
          ) : isRepair && repairPreview ? (
            <div className="stat-list" style={{ gridTemplateColumns: "1fr", marginBottom: 16 }}>
              <div className="sl-row"><span className="lbl">{t("inventory.selectedItems")}</span><span className="val">{repairPreview.items_count}</span></div>
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
   InventoryScreen
═══════════════════════════════════════ */
export function InventoryScreen() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectMode, setSelectMode] = useState(false);
  const [selectedBulkIds, setSelectedBulkIds] = useState<number[]>([]);
  const [bulkAction, setBulkAction] = useState<"repair" | "destroy" | null>(null);
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
  const packCells    = Array.from(
    { length: Math.max(INVENTORY_PAGE_SIZE, items.length) },
    (_, i) => items[i],
  );
  const selectedBulkSet = new Set(selectedBulkIds);

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
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(320px, 0.42fr)", gap: 18, alignItems: "start" }}>

        {/* Left column */}
        <div className="col" style={{ gap: 18 }}>

          {/* ── Top stat cards ── */}
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

          <ErrorNotice message={(invQ.error as Error | null)?.message} />

          {/* ── Pack grid ── */}
          <div className="card">
            <div className="card-h">
              <div className="card-title">{t("nav.inventory")}</div>
              <div className="card-sub">{t("inventory.stored")}</div>
            </div>
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

        {/* Right column — item detail */}
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

      </div>
      {bulkAction && (
        <BulkActionModal
          action={bulkAction}
          repairPreview={repairPreviewQ.data}
          destroyPreview={destroyPreviewQ.data}
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
