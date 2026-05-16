"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, BadgeInfo, ShieldCheck } from "lucide-react";
import {
  EmptyState,
  ErrorNotice,
  ItemGlyph,
  LoadingLine,
  Panel,
  StatBadge,
  formatStatName
} from "@/components/ui";
import { api } from "@/lib/api";
import type { EquipmentSlot } from "@/lib/types";

const equipmentSlots: EquipmentSlot[] = [
  "weapon",
  "helmet",
  "armor",
  "boots",
  "ring"
];

export function CharacterScreen() {
  const characterQuery = useQuery({
    queryKey: ["character"],
    queryFn: api.character
  });

  if (characterQuery.isLoading) {
    return (
      <Panel>
        <LoadingLine label="Loading character" />
      </Panel>
    );
  }

  if (characterQuery.error || !characterQuery.data) {
    return (
      <Panel>
        <ErrorNotice message={(characterQuery.error as Error | null)?.message} />
      </Panel>
    );
  }

  const character = characterQuery.data;
  const progress =
    character.experience_to_next_level && character.experience_to_next_level > 0
      ? Math.min(
          100,
          Math.round(
            (character.experience / character.experience_to_next_level) * 100
          )
        )
      : 0;

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
      <Panel>
        <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-bold uppercase text-brass">
              Level {character.level}
            </p>
            <h2 className="text-4xl font-black text-parchment">
              {character.name}
            </h2>
            <p className="mt-1 text-parchment/65">
              {character.class?.name ?? character.class_key ?? "Unknown class"}
            </p>
          </div>
          <div className="rounded-lg border border-brass/40 bg-brass/10 p-4 text-right">
            <div className="flex items-center justify-end gap-2 text-brass">
              <Activity size={18} />
              <span className="text-xs font-bold uppercase">Power</span>
            </div>
            <div className="mt-1 text-4xl font-black text-parchment">
              {character.stats?.power ?? 0}
            </div>
          </div>
        </div>

        <div className="mt-6">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-bold text-parchment">Experience</span>
            <span className="text-parchment/65">
              {character.experience} / {character.experience_to_next_level ?? "-"}
            </span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-black/35">
            <div
              className="h-full rounded-full bg-gradient-to-r from-moss via-brass to-ember"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-3">
          {Object.entries(character.stats ?? {}).map(([key, value]) => (
            <StatBadge
              key={key}
              label={formatStatName(key)}
              tone={key === "power" ? "good" : "plain"}
              value={value}
            />
          ))}
        </div>
      </Panel>

      <Panel>
        <div className="mb-4 flex items-center gap-3">
          <ShieldCheck className="text-moss" size={22} />
          <h2 className="text-2xl font-black text-parchment">Equipment</h2>
        </div>
        <div className="grid gap-3">
          {equipmentSlots.map((slot) => {
            const item = character.equipment?.[slot] ?? null;

            return (
              <div
                className="flex min-h-16 items-center justify-between gap-3 rounded-md border border-white/10 bg-white/[0.04] p-3"
                key={slot}
              >
                <div>
                  <div className="text-xs uppercase text-parchment/55">
                    {formatStatName(slot)}
                  </div>
                  <div className="mt-1 font-bold text-parchment">
                    {item ? `${item.rarity} item #${item.id}` : "Empty slot"}
                  </div>
                </div>
                {item ? (
                  <ItemGlyph
                    broken={item.is_broken}
                    rarity={item.rarity}
                    size="sm"
                    src={item.icon_url}
                  />
                ) : (
                  <BadgeInfo className="text-parchment/35" size={22} />
                )}
              </div>
            );
          })}
        </div>
        {!character.equipment ? (
          <div className="mt-4">
            <EmptyState
              body="The backend did not return equipment yet."
              title="No equipment payload"
            />
          </div>
        ) : null}
      </Panel>
    </div>
  );
}
