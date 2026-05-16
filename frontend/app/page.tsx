"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Backpack, Coins, Crown, Hammer, LogOut, Play, Shield, Swords, TimerReset, UserRound } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { QueryProvider } from "@/components/query-provider";
import {
  ApiError,
  AuthPayload,
  Character,
  CharacterClass,
  CurrentRun,
  Dungeon,
  Inventory,
  ItemDetail,
  RepairPreview,
  apiFetch,
  formatMoney,
  readTokens,
  writeTokens,
} from "@/lib/api";

type View = "character" | "dungeons" | "inventory" | "leaderboard";

const authSchema = z.object({ email: z.string().email(), password: z.string().min(8) });
const characterSchema = z.object({ name: z.string().min(2).max(80), class_key: z.string().min(1) });

function App() {
  return (
    <QueryProvider>
      <RpgApp />
    </QueryProvider>
  );
}

function RpgApp() {
  const queryClient = useQueryClient();
  const [tokensReady, setTokensReady] = useState(false);
  const [view, setView] = useState<View>("character");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [selectedItem, setSelectedItem] = useState<number | null>(null);

  useEffect(() => setTokensReady(Boolean(readTokens())), []);

  const me = useQuery({
    queryKey: ["me", tokensReady],
    queryFn: () => apiFetch<{ id: number; email: string; money_copper: number; has_character: boolean }>("/auth/me"),
    enabled: tokensReady,
  });

  const character = useQuery({
    queryKey: ["character"],
    queryFn: () => apiFetch<Character>("/characters/me"),
    enabled: tokensReady && Boolean(me.data?.has_character),
  });

  const logout = () => {
    writeTokens(null);
    queryClient.clear();
    setTokensReady(false);
    setView("character");
  };

  if (!tokensReady || me.error instanceof ApiError && me.error.status === 401) {
    return <AuthScreen mode={authMode} setMode={setAuthMode} onAuthed={() => setTokensReady(true)} />;
  }

  if (me.isLoading) return <Shell status="Loading account..." />;

  if (me.data && !me.data.has_character) {
    return <CreateCharacterScreen onCreated={() => queryClient.invalidateQueries()} />;
  }

  return (
    <main className="min-h-screen px-4 py-5 md:px-8">
      <section className="mx-auto flex max-w-7xl flex-col gap-5">
        <header className="panel flex flex-col justify-between gap-4 rounded-lg p-4 md:flex-row md:items-center">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.24em] text-moss">Async dungeon ledger</p>
            <h1 className="mt-1 text-3xl font-black md:text-5xl">Browser Async RPG</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge icon={<Coins size={16} />} label={formatMoney(me.data?.money_copper ?? 0)} />
            <button className="btn" onClick={logout} title="Logout">
              <LogOut size={17} /> Logout
            </button>
          </div>
        </header>

        <nav className="grid grid-cols-2 gap-2 md:grid-cols-4">
          <NavButton active={view === "character"} icon={<UserRound size={18} />} label="Character" onClick={() => setView("character")} />
          <NavButton active={view === "dungeons"} icon={<Swords size={18} />} label="Dungeons" onClick={() => setView("dungeons")} />
          <NavButton active={view === "inventory"} icon={<Backpack size={18} />} label="Inventory" onClick={() => setView("inventory")} />
          <NavButton active={view === "leaderboard"} icon={<Crown size={18} />} label="Leaderboard" onClick={() => setView("leaderboard")} />
        </nav>

        {view === "character" && <CharacterPanel character={character.data} loading={character.isLoading} />}
        {view === "dungeons" && <DungeonsPanel />}
        {view === "inventory" && <InventoryPanel selectedItem={selectedItem} setSelectedItem={setSelectedItem} />}
        {view === "leaderboard" && <LeaderboardPanel />}
      </section>
    </main>
  );
}

function Shell({ status }: { status: string }) {
  return <main className="grid min-h-screen place-items-center text-lg font-black">{status}</main>;
}

