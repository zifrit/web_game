"use client";

import { useQuery } from "@tanstack/react-query";
import { Medal } from "lucide-react";
import {
  EmptyState,
  ErrorNotice,
  ItemGlyph,
  LoadingLine,
  Panel
} from "@/components/ui";
import { api } from "@/lib/api";

function rankTone(rank: number) {
  if (rank === 1) {
    return "border-brass bg-brass/15 text-brass";
  }

  if (rank === 2) {
    return "border-white/25 bg-white/10 text-parchment";
  }

  if (rank === 3) {
    return "border-ember/45 bg-ember/15 text-ember";
  }

  return "border-white/10 bg-white/[0.04] text-parchment/75";
}

export function LeaderboardScreen() {
  const leaderboardQuery = useQuery({
    queryKey: ["leaderboard", "level"],
    queryFn: api.leaderboard
  });

  return (
    <Panel>
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <Medal className="text-brass" size={24} />
          <div>
            <p className="text-sm font-bold uppercase text-brass">Top by level</p>
            <h2 className="text-3xl font-black text-parchment">Leaderboard</h2>
          </div>
        </div>
        {leaderboardQuery.data?.my_rank ? (
          <div className="rounded-md border border-moss/40 bg-moss/15 px-4 py-2 text-right">
            <div className="text-xs uppercase text-parchment/55">My rank</div>
            <div className="font-black text-parchment">
              #{leaderboardQuery.data.my_rank.rank} / Level{" "}
              {leaderboardQuery.data.my_rank.level}
            </div>
          </div>
        ) : null}
      </div>

      {leaderboardQuery.isLoading ? <LoadingLine label="Loading leaderboard" /> : null}
      <ErrorNotice message={(leaderboardQuery.error as Error | null)?.message} />

      {leaderboardQuery.data?.items.length === 0 ? (
        <EmptyState
          body="Heroes will appear once the backend has leaderboard rows."
          title="No rankings yet"
        />
      ) : null}

      <div className="grid gap-2">
        {leaderboardQuery.data?.items.map((entry) => (
          <div
            className="grid min-h-20 grid-cols-[64px_1fr_auto] items-center gap-3 rounded-lg border border-white/10 bg-white/[0.045] p-3"
            key={entry.character_id}
          >
            <div
              className={`grid h-12 w-12 place-items-center rounded-md border text-lg font-black ${rankTone(
                entry.rank
              )}`}
            >
              #{entry.rank}
            </div>
            <div className="min-w-0">
              <div className="truncate text-lg font-black text-parchment">
                {entry.character_name}
              </div>
              <div className="text-sm text-parchment/60">{entry.class.name}</div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-xs uppercase text-parchment/55">Level</div>
                <div className="text-2xl font-black text-parchment">
                  {entry.level}
                </div>
              </div>
              <ItemGlyph
                rarity={entry.class.key}
                size="sm"
                src={entry.avatar?.icon_url ?? entry.avatar?.small_url}
              />
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
