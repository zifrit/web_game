"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Clock, PackageCheck, Pickaxe, Trophy } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  Button,
  EmptyState,
  ErrorNotice,
  LoadingLine,
  Panel,
  StatBadge,
  formatCopper,
  formatDuration
} from "@/components/ui";
import { api } from "@/lib/api";
import type { DungeonRun } from "@/lib/types";

function useRemainingSeconds(run?: DungeonRun | null) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!run?.ends_at || run.status !== "IN_PROGRESS") {
      return;
    }

    const interval = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, [run?.ends_at, run?.status]);

  return useMemo(() => {
    if (!run || run.status !== "IN_PROGRESS") {
      return 0;
    }

    if (run.ends_at) {
      return Math.max(
        0,
        Math.ceil((new Date(run.ends_at).getTime() - now) / 1000)
      );
    }

    return Math.max(0, run.remaining_seconds ?? 0);
  }, [now, run]);
}

function CurrentRunPanel({ run }: { run: DungeonRun | null | undefined }) {
  const queryClient = useQueryClient();
  const remainingSeconds = useRemainingSeconds(run);

  const claimMutation = useMutation({
    mutationFn: (runId: number) => api.claimRun(runId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["current-run"] }),
        queryClient.invalidateQueries({ queryKey: ["character"] }),
        queryClient.invalidateQueries({ queryKey: ["inventory"] }),
        queryClient.invalidateQueries({ queryKey: ["me"] })
      ]);
    }
  });

  if (!run) {
    return (
      <Panel>
        <EmptyState
          body="Pick a location below and the server will resolve the run when it ends."
          title="No active expedition"
        />
      </Panel>
    );
  }

  const waitingForClaim =
    run.status === "SUCCESS_WAITING_CLAIM" ||
    run.status === "FAILED_WAITING_CLAIM";

  return (
    <Panel className="border-brass/35">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-bold uppercase text-brass">Current run</p>
          <h2 className="text-3xl font-black text-parchment">
            {run.location.name}
          </h2>
          <p className="mt-1 text-parchment/65">{run.status}</p>
        </div>
        {run.status === "IN_PROGRESS" ? (
          <div className="rounded-lg border border-moss/40 bg-moss/15 p-4 text-right">
            <div className="flex items-center justify-end gap-2 text-moss">
              <Clock size={18} />
              <span className="text-xs font-bold uppercase">Remaining</span>
            </div>
            <div className="mt-1 text-4xl font-black text-parchment">
              {formatDuration(remainingSeconds)}
            </div>
          </div>
        ) : null}
      </div>

      {waitingForClaim && run.result_preview ? (
        <div className="mt-5 grid gap-4">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatBadge
              label="Result"
              tone={run.result_preview.is_success ? "good" : "warn"}
              value={run.result_preview.is_success ? "Success" : "Failed"}
            />
            <StatBadge label="Experience" value={run.result_preview.experience} />
            <StatBadge
              label="Coin"
              value={formatCopper(run.result_preview.money_copper)}
            />
            <StatBadge
              label="Items"
              value={run.result_preview.items_count}
            />
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-parchment/65">
              Durability loss: {run.result_preview.durability_loss}
            </p>
            <Button
              disabled={claimMutation.isPending}
              onClick={() => claimMutation.mutate(run.id)}
            >
              <PackageCheck size={17} />
              {claimMutation.isPending ? "Claiming..." : "Claim reward"}
            </Button>
          </div>
          <ErrorNotice message={(claimMutation.error as Error | null)?.message} />
        </div>
      ) : null}

      {run.status === "IN_PROGRESS" && remainingSeconds === 0 ? (
        <div className="mt-5 flex flex-col gap-3 rounded-md border border-brass/35 bg-brass/10 p-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-parchment/72">
            The timer is done. Refresh current run to let the backend confirm the
            result.
          </p>
          <Button
            onClick={() =>
              void queryClient.invalidateQueries({ queryKey: ["current-run"] })
            }
            variant="secondary"
          >
            Check result
          </Button>
        </div>
      ) : null}
    </Panel>
  );
}

export function DungeonsScreen() {
  const queryClient = useQueryClient();
  const dungeonsQuery = useQuery({
    queryKey: ["dungeons"],
    queryFn: api.dungeons
  });
  const currentRunQuery = useQuery({
    queryKey: ["current-run"],
    queryFn: api.currentRun,
    refetchInterval: (query) =>
      query.state.data?.status === "IN_PROGRESS" ? 5000 : false
  });

  const startMutation = useMutation({
    mutationFn: (locationId: number) => api.startRun(locationId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["current-run"] });
    }
  });

  return (
    <div className="grid gap-5">
      <CurrentRunPanel run={currentRunQuery.data} />

      <Panel>
        <div className="mb-5 flex items-center gap-3">
          <Pickaxe className="text-ember" size={22} />
          <h2 className="text-2xl font-black text-parchment">Dungeons</h2>
        </div>

        {dungeonsQuery.isLoading ? <LoadingLine label="Loading dungeons" /> : null}
        <ErrorNotice
          message={
            (dungeonsQuery.error as Error | null)?.message ??
            (startMutation.error as Error | null)?.message
          }
        />

        <div className="mt-4 grid gap-4 lg:grid-cols-2">
          {dungeonsQuery.data?.map((dungeon) => (
            <article
              className="grid overflow-hidden rounded-lg border border-white/10 bg-white/[0.045] md:grid-cols-[180px_1fr]"
              key={dungeon.id}
            >
              <div className="min-h-48 bg-black/30 md:min-h-full">
                {dungeon.media?.medium_url || dungeon.media?.small_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    alt=""
                    className="h-full w-full object-cover"
                    src={dungeon.media.medium_url ?? dungeon.media.small_url}
                  />
                ) : (
                  <div className="grid h-full min-h-48 place-items-center bg-[linear-gradient(135deg,rgba(106,139,78,.35),rgba(214,168,79,.22),rgba(179,64,74,.24))]">
                    <Trophy className="text-parchment/75" size={46} />
                  </div>
                )}
              </div>
              <div className="grid gap-4 p-4">
                <div>
                  <h3 className="text-2xl font-black text-parchment">
                    {dungeon.name}
                  </h3>
                  <p className="mt-1 text-sm text-parchment/65">
                    {dungeon.description}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <StatBadge
                    label="Time"
                    value={formatDuration(dungeon.duration_seconds)}
                  />
                  <StatBadge
                    label="Required power"
                    value={dungeon.required_power}
                  />
                  <StatBadge
                    label="Success"
                    tone="good"
                    value={`${dungeon.success_chance}%`}
                  />
                  <StatBadge
                    label="Item drop"
                    tone="warn"
                    value={`${dungeon.item_drop_chance}%`}
                  />
                </div>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-sm text-parchment/65">
                    XP {dungeon.rewards_preview?.experience?.min ?? "?"}-
                    {dungeon.rewards_preview?.experience?.max ?? "?"} / Coin{" "}
                    {dungeon.rewards_preview?.money_copper?.min ?? "?"}-
                    {dungeon.rewards_preview?.money_copper?.max ?? "?"}
                  </p>
                  <Button
                    disabled={
                      startMutation.isPending ||
                      currentRunQuery.data?.status === "IN_PROGRESS"
                    }
                    onClick={() => startMutation.mutate(dungeon.id)}
                  >
                    Start
                  </Button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}
