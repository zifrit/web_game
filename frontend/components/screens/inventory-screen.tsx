"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Hammer, Shirt, Wrench } from "lucide-react";
import { useState } from "react";
import {
  Button,
  EmptyState,
  ErrorNotice,
  ItemGlyph,
  LoadingLine,
  Panel,
  StatBadge,
  formatCopper,
  formatStatName
} from "@/components/ui";
import { api } from "@/lib/api";
import type { EquipmentSlot, InventoryCard, ItemDetail } from "@/lib/types";

const slots: EquipmentSlot[] = ["weapon", "helmet", "armor", "boots", "ring"];

function ItemButton({
  item,
  selected,
  onSelect
}: {
  item: InventoryCard;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      className={`flex min-h-20 items-center gap-3 rounded-md border p-3 text-left transition ${
        selected
          ? "border-brass bg-brass/15"
          : "border-white/10 bg-white/[0.04] hover:bg-white/[0.08]"
      }`}
      onClick={onSelect}
      type="button"
    >
      <ItemGlyph broken={item.is_broken} rarity={item.rarity} src={item.icon_url} />
      <div>
        <div className="font-bold capitalize text-parchment">{item.rarity}</div>
        <div className="text-sm text-parchment/60">Item #{item.id}</div>
        {item.is_broken ? (
          <div className="mt-1 text-xs font-bold uppercase text-[#ff9aa3]">
            Broken
          </div>
        ) : null}
      </div>
    </button>
  );
}

function ItemDetailPanel({
  itemId,
  onChanged
}: {
  itemId: number | null;
  onChanged: () => void;
}) {
  const [showRepairPreview, setShowRepairPreview] = useState(false);
  const queryClient = useQueryClient();

  const itemQuery = useQuery({
    queryKey: ["inventory-item", itemId],
    queryFn: () => api.item(itemId ?? 0),
    enabled: Boolean(itemId)
  });

  const repairPreviewQuery = useQuery({
    queryKey: ["repair-preview", itemId],
    queryFn: () => api.repairPreview(itemId ?? 0),
    enabled: Boolean(itemId && showRepairPreview)
  });

  const invalidateInventory = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["inventory"] }),
      queryClient.invalidateQueries({ queryKey: ["inventory-item", itemId] }),
      queryClient.invalidateQueries({ queryKey: ["character"] }),
      queryClient.invalidateQueries({ queryKey: ["me"] })
    ]);
    setShowRepairPreview(false);
    onChanged();
  };

  const equipMutation = useMutation({
    mutationFn: (item: ItemDetail) =>
      item.is_equipped ? api.unequip(item.id) : api.equip(item.id),
    onSuccess: invalidateInventory
  });

  const repairMutation = useMutation({
    mutationFn: (id: number) => api.repair(id),
    onSuccess: invalidateInventory
  });

  if (!itemId) {
    return (
      <Panel>
        <EmptyState
          body="Select an item to inspect stats, durability, and actions."
          title="No item selected"
        />
      </Panel>
    );
  }

  if (itemQuery.isLoading) {
    return (
      <Panel>
        <LoadingLine label="Loading item details" />
      </Panel>
    );
  }

  if (itemQuery.error || !itemQuery.data) {
    return (
      <Panel>
        <ErrorNotice message={(itemQuery.error as Error | null)?.message} />
      </Panel>
    );
  }

  const item = itemQuery.data;
  const needsRepair = item.durability.current < item.durability.max;

  return (
    <Panel>
      <div className="flex flex-col gap-5 sm:flex-row">
        <ItemGlyph
          broken={item.is_broken}
          rarity={item.rarity}
          size="lg"
          src={item.media?.medium_url ?? item.media?.small_url ?? item.media?.icon_url}
        />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold uppercase text-brass">
            {item.rarity} {formatStatName(item.slot)}
          </p>
          <h2 className="text-3xl font-black text-parchment">{item.name}</h2>
          <p className="mt-1 text-parchment/65">
            Level {item.item_level} / {item.item_type}
          </p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3">
        {Object.entries(item.stats).map(([key, value]) => (
          <StatBadge key={key} label={formatStatName(key)} value={`+${value}`} />
        ))}
        <StatBadge
          label="Durability"
          tone={item.is_broken ? "warn" : "good"}
          value={`${item.durability.current}/${item.durability.max}`}
        />
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <Button
          disabled={
            equipMutation.isPending ||
            (!item.is_equipped && (!item.can_equip || item.is_broken))
          }
          onClick={() => equipMutation.mutate(item)}
        >
          <Shirt size={17} />
          {item.is_equipped ? "Unequip" : "Equip"}
        </Button>
        {needsRepair ? (
          <Button
            disabled={repairPreviewQuery.isFetching}
            onClick={() => setShowRepairPreview(true)}
            variant="secondary"
          >
            <Wrench size={17} />
            Repair
          </Button>
        ) : null}
      </div>

      <ErrorNotice
        message={
          (equipMutation.error as Error | null)?.message ??
          (repairMutation.error as Error | null)?.message ??
          (repairPreviewQuery.error as Error | null)?.message
        }
      />

      {showRepairPreview ? (
        <div className="mt-5 rounded-lg border border-brass/35 bg-brass/10 p-4">
          {repairPreviewQuery.isLoading ? (
            <LoadingLine label="Calculating repair cost" />
          ) : repairPreviewQuery.data ? (
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-lg font-black text-parchment">
                  Repair preview
                </h3>
                <p className="mt-1 text-sm text-parchment/65">
                  Missing durability: {repairPreviewQuery.data.durability.missing}
                </p>
                <p className="text-sm text-parchment/65">
                  Cost: {formatCopper(repairPreviewQuery.data.repair_cost_copper)}
                </p>
              </div>
              <Button
                disabled={
                  repairMutation.isPending || !repairPreviewQuery.data.can_repair
                }
                onClick={() => repairMutation.mutate(item.id)}
              >
                <Hammer size={17} />
                {repairMutation.isPending ? "Repairing..." : "Confirm"}
              </Button>
            </div>
          ) : null}
        </div>
      ) : null}
    </Panel>
  );
}

