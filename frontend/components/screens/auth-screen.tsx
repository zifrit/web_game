"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Lock, LogIn, Mail, ShieldCheck, UserPlus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useI18n, useSession } from "@/components/providers";
import { useToast } from "@/components/toast";
import { api } from "@/lib/api";

const authSchema = (t: ReturnType<typeof useI18n>["t"]) => z.object({
  email: z.string().email(t("validation.email")),
  password: z.string().min(6, t("validation.password")),
});

type AuthValues = z.infer<ReturnType<typeof authSchema>>;
type AuthMode = "login" | "register";


export function AuthScreen() {
  const [mode, setMode] = useState<AuthMode>("login");
  const [totpChallenge, setTotpChallenge] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const { setSession } = useSession();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const form = useForm<AuthValues>({
    resolver: zodResolver(authSchema(t)),
    defaultValues: { email: "", password: "" },
  });

  const mutation = useMutation({
    mutationFn: (values: AuthValues) =>
      mode === "login"
        ? api.login(values.email, values.password)
        : api.register(values.email, values.password),
    onSuccess: (auth) => {
      if ("two_factor_required" in auth) {
        setTotpChallenge(auth.challenge_token);
        setTotpCode("");
        return;
      }
      setSession(auth);
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  const totpMutation = useMutation({
    mutationFn: () => api.verifyLoginTotp(totpChallenge ?? "", totpCode),
    onSuccess: (auth) => {
      setSession(auth);
      setTotpChallenge(null);
      setTotpCode("");
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  const setAuthMode = (nextMode: AuthMode) => {
    setMode(nextMode);
    setTotpChallenge(null);
    setTotpCode("");
    form.clearErrors();
    mutation.reset();
    totpMutation.reset();
  };

  const { showError } = useToast();
  const isLogin = mode === "login";
  const needsTotp = Boolean(totpChallenge);

  return (
    <main className="auth-shell">
      <section className="auth-frame">
        <div className="auth-hero">
          <div className="auth-brand">
            <div className="brand-mark auth-brand-mark" />
            <div>
              <div className="brand-name">VultWake</div>
              <div className="brand-sub">v0.1 — MVP</div>
            </div>
          </div>

          <div className="auth-copy">
            <div className="card-sub">{t("auth.heroSub")}</div>
            <h1>{t("auth.heroTitle")}</h1>
            <p>
              {t("auth.heroCopy")}
            </p>
          </div>

          <div className="auth-ledger">
            <div>
              <span>{t("auth.class")}</span>
              <strong>{t("auth.vanguard")}</strong>
            </div>
            <div>
              <span>{t("auth.status")}</span>
              <strong>{t("auth.awaiting")}</strong>
            </div>
            <div>
              <span>{t("auth.realm")}</span>
              <strong>VultWake</strong>
            </div>
          </div>
        </div>

        <div className="auth-panel card">
          <div className="auth-mode" aria-label={t("auth.modeLabel")}>
            <button
              type="button"
              className={isLogin ? "active" : ""}
              onClick={() => setAuthMode("login")}
            >
              <LogIn size={16} />
              {t("auth.login")}
            </button>
            <button
              type="button"
              className={!isLogin ? "active" : ""}
              onClick={() => setAuthMode("register")}
            >
              <UserPlus size={16} />
              {t("auth.register")}
            </button>
          </div>

          <div className="auth-panel-head">
            <div className="card-sub">{needsTotp ? t("auth.totpRequired") : isLogin ? t("auth.accountAccess") : t("auth.newAccount")}</div>
            <h2>{needsTotp ? t("auth.totpTitle") : isLogin ? t("auth.enterKeep") : t("auth.openGate")}</h2>
          </div>

          {needsTotp ? (
            <form className="auth-form" onSubmit={(event) => {
              event.preventDefault();
              totpMutation.mutate();
            }}>
              <label>
                <span>{t("auth.totpCode")}</span>
                <div className="auth-input-wrap">
                  <KeyRound size={16} />
                  <input
                    autoComplete="one-time-code"
                    className="input"
                    inputMode="numeric"
                    maxLength={6}
                    placeholder="123456"
                    type="text"
                    value={totpCode}
                    onChange={(event) => setTotpCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                  />
                </div>
              </label>

              <button
                type="submit"
                disabled={totpMutation.isPending || totpCode.length !== 6}
                className="btn btn-primary auth-submit"
              >
                {totpMutation.isPending ? t("auth.working") : (
                  <>
                    <ShieldCheck size={17} />
                    {t("auth.verifyTotp")}
                  </>
                )}
              </button>

              <button
                type="button"
                className="btn"
                onClick={() => {
                  setTotpChallenge(null);
                  setTotpCode("");
                  mutation.reset();
                  totpMutation.reset();
                }}
              >
                {t("common.back")}
              </button>
            </form>
          ) : (
            <form className="auth-form" onSubmit={form.handleSubmit(
              (values) => mutation.mutate(values),
              (errors) => {
                const first = Object.values(errors)[0];
                if (first?.message) showError(String(first.message));
              }
            )}>
              <label>
                <span>{t("auth.email")}</span>
                <div className="auth-input-wrap">
                  <Mail size={16} />
                  <input
                    autoComplete="email"
                    className="input"
                    placeholder="you@example.com"
                    type="email"
                    {...form.register("email")}
                  />
                </div>
              </label>

              <label>
                <span>{t("auth.password")}</span>
                <div className="auth-input-wrap">
                  <Lock size={16} />
                  <input
                    autoComplete={isLogin ? "current-password" : "new-password"}
                    className="input"
                    placeholder={t("auth.passwordPlaceholder")}
                    type="password"
                    {...form.register("password")}
                  />
                </div>
              </label>

              <button
                type="submit"
                disabled={mutation.isPending}
                className="btn btn-primary auth-submit"
              >
                {mutation.isPending ? (
                  t("auth.working")
                ) : isLogin ? (
                  <>
                    <ShieldCheck size={17} />
                    {t("auth.enter")}
                  </>
                ) : (
                  <>
                    <UserPlus size={17} />
                    {t("auth.createAccount")}
                  </>
                )}
              </button>
            </form>
          )}
        </div>
      </section>
    </main>
  );
}
