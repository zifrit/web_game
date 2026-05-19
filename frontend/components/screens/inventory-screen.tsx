"use client";

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type UIEvent } from "react";
import { useI18n } from "@/components/providers";
import { ErrorNotice, LoadingLine } from "@/components/ui";
import { api } from "@/lib/api";
import type { TranslationKey } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import type { InventoryCard, ItemDetail } from "@/lib/types";

const INVENTORY_PAGE_SIZE = 24;

/* ── Rarity helpers ── */
const RARITY_COLOR: Record<string, string> = {
  common:   "#9CA3AF",
  uncommon: "#22C55E",
  rare:     "#3B82F6",
  epic:     "#A855F7",
  legendary:"#F59E0B",
};
const RARITY_GLOW: Record<string, string> = {
  common:   "rgba(156,163,175,0.25)",
  uncommon: "rgba(34,197,94,0.30)",
  rare:     "rgba(59,130,246,0.35)",
  epic:     "rgba(168,85,247,0.35)",
  legendary:"rgba(245,158,11,0.35)",
};
function rc(rarity?: string) { return RARITY_COLOR[(rarity ?? "common").toLowerCase()] ?? RARITY_COLOR.common; }
function rg(rarity?: string) { return RARITY_GLOW[(rarity ?? "common").toLowerCase()]  ?? RARITY_GLOW.common;  }

