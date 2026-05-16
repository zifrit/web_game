"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Backpack,
  Crown,
  DoorOpen,
  LogOut,
  Shield,
  Swords
} from "lucide-react";
import { useEffect, useState } from "react";
import { AuthScreen } from "@/components/screens/auth-screen";
import { CharacterScreen } from "@/components/screens/character-screen";
import { CreateCharacterScreen } from "@/components/screens/create-character-screen";
import { DungeonsScreen } from "@/components/screens/dungeons-screen";
import { InventoryScreen } from "@/components/screens/inventory-screen";
import { LeaderboardScreen } from "@/components/screens/leaderboard-screen";
import { Button, ErrorNotice, LoadingLine, formatCopper } from "@/components/ui";
import { api } from "@/lib/api";
import { useSession } from "@/components/providers";

type Tab = "character" | "dungeons" | "inventory" | "leaderboard";

const tabs: Array<{
  key: Tab;
  label: string;
  icon: React.ComponentType<{ size?: number }>;
}> = [
  { key: "character", label: "Character", icon: Shield },
  { key: "dungeons", label: "Dungeons", icon: DoorOpen },
  { key: "inventory", label: "Inventory", icon: Backpack },
  { key: "leaderboard", label: "Leaderboard", icon: Crown }
];

export function RpgClient() {
  const { accessToken, user, isBooting, logout, setUser } = useSession();
  const [tab, setTab] = useState<Tab>("character");
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: api.me,
    enabled: Boolean(accessToken),
    staleTime: 10_000
  });

  const activeUser = meQuery.data ?? user;

  useEffect(() => {
    if (meQuery.data) {
      setUser(meQuery.data);
    }
  }, [meQuery.data, setUser]);

  if (isBooting) {
    return (
      <main className="rpg-shell grid min-h-screen place-items-center p-6">
        <LoadingLine label="Opening the account ledger" />
      </main>
    );
  }

  if (!accessToken) {
    return <AuthScreen />;
  }

  if (meQuery.isLoading && !activeUser) {
    return (
      <main className="rpg-shell grid min-h-screen place-items-center p-6">
        <LoadingLine label="Reading hero records" />
      </main>
    );
  }

  if (meQuery.error) {
    return (
      <main className="rpg-shell grid min-h-screen place-items-center p-6">
        <div className="max-w-md space-y-4">
          <ErrorNotice message={(meQuery.error as Error).message} />
          <Button onClick={() => void logout()} variant="secondary">
            Return to login
          </Button>
        </div>
      </main>
    );
  }

  if (!activeUser?.has_character) {
    return <CreateCharacterScreen />;
  }

  return (
    <main className="rpg-shell min-h-screen px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5">
        <header className="flex flex-col gap-4 rounded-lg border border-white/12 bg-black/30 p-4 shadow-iron backdrop-blur md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-3 text-brass">
              <Swords size={22} />
              <span className="text-sm font-bold uppercase tracking-normal">
                Browser Async RPG
              </span>
            </div>
            <h1 className="mt-2 text-3xl font-black text-parchment">
              Expedition Desk
            </h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-md border border-white/12 bg-white/[0.06] px-4 py-2">
              <div className="text-xs text-parchment/55">{activeUser.email}</div>
              <div className="font-bold text-parchment">
                {formatCopper(activeUser.money_copper)}
              </div>
            </div>
            <Button
              onClick={() => {
                queryClient.clear();
                void logout();
              }}
              variant="secondary"
            >
              <LogOut size={17} />
              Logout
            </Button>
          </div>
        </header>

        <nav className="grid grid-cols-2 gap-2 rounded-lg border border-white/10 bg-black/20 p-2 md:grid-cols-4">
          {tabs.map((item) => {
            const Icon = item.icon;
            const selected = tab === item.key;

            return (
              <button
                className={`flex min-h-12 items-center justify-center gap-2 rounded-md border px-3 text-sm font-bold transition ${
                  selected
                    ? "border-brass bg-brass text-ink"
                    : "border-white/10 bg-white/[0.04] text-parchment hover:bg-white/10"
                }`}
                key={item.key}
                onClick={() => setTab(item.key)}
                type="button"
              >
                <Icon size={17} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {tab === "character" ? <CharacterScreen /> : null}
        {tab === "dungeons" ? <DungeonsScreen /> : null}
        {tab === "inventory" ? <InventoryScreen /> : null}
        {tab === "leaderboard" ? <LeaderboardScreen /> : null}
      </div>
    </main>
  );
}