function AuthScreen({ mode, setMode, onAuthed }: { mode: "login" | "register"; setMode: (mode: "login" | "register") => void; onAuthed: () => void }) {
  const form = useForm<z.infer<typeof authSchema>>({ resolver: zodResolver(authSchema), defaultValues: { email: "", password: "" } });
  const [error, setError] = useState("");
  const mutation = useMutation({
    mutationFn: (values: z.infer<typeof authSchema>) =>
      apiFetch<AuthPayload>(mode === "login" ? "/auth/login" : "/auth/register", { method: "POST", body: JSON.stringify(values) }, false),
    onSuccess: (data) => {
      writeTokens({ access_token: data.access_token, refresh_token: data.refresh_token });
      onAuthed();
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Auth failed"),
  });

  return (
    <main className="grid min-h-screen place-items-center px-4">
      <section className="panel w-full max-w-md rounded-lg p-6">
        <p className="text-xs font-black uppercase tracking-[0.24em] text-ember">MVP access</p>
        <h1 className="mt-2 text-4xl font-black">{mode === "login" ? "Return to camp" : "Create account"}</h1>
        <form className="mt-6 space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
          <input className="input" placeholder="email" {...form.register("email")} />
          <input className="input" placeholder="password" type="password" {...form.register("password")} />
          {error && <p className="rounded-md bg-red-100 p-3 text-sm font-bold text-red-800">{error}</p>}
          <button className="btn btn-primary w-full" disabled={mutation.isPending}>
            {mode === "login" ? "Login" : "Register"}
          </button>
        </form>
        <button className="mt-4 text-sm font-black text-moss" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Need a new account?" : "Already registered?"}
        </button>
      </section>
    </main>
  );
}

function CreateCharacterScreen({ onCreated }: { onCreated: () => void }) {
  const classes = useQuery({ queryKey: ["classes"], queryFn: () => apiFetch<CharacterClass[]>("/character-classes") });
  const form = useForm<z.infer<typeof characterSchema>>({ resolver: zodResolver(characterSchema), defaultValues: { name: "", class_key: "" } });
  const mutation = useMutation({
    mutationFn: (values: z.infer<typeof characterSchema>) => apiFetch("/characters", { method: "POST", body: JSON.stringify(values) }),
    onSuccess: onCreated,
  });
  const selected = classes.data?.find((item) => item.key === form.watch("class_key"));

  return (
    <main className="min-h-screen px-4 py-6">
      <section className="panel mx-auto max-w-4xl rounded-lg p-6">
        <h1 className="text-4xl font-black">Create Hero</h1>
        <form className="mt-6 grid gap-4 md:grid-cols-[1fr_1.4fr]" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
          <div className="space-y-4">
            <input className="input" placeholder="Hero name" {...form.register("name")} />
            <select className="input" {...form.register("class_key")}>
              <option value="">Choose class</option>
              {classes.data?.map((cls) => <option key={cls.key} value={cls.key}>{cls.name}</option>)}
            </select>
            <button className="btn btn-warm w-full" disabled={mutation.isPending}>Create</button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {(selected ? [selected] : classes.data ?? []).map((cls) => (
              <article key={cls.key} className="rounded-lg border border-ink/15 bg-white/50 p-4">
                <h2 className="text-xl font-black">{cls.name}</h2>
                <Stats stats={cls.start_stats} />
              </article>
            ))}
          </div>
        </form>
      </section>
    </main>
  );
}

function CharacterPanel({ character, loading }: { character?: Character; loading: boolean }) {
  if (loading || !character) return <Shell status="Loading hero..." />;
  return (
    <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
      <article className="panel rounded-lg p-5">
        <p className="text-sm font-black uppercase tracking-[0.18em] text-moss">{character.class.name}</p>
        <h2 className="mt-1 text-4xl font-black">{character.name}</h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <Metric label="Level" value={character.level} />
          <Metric label="Experience" value={`${character.experience}/${character.experience_to_next_level}`} />
          <Metric label="Power" value={character.stats.power} />
        </div>
        <Stats stats={character.stats} />
      </article>
      <article className="panel rounded-lg p-5">
        <h3 className="text-2xl font-black">Equipped</h3>
        <div className="mt-4 grid gap-2">
          {Object.entries(character.equipment).map(([slot, item]) => (
            <div key={slot} className="flex items-center justify-between rounded-md border border-ink/10 bg-white/40 p-3">
              <span className="font-black capitalize">{slot}</span>
              <span className={item?.is_broken ? "font-bold text-red-700" : "font-bold"}>{item ? `${item.rarity} #${item.id}` : "empty"}</span>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}

function DungeonsPanel() {
  const queryClient = useQueryClient();
  const dungeons = useQuery({ queryKey: ["dungeons"], queryFn: () => apiFetch<Dungeon[]>("/dungeons") });
  const current = useQuery({ queryKey: ["current-run"], queryFn: () => apiFetch<CurrentRun>("/dungeon-runs/current"), refetchInterval: 3000 });
  const start = useMutation({
    mutationFn: (location_id: number) => apiFetch("/dungeon-runs", { method: "POST", body: JSON.stringify({ location_id }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["current-run"] }),
  });
  const claim = useMutation({
    mutationFn: (id: number) => apiFetch(`/dungeon-runs/${id}/claim`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  return (
    <section className="grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
      <article className="panel rounded-lg p-5">
        <h2 className="text-2xl font-black">Current Run</h2>
        <CurrentRunCard run={current.data} onClaim={(id) => claim.mutate(id)} pending={claim.isPending} />
      </article>
      <div className="grid gap-4">
        {dungeons.data?.map((dungeon) => (
          <article key={dungeon.id} className="panel grid gap-4 rounded-lg p-5 md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <h3 className="text-2xl font-black">{dungeon.name}</h3>
              <p className="mt-1 text-sm font-semibold text-ink/70">{dungeon.description}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge icon={<TimerReset size={16} />} label={`${dungeon.duration_seconds}s`} />
                <Badge icon={<Shield size={16} />} label={`Power ${dungeon.required_power}`} />
                <Badge icon={<Swords size={16} />} label={`${dungeon.success_chance}% success`} />
                <Badge icon={<Backpack size={16} />} label={`${dungeon.item_drop_chance}% drop`} />
              </div>
            </div>
            <button className="btn btn-primary" disabled={start.isPending || Boolean(current.data && "status" in current.data)} onClick={() => start.mutate(dungeon.id)}>
              <Play size={17} /> Start
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

function CurrentRunCard({ run, onClaim, pending }: { run?: CurrentRun; onClaim: (id: number) => void; pending: boolean }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);
  if (!run || "current_run" in run) return <p className="mt-4 font-bold text-ink/70">No active expedition.</p>;
  if (run.status === "IN_PROGRESS") {
    const remaining = Math.max(0, Math.ceil((new Date(run.ends_at).getTime() - now) / 1000));
    return <p className="mt-4 text-xl font-black">{run.location.name}: {remaining}s remaining</p>;
  }
  return (
    <div className="mt-4 space-y-3">
      <p className="text-xl font-black">{run.result_preview.is_success ? "SUCCESS" : "FAILED"}</p>
      <Stats stats={{ experience: run.result_preview.experience, money: run.result_preview.money_copper, items: run.result_preview.items_count, durability_loss: run.result_preview.durability_loss }} />
      <button className="btn btn-warm w-full" disabled={pending} onClick={() => onClaim(run.id)}>Claim Reward</button>
    </div>
  );
}

function InventoryPanel({ selectedItem, setSelectedItem }: { selectedItem: number | null; setSelectedItem: (id: number | null) => void }) {
  const inventory = useQuery({ queryKey: ["inventory"], queryFn: () => apiFetch<Inventory>("/inventory") });
  return (
    <section className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
      <article className="panel rounded-lg p-5">
        <h2 className="text-2xl font-black">Inventory</h2>
        <Stats stats={inventory.data?.equipment_summary ?? {}} />
        <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-3">
          {inventory.data?.items.map((item) => (
            <button key={item.id} className="rounded-md border border-ink/15 bg-white/45 p-3 text-left" onClick={() => setSelectedItem(item.id)}>
              <span className="block font-black">#{item.id}</span>
              <span className="text-sm font-bold">{item.rarity}</span>
              {item.is_broken && <span className="mt-1 block text-xs font-black text-red-700">BROKEN</span>}
            </button>
          ))}
        </div>
      </article>
      <ItemDetails itemId={selectedItem} />
    </section>
  );
}

function ItemDetails({ itemId }: { itemId: number | null }) {
  const queryClient = useQueryClient();
  const item = useQuery({ queryKey: ["item", itemId], queryFn: () => apiFetch<ItemDetail>(`/inventory/items/${itemId}`), enabled: Boolean(itemId) });
  const repairPreview = useQuery({ queryKey: ["repair-preview", itemId], queryFn: () => apiFetch<RepairPreview>(`/inventory/items/${itemId}/repair-preview`), enabled: Boolean(itemId && item.data && item.data.durability.current < item.data.durability.max) });
  const invalidate = () => queryClient.invalidateQueries();
  const equip = useMutation({ mutationFn: () => apiFetch(`/inventory/items/${itemId}/equip`, { method: "POST" }), onSuccess: invalidate });
  const unequip = useMutation({ mutationFn: () => apiFetch(`/inventory/items/${itemId}/unequip`, { method: "POST" }), onSuccess: invalidate });
  const repair = useMutation({ mutationFn: () => apiFetch(`/inventory/items/${itemId}/repair`, { method: "POST" }), onSuccess: invalidate });

  if (!itemId) return <article className="panel rounded-lg p-5"><h2 className="text-2xl font-black">Select an item</h2></article>;
  if (!item.data) return <article className="panel rounded-lg p-5">Loading item...</article>;
  return (
    <article className="panel rounded-lg p-5">
      <h2 className="text-3xl font-black">{item.data.name}</h2>
      <div className="mt-3 flex flex-wrap gap-2">
        <Badge label={item.data.slot} />
        <Badge label={item.data.rarity} />
        <Badge label={`lvl ${item.data.item_level}`} />
        <Badge label={`${item.data.durability.current}/${item.data.durability.max} durability`} />
      </div>
      <Stats stats={item.data.stats} />
      <div className="mt-5 flex flex-wrap gap-2">
        {item.data.is_equipped ? (
          <button className="btn" onClick={() => unequip.mutate()}>Unequip</button>
        ) : (
          <button className="btn btn-primary" disabled={!item.data.can_equip} onClick={() => equip.mutate()}>Equip</button>
        )}
        {repairPreview.data && (
          <button className="btn btn-warm" disabled={!repairPreview.data.can_repair} onClick={() => repair.mutate()}>
            <Hammer size={17} /> Repair {formatMoney(repairPreview.data.repair_cost_copper)}
          </button>
        )}
      </div>
    </article>
  );
}

function LeaderboardPanel() {
  const board = useQuery({ queryKey: ["leaderboard"], queryFn: () => apiFetch<{ items: Array<{ rank: number; character_name: string; level: number; class: { name: string } }>; my_rank?: { rank: number; level: number } }>("/leaderboard?type=level") });
  return (
    <section className="panel rounded-lg p-5">
      <h2 className="text-2xl font-black">Top by Level</h2>
      <div className="mt-4 grid gap-2">
        {board.data?.items.map((item) => (
          <div key={`${item.rank}-${item.character_name}`} className="grid grid-cols-[4rem_1fr_5rem] rounded-md border border-ink/10 bg-white/45 p-3 font-bold">
            <span>#{item.rank}</span>
            <span>{item.character_name} · {item.class.name}</span>
            <span>Lvl {item.level}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function Stats({ stats }: { stats: Record<string, number> }) {
  return (
    <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-3">
      {Object.entries(stats).map(([key, value]) => (
        <Metric key={key} label={key.replaceAll("_", " ")} value={value} />
      ))}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-ink/10 bg-white/45 p-3">
      <p className="text-xs font-black uppercase tracking-[0.14em] text-ink/55">{label}</p>
      <p className="mt-1 text-xl font-black">{value}</p>
    </div>
  );
}

function Badge({ icon, label }: { icon?: React.ReactNode; label: string }) {
  return <span className="inline-flex items-center gap-1 rounded-md border border-ink/15 bg-white/55 px-2.5 py-1 text-sm font-black">{icon}{label}</span>;
}

function NavButton({ active, icon, label, onClick }: { active: boolean; icon: React.ReactNode; label: string; onClick: () => void }) {
  return (
    <button className={`btn ${active ? "btn-primary" : "bg-white/60"}`} onClick={onClick}>
      {icon} {label}
    </button>
  );
}

export default App;