/* ── Pack grid cell ── */
function PackCell({
  item,
  selected,
  equipped,
  onClick,
}: {
  item?: InventoryCard;
  selected?: boolean;
  equipped?: boolean;
  onClick?: () => void;
}) {
  const color   = item ? rc(item.rarity) : undefined;
  const hasItem = Boolean(item);
  const iconUrl = item?.icon_url ?? "";
  const itemName = item?.name ?? "";
  return (
    <button
      type="button"
      disabled={!hasItem}
      onClick={onClick}
      className={`inv-cell${hasItem ? "" : " empty"}`}
      style={hasItem ? {
        borderColor: selected ? "var(--primary)" : color,
        boxShadow: selected
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
    </button>
  );
}

/* ── Item Detail Panel ── */
function ItemDetailPanel({ itemId, onChanged }: { itemId: number | null; onChanged: () => void }) {
  const [showRepair, setShowRepair] = useState(false);
  const queryClient = useQueryClient();
  const { t } = useI18n();

  const itemQ   = useQuery({ queryKey: ["inventory-item", itemId], queryFn: () => api.item(itemId!), enabled: !!itemId });
  const repairQ = useQuery({
    queryKey: ["repair-preview", itemId],
    queryFn: () => api.repairPreview(itemId!),
    enabled: !!(itemId && showRepair),
  });

  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["inventory"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-item", itemId] }),
      queryClient.invalidateQueries({ queryKey: ["character"] }),
      queryClient.invalidateQueries({ queryKey: ["me"] }),
    ]);
    setShowRepair(false);
    onChanged();
  };

  const equipM  = useMutation({ mutationFn: (item: ItemDetail) => item.is_equipped ? api.unequip(item.id) : api.equip(item.id), onSuccess: invalidate });
  const repairM = useMutation({ mutationFn: (id: number) => api.repair(id), onSuccess: invalidate });

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
  const itemImage = bestMediaUrl(item.media, ["large_url", "medium_url", "small_url", "icon_url", "original_url"]);

  return (
    <div className="card animate-fade-in">
      {/* Header */}
      <div style={{
        padding: "20px 24px", borderBottom: "1px solid var(--line-soft)",
        display: "flex", flexDirection: "column", alignItems: "center", gap: 14,
      }}>
        {/* Item icon placeholder */}
        <div style={{
          width: "min(320px, 100%)", aspectRatio: "1", borderRadius: 4, flexShrink: 0,
          background: "repeating-linear-gradient(45deg, var(--bg-3) 0 6px, var(--bg-2) 6px 12px)",
          border: `1px solid ${color}`,
          overflow: "hidden",
          position: "relative",
        }}>
          {itemImage && (
            <img
              src={itemImage}
              alt={item.name}
              style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
            />
          )}
        </div>
        <div style={{ width: "100%", textAlign: "center" }}>
          <span className={`tag rare-${item.rarity.toLowerCase()}`}>{t(`rarity.${item.rarity}` as TranslationKey)}</span>
          <div style={{
            fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
            fontSize: 26, fontWeight: 600, marginTop: 6,
            color, letterSpacing: "0.03em",
          }}>
            {item.name}
          </div>
          <div className="mono" style={{
            fontSize: 10, letterSpacing: "0.18em", textTransform: "uppercase",
            color: "var(--text-mute)",
          }}>
            {t(`slot.${item.slot}` as TranslationKey)} · {t("inventory.forged")}
          </div>
          {item.is_equipped && (
            <span className="mono" style={{
              display: "inline-flex", marginTop: 8,
              background: "rgba(34,197,94,0.15)", padding: "2px 8px",
              borderRadius: 2, fontSize: 9, letterSpacing: "0.15em",
              color: "var(--success)",
            }}>{t("common.equipped").toUpperCase()}</span>
          )}
        </div>
      </div>

      {/* Body */}
      <div style={{ padding: 24 }}>
        {/* Stats */}
        <div className="stat-list" style={{ gridTemplateColumns: "1fr", marginBottom: 18 }}>
          {Object.entries(item.stats).map(([k, v]) => (
            <div key={k} className="sl-row">
              <span className="lbl" style={{ textTransform: "capitalize" }}>{t(`stats.${k}` as TranslationKey)}</span>
              <span className="val">+{v}</span>
            </div>
          ))}
        </div>

        {/* Durability */}
        <div style={{ marginBottom: 18 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
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
            <div className="mono" style={{ fontSize: 11, color: "var(--error)", marginTop: 6 }}>
              ⚠ {t("inventory.criticalWear")}
            </div>
          )}
        </div>

        {/* Level + type */}
        <div className="stat-list" style={{ gridTemplateColumns: "1fr", marginBottom: 18 }}>
          <div className="sl-row">
            <span className="lbl">{t("common.itemLevel")}</span>
            <span className="val">{item.item_level}</span>
          </div>
          <div className="sl-row">
            <span className="lbl">{t("common.type")}</span>
            <span className="val">{item.item_type}</span>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 10 }}>
          {item.durability.current < item.durability.max && (
            <button
              className="btn"
              style={{ flex: 1 }}
              disabled={repairM.isPending}
              onClick={() => setShowRepair(true)}
            >
              {t("common.repair")} ◈ —
            </button>
          )}
          <button
            className="btn btn-primary"
            style={{ flex: 1 }}
            disabled={equipM.isPending || (!item.is_equipped && (!item.can_equip || item.is_broken))}
            onClick={() => equipM.mutate(item)}
          >
            {item.is_equipped ? t("common.unequip") : t("common.equip")}
          </button>
        </div>

        {/* Repair preview */}
        {showRepair && (
          <div style={{ marginTop: 14 }}>
            {repairQ.isLoading ? (
              <LoadingLine label={t("inventory.calculating")} />
            ) : repairQ.data ? (
              <div style={{
                padding: 14, borderRadius: 12,
                background: "rgba(59,130,246,0.08)",
                border: "1px solid rgba(59,130,246,0.25)",
                display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12,
              }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>{t("inventory.repairPreview")}</div>
                  <div className="mono" style={{ fontSize: 11, color: "var(--text-mute)", marginTop: 2 }}>
                    {t("inventory.missingCost", { missing: repairQ.data.durability.missing, cost: repairQ.data.repair_cost_copper })}
                  </div>
                </div>
                <button
                  className="btn btn-primary"
                  disabled={repairM.isPending || !repairQ.data.can_repair}
                  onClick={() => repairM.mutate(item.id)}
                >
                  {repairM.isPending ? t("common.repairing") : t("common.confirm")}
                </button>
              </div>
            ) : null}
          </div>
        )}

        <ErrorNotice message={(equipM.error as Error | null)?.message ?? (repairM.error as Error | null)?.message} />
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════
   InventoryScreen
═══════════════════════════════════════ */
export function InventoryScreen() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { t } = useI18n();
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
  const totalCost    = brokenItems.length * 50; // placeholder
  const itemsCount   = inv?.items_count ?? items.length;
  const slotsLimit   = inv?.slots_limit ?? null;
  const freeSlots    = inv?.free_slots ?? (slotsLimit === null ? null : Math.max(slotsLimit - itemsCount, 0));
  const packCells    = Array.from(
    { length: Math.max(INVENTORY_PAGE_SIZE, items.length) },
    (_, i) => items[i],
  );

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

  return (
    <div className="col animate-fade-in">

      {/* ── Top stat cards ── */}
      <div className="grid-3">
        {/* Pack */}
        <div className="card">
          <div className="card-body" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div className="card-sub">{t("nav.inventory")}</div>
              <div style={{
                fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                fontSize: 26, fontWeight: 500, color: "var(--bone)",
              }}>
                {slotsLimit === null ? itemsCount : `${itemsCount} / ${slotsLimit}`}
              </div>
            </div>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-dim)" }}>
              {freeSlots === null ? t("common.noLimit") : t("common.free", { count: freeSlots })}
            </div>
          </div>
        </div>

        {/* Needs repair */}
        <div className="card">
          <div className="card-body" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div className="card-sub">{t("inventory.needsRepair")}</div>
              <div style={{
                fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                fontSize: 26, fontWeight: 500,
                color: brokenItems.length ? "var(--primary-bright)" : "var(--text-dim)",
              }}>
                {t("common.items", { count: brokenItems.length })}
              </div>
            </div>
            <div className="mono" style={{ fontSize: 11, color: "var(--text-dim)" }}>
              {t("inventory.cost")} ◈ {totalCost}
            </div>
          </div>
        </div>

        {/* Quick action */}
        <div className="card" style={{ background: "linear-gradient(180deg, rgba(59,130,246,0.12), var(--bg-2))" }}>
          <div className="card-body" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
            <div style={{ minWidth: 0 }}>
              <div className="card-sub">{t("inventory.quickAction")}</div>
              <div style={{
                fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                fontSize: 18, fontWeight: 500, color: "var(--bone)",
              }}>
                {t("inventory.repairPack")}
              </div>
            </div>
            <button
              className="btn btn-primary"
              disabled={brokenItems.length === 0}
            >
              {t("inventory.repairAll")}
            </button>
          </div>
        </div>
      </div>

      <ErrorNotice message={(invQ.error as Error | null)?.message} />
      {invQ.isLoading && <LoadingLine label={t("inventory.loading")} />}

      {/* ── Pack grid + selected item detail ── */}
      <div className="inventory-main-layout">
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
                      equipped={item ? equippedItemIds.has(item.id) : false}
                      onClick={item ? () => setSelectedId(item.id) : undefined}
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

        <aside className="inventory-detail-pane">
          <ItemDetailPanel
            itemId={selectedId}
            onChanged={() => {/* keep selection */}}
          />
        </aside>
      </div>
    </div>
  );
}
