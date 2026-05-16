"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Castle, LogIn, UserPlus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useSession } from "@/components/providers";
import { Button, ErrorNotice, Field, Panel, inputClassName } from "@/components/ui";
import { api } from "@/lib/api";

const authSchema = z.object({
  email: z.string().email("Enter a valid email."),
  password: z.string().min(6, "Use at least 6 characters.")
});

type AuthValues = z.infer<typeof authSchema>;
type AuthMode = "login" | "register";

export function AuthScreen() {
  const [mode, setMode] = useState<AuthMode>("login");
  const { setSession } = useSession();
  const queryClient = useQueryClient();
  const form = useForm<AuthValues>({
    resolver: zodResolver(authSchema),
    defaultValues: {
      email: "",
      password: ""
    }
  });

  const mutation = useMutation({
    mutationFn: (values: AuthValues) =>
      mode === "login"
        ? api.login(values.email, values.password)
        : api.register(values.email, values.password),
    onSuccess: (auth) => {
      setSession(auth);
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    }
  });

  return (
    <main className="rpg-shell grid min-h-screen place-items-center px-4 py-8">
      <div className="grid w-full max-w-5xl gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="min-h-[520px] rounded-lg border border-white/12 bg-[#18140f]/90 p-6 shadow-iron sm:p-8">
          <div className="flex h-full flex-col justify-between gap-10">
            <div>
              <div className="mb-8 flex h-16 w-16 items-center justify-center rounded-lg border border-brass/40 bg-brass/15 text-brass">
                <Castle size={34} />
              </div>
              <p className="text-sm font-bold uppercase text-brass">
                Idle dungeon command
              </p>
              <h1 className="mt-4 max-w-xl text-5xl font-black leading-tight text-parchment sm:text-6xl">
                Send one hero. Bring back scars, coin, and better steel.
              </h1>
            </div>
            <div className="grid gap-3 text-sm text-parchment/72 sm:grid-cols-3">
              <div className="border-l-2 border-moss pl-3">
                Async dungeon timers
              </div>
              <div className="border-l-2 border-brass pl-3">
                Loot, equip, repair
              </div>
              <div className="border-l-2 border-blood pl-3">
                Level leaderboard
              </div>
            </div>
          </div>
        </section>

        <Panel className="self-center">
          <div className="mb-5 grid grid-cols-2 gap-2 rounded-md border border-white/10 bg-black/25 p-1">
            <Button
              onClick={() => setMode("login")}
              type="button"
              variant={mode === "login" ? "primary" : "ghost"}
            >
              <LogIn size={17} />
              Login
            </Button>
            <Button
              onClick={() => setMode("register")}
              type="button"
              variant={mode === "register" ? "primary" : "ghost"}
            >
              <UserPlus size={17} />
              Register
            </Button>
          </div>

          <form
            className="grid gap-4"
            onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
          >
            <Field
              error={form.formState.errors.email?.message}
              label="Email"
            >
              <input
                autoComplete="email"
                className={inputClassName}
                placeholder="you@example.com"
                type="email"
                {...form.register("email")}
              />
            </Field>
            <Field
              error={form.formState.errors.password?.message}
              label="Password"
            >
              <input
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                className={inputClassName}
                placeholder="Your password"
                type="password"
                {...form.register("password")}
              />
            </Field>

            <ErrorNotice message={(mutation.error as Error | null)?.message} />

            <Button disabled={mutation.isPending} type="submit">
              {mutation.isPending
                ? "Working..."
                : mode === "login"
                  ? "Enter"
                  : "Create account"}
            </Button>
          </form>
        </Panel>
      </div>
    </main>
  );
}