export function InventoryScreen() {
  const [selectedItemId, setSelectedItemId] = useState<number | null>(null);
  const inventoryQuery = useQuery({
    queryKey: ["inventory"],
    queryFn: api.inventory
  });

  return (
    <div className="grid gap-5 lg:grid-cols-[0.92fr_1.08fr]">
      <div className="grid gap-5">
        <Panel>
          <h2 className="mb-4 text-2xl font-black text-parchment">Bonuses</h2>
          {inventoryQuery.isLoading ? <LoadingLine label="Loading inventory" /> : null}
          <ErrorNotice message={(inventoryQuery.error as Error | null)?.message} />
          <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
            {Object.entries(inventoryQuery.data?.equipment_summary ?? {}).map(
              ([key, value]) => (
                <StatBadge key={key} label={formatStatName(key)} value={value} />
              )
            )}
          </div>
        </Panel>

        <Panel>
          <h2 className="mb-4 text-2xl font-black text-parchment">
            Equipped slots
          </h2>
          <div className="grid gap-2">
            {slots.map((slot) => {
              const item = inventoryQuery.data?.equipped?.[slot] ?? null;

              return (
                <button
                  className="flex min-h-14 items-center justify-between gap-3 rounded-md border border-white/10 bg-white/[0.04] p-3 text-left disabled:cursor-default"
                  disabled={!item}
                  key={slot}
                  onClick={() => item && setSelectedItemId(item.id)}
                  type="button"
                >
                  <span className="font-bold capitalize text-parchment">
                    {formatStatName(slot)}
                  </span>
                  {item ? (
                    <ItemGlyph
                      broken={item.is_broken}
                      rarity={item.rarity}
                      size="sm"
                      src={item.icon_url}
                    />
                  ) : (
                    <span className="text-sm text-parchment/45">Empty</span>
                  )}
                </button>
              );
            })}
          </div>
        </Panel>

        <Panel>
          <h2 className="mb-4 text-2xl font-black text-parchment">Inventory</h2>
          {inventoryQuery.data?.items.length === 0 ? (
            <EmptyState
              body="Dungeon rewards will appear here after you claim them."
              title="Pack is empty"
            />
          ) : null}
          <div className="grid gap-2 sm:grid-cols-2">
            {inventoryQuery.data?.items.map((item) => (
              <ItemButton
                item={item}
                key={item.id}
                onSelect={() => setSelectedItemId(item.id)}
                selected={selectedItemId === item.id}
              />
            ))}
          </div>
        </Panel>
      </div>

      <ItemDetailPanel
        itemId={selectedItemId}
        onChanged={() =>
          selectedItemId
            ? setSelectedItemId((current) => current ?? selectedItemId)
            : undefined
        }
      />
    </div>
  );
}
