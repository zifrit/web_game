"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound } from "lucide-react";
import { useI18n } from "@/components/providers";
import { useToast } from "@/components/toast";
import { ErrorNotice } from "@/components/ui";
import { api } from "@/lib/api";
import { bestMediaUrl } from "@/lib/media";
import type { TwoFactorSetup, User } from "@/lib/types";
import type { Locale } from "@/lib/i18n";

export function SettingsScreen() {
  const { locale, setLocale, t } = useI18n();
  const { showToast, showSuccess } = useToast();
  const queryClient = useQueryClient();

  const [pickerOpen, setPickerOpen] = useState(false);
  const [selectedIconId, setSelectedIconId] = useState<number | null>(null);
  const [twoFactorSetup, setTwoFactorSetup] = useState<TwoFactorSetup | null>(null);
  const [confirmCode, setConfirmCode] = useState("");
  const [disableOpen, setDisableOpen] = useState(false);
  const [disablePassword, setDisablePassword] = useState("");
  const [disableCode, setDisableCode] = useState("");

  const characterQuery = useQuery({ queryKey: ["character"], queryFn: api.character });
  const userQuery      = useQuery({ queryKey: ["me"],        queryFn: api.me });
  const iconsQuery     = useQuery({ queryKey: ["iconAssets"], queryFn: api.iconAssets, enabled: pickerOpen });
  const twoFactorQuery = useQuery({ queryKey: ["twoFactor"], queryFn: api.twoFactorStatus });

  const character = characterQuery.data;
  const user      = userQuery.data;
  const twoFactor = twoFactorQuery.data ?? user?.two_factor;

  const avatarMutation = useMutation({
    mutationFn: (id: number) => api.updateAvatar(id),
    onSuccess: (data) => {
      queryClient.setQueryData<User>(["me"], (prev) =>
        prev ? { ...prev, avatar: data.avatar } : prev,
      );
      setPickerOpen(false);
      setSelectedIconId(null);
    },
  });

  const currentAvatarUrl = user?.avatar ? bestMediaUrl(user.avatar) : undefined;

  const showErrorToast = (error: unknown) => {
    const message = error instanceof Error && error.message ? error.message : t("settings.totpErrorToast");
    showToast({ tone: "error", message });
  };

  const setTwoFactorEnabled = (totpProtection: boolean) => {
    queryClient.setQueryData<User>(["me"], (prev) =>
      prev ? { ...prev, two_factor: { ...(prev.two_factor ?? {}), totp_protection: totpProtection } } : prev,
    );
    void queryClient.invalidateQueries({ queryKey: ["twoFactor"] });
    void queryClient.invalidateQueries({ queryKey: ["me"] });
  };

  const setupMutation = useMutation({
    mutationFn: api.startTwoFactorSetup,
    onSuccess: (data) => {
      setTwoFactorSetup(data);
      setConfirmCode("");
      setDisableOpen(false);
    },
    onError: showErrorToast,
  });

  const confirmMutation = useMutation({
    mutationFn: () => api.confirmTwoFactorSetup(confirmCode),
    onSuccess: () => {
      setTwoFactorSetup(null);
      setConfirmCode("");
      setTwoFactorEnabled(true);
      showSuccess(t("settings.totpEnabledToast"));
    },
    onError: showErrorToast,
  });

  const disableMutation = useMutation({
    mutationFn: () => api.disableTwoFactor(disablePassword, disableCode),
    onSuccess: () => {
      setDisableOpen(false);
      setDisablePassword("");
      setDisableCode("");
      setTwoFactorEnabled(false);
      showSuccess(t("settings.totpDisabledToast"));
    },
    onError: showErrorToast,
  });

  const handleEdit = () => {
    setPickerOpen(true);
    setSelectedIconId(null);
  };

  const handleCancel = () => {
    setPickerOpen(false);
    setSelectedIconId(null);
  };

  const handleSave = () => {
    if (selectedIconId) avatarMutation.mutate(selectedIconId);
  };

  return (
    <div className="col" style={{ maxWidth: 900, marginLeft: "auto", marginRight: "auto" }}>
      {/* Account + Avatar */}
      <div className="card">
        <div className="card-h">
          <div>
            <div className="card-title">{t("settings.account")}</div>
            <div className="card-sub">{t("settings.accountSub")}</div>
          </div>
        </div>
        <div className="card-body">

          {/* Avatar section */}
          <div style={{ marginBottom: 20 }}>
            <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.18em", textTransform: "uppercase", marginBottom: 12 }}>
              {t("settings.avatar")}
            </div>

            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
              {/* Avatar preview */}
              <div style={{
                width: 192, height: 192, minWidth: 192, borderRadius: "50%",
                overflow: "hidden",
                border: `2px solid ${currentAvatarUrl ? "var(--primary)" : "var(--line)"}`,
                background: "var(--bg-2)",
                display: "flex", alignItems: "center", justifyContent: "center",
                flexShrink: 0,
                boxShadow: currentAvatarUrl ? "0 0 0 3px color-mix(in srgb, var(--primary) 20%, transparent)" : "none",
              }}>
                {currentAvatarUrl
                  ? <img src={currentAvatarUrl} alt="avatar" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
                  : <span style={{ fontSize: 56, color: "var(--text-mute)" }}>?</span>
                }
              </div>

              {/* Edit button + sub-label */}
              {!pickerOpen && (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
                  <div className="mono" style={{ fontSize: 11, color: "var(--text-dim)" }}>
                    {t("settings.avatarSub")}
                  </div>
                  <button
                    type="button"
                    className="btn"
                    style={{ fontSize: 12, padding: "6px 14px" }}
                    onClick={handleEdit}
                  >
                    {t("settings.avatarEdit")}
                  </button>
                </div>
              )}
            </div>

            {/* Picker — shown only after Edit is clicked */}
            {pickerOpen && (
              <div style={{ marginTop: 16 }}>
                <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.16em", textTransform: "uppercase", marginBottom: 10 }}>
                  {t("settings.avatarPicker")}
                </div>

                {iconsQuery.isLoading ? (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(8, 112px)", gap: 8, marginBottom: 14 }}>
                    {Array.from({ length: 8 }).map((_, i) => (
                      <div key={i} style={{ width: 112, height: 112, borderRadius: "50%", background: "var(--bg-1)", animation: "shimmer 1.4s infinite" }} />
                    ))}
                  </div>
                ) : (iconsQuery.data ?? []).length === 0 ? (
                  <div className="mono" style={{ fontSize: 12, color: "var(--text-mute)", marginBottom: 14 }}>
                    {t("settings.avatarEmpty")}
                  </div>
                ) : (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(8, 112px)", gap: 8, marginBottom: 14 }}>
                    {(iconsQuery.data ?? []).map((icon) => {
                      const iconUrl = bestMediaUrl(icon);
                      const isSelected = selectedIconId === icon.id;
                      return (
                        <button
                          key={icon.id}
                          type="button"
                          onClick={() => setSelectedIconId(icon.id)}
                          disabled={avatarMutation.isPending}
                          title={icon.name}
                          style={{
                            appearance: "none", padding: 0,
                            border: `2px solid ${isSelected ? "var(--primary)" : "var(--line)"}`,
                            borderRadius: "50%",
                            background: isSelected ? "color-mix(in srgb, var(--primary) 14%, transparent)" : "var(--bg-1)",
                            cursor: "pointer",
                            width: 112, height: 112,
                            overflow: "hidden",
                            transition: "border-color 0.15s, background 0.15s, transform 0.1s",
                            transform: isSelected ? "scale(1.06)" : "scale(1)",
                            boxShadow: isSelected ? "0 0 0 2px color-mix(in srgb, var(--primary) 30%, transparent)" : "none",
                          }}
                        >
                          {iconUrl
                            ? <img src={iconUrl} alt={icon.name} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
                            : <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, color: "var(--text-mute)" }}>?</div>
                          }
                        </button>
                      );
                    })}
                  </div>
                )}

                <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                  <button
                    type="button"
                    className="btn"
                    style={{ fontSize: 12, padding: "6px 14px" }}
                    onClick={handleCancel}
                    disabled={avatarMutation.isPending}
                  >
                    {t("settings.avatarCancel")}
                  </button>
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ fontSize: 12, padding: "6px 14px" }}
                    onClick={handleSave}
                    disabled={!selectedIconId || avatarMutation.isPending}
                  >
                    {avatarMutation.isPending ? t("settings.avatarSaving") : t("settings.avatarSave")}
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="divider" />

          {/* Active hero */}
          <div className="setting-row">
            <div>
              <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.18em", textTransform: "uppercase" }}>
                {t("settings.activeHero")}
              </div>
              {character ? (
                <>
                  <div style={{
                    fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                    fontSize: 18, fontWeight: 600, letterSpacing: "0.04em",
                    textTransform: "uppercase", marginTop: 4, color: "var(--bone)",
                  }}>
                    {character.name}
                  </div>
                  <div className="mono" style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 2 }}>
                    {character.class?.name ?? "—"} · {t("common.levelShort")} {character.level} · {t("common.rank")} {character.rank ?? "F"}
                  </div>
                </>
              ) : (
                <div style={{ fontSize: 13, color: "var(--text-dim)", marginTop: 4 }}>—</div>
              )}
            </div>
            <div style={{ textAlign: "right" }}>
              <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.18em", textTransform: "uppercase" }}>
                {t("settings.build")}
              </div>
              <div className="mono" style={{ fontSize: 13, color: "var(--bone)", marginTop: 4 }}>v0.1 — MVP</div>
            </div>
          </div>
        </div>
      </div>

      {/* Security */}
      <div className="card">
        <div className="card-h">
          <div>
            <div className="card-title">{t("settings.security")}</div>
            <div className="card-sub">{t("settings.securitySub")}</div>
          </div>
        </div>
        <div className="card-body">
          <div className="setting-row">
            <div>
              <div style={{ fontSize: 13, color: "var(--text)" }}>{t("settings.totpProtection")}</div>
              <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.12em", textTransform: "uppercase", marginTop: 2 }}>
                {twoFactor?.totp_protection ? t("settings.totpEnabled") : t("settings.totpDisabled")}
              </div>
            </div>
            <label className="switch-control" aria-label={t("settings.totpProtection")}>
              <input
                type="checkbox"
                checked={Boolean(twoFactor?.totp_protection)}
                disabled={setupMutation.isPending || disableMutation.isPending || confirmMutation.isPending || twoFactorQuery.isLoading}
                onChange={(event) => {
                  if (event.target.checked) {
                    setupMutation.mutate();
                    return;
                  }
                  setDisableOpen(true);
                  setTwoFactorSetup(null);
                }}
              />
              <span className="switch-track">
                <span className="switch-thumb" />
              </span>
            </label>
          </div>

          <ErrorNotice message={(setupMutation.error as Error | null)?.message} />

          {twoFactorSetup && (
            <div style={{ marginTop: 18, display: "grid", gap: 14 }}>
              <div className="divider" />
              <div style={{ display: "grid", gridTemplateColumns: "minmax(120px, 180px) 1fr", gap: 18, alignItems: "center" }}>
                <img
                  src={twoFactorSetup.qr_data_url}
                  alt={t("settings.totpQr")}
                  style={{ width: "100%", maxWidth: 180, borderRadius: 8, background: "#fff", padding: 8 }}
                />
                <div>
                  <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.16em", textTransform: "uppercase", marginBottom: 8 }}>
                    {t("settings.totpManualKey")}
                  </div>
                  <div className="mono" style={{ overflowWrap: "anywhere", color: "var(--bone)", fontSize: 13, lineHeight: 1.6 }}>
                    {twoFactorSetup.secret}
                  </div>
                </div>
              </div>

              <label>
                <span style={{ display: "block", fontSize: 12, color: "var(--text-dim)", marginBottom: 6 }}>{t("settings.totpConfirmCode")}</span>
                <div className="auth-input-wrap">
                  <KeyRound size={16} />
                  <input
                    autoComplete="one-time-code"
                    className="input"
                    inputMode="numeric"
                    maxLength={6}
                    placeholder="123456"
                    type="text"
                    value={confirmCode}
                    onChange={(event) => setConfirmCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                  />
                </div>
              </label>

              <ErrorNotice message={(confirmMutation.error as Error | null)?.message} />

              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className="btn"
                  onClick={() => {
                    setTwoFactorSetup(null);
                    setConfirmCode("");
                    setupMutation.reset();
                    confirmMutation.reset();
                  }}
                  disabled={confirmMutation.isPending}
                >
                  {t("common.cancel")}
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => confirmMutation.mutate()}
                  disabled={confirmCode.length !== 6 || confirmMutation.isPending}
                >
                  {confirmMutation.isPending ? t("settings.totpConfirming") : t("settings.totpConfirm")}
                </button>
              </div>
            </div>
          )}

          {disableOpen && (
            <div style={{ marginTop: 18, display: "grid", gap: 14 }}>
              <div className="divider" />
              <label>
                <span style={{ display: "block", fontSize: 12, color: "var(--text-dim)", marginBottom: 6 }}>{t("settings.totpPassword")}</span>
                <div className="auth-input-wrap">
                  <KeyRound size={16} />
                  <input
                    autoComplete="current-password"
                    className="input"
                    placeholder={t("auth.passwordPlaceholder")}
                    type="password"
                    value={disablePassword}
                    onChange={(event) => setDisablePassword(event.target.value)}
                  />
                </div>
              </label>
              <label>
                <span style={{ display: "block", fontSize: 12, color: "var(--text-dim)", marginBottom: 6 }}>{t("settings.totpCurrentCode")}</span>
                <div className="auth-input-wrap">
                  <KeyRound size={16} />
                  <input
                    autoComplete="one-time-code"
                    className="input"
                    inputMode="numeric"
                    maxLength={6}
                    placeholder="123456"
                    type="text"
                    value={disableCode}
                    onChange={(event) => setDisableCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                  />
                </div>
              </label>

              <ErrorNotice message={(disableMutation.error as Error | null)?.message} />

              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className="btn"
                  onClick={() => {
                    setDisableOpen(false);
                    setDisablePassword("");
                    setDisableCode("");
                    disableMutation.reset();
                  }}
                  disabled={disableMutation.isPending}
                >
                  {t("common.cancel")}
                </button>
                <button
                  type="button"
                  className="btn btn-danger"
                  onClick={() => disableMutation.mutate()}
                  disabled={!disablePassword || disableCode.length !== 6 || disableMutation.isPending}
                >
                  {disableMutation.isPending ? t("settings.totpDisabling") : t("settings.totpDisableConfirm")}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Language */}
      <div className="card">
        <div className="card-h">
          <div>
            <div className="card-title">{t("common.language")}</div>
            <div className="card-sub">{t("settings.choose")}</div>
          </div>
        </div>
        <div className="card-body">
          <div className="lang-cards">
            {(["en", "ru"] as Locale[]).map((item) => (
              <button
                key={item}
                type="button"
                className={`lang-card${locale === item ? " active" : ""}`}
                onClick={() => setLocale(item)}
              >
                <div className="lang-card-code">{item.toUpperCase()}</div>
                <div className="lang-card-name">{item === "en" ? "English" : "Русский"}</div>
                {locale === item && <div className="lang-card-check">✓</div>}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Appearance */}
      <div className="card">
        <div className="card-h">
          <div>
            <div className="card-title">{t("settings.appearance")}</div>
            <div className="card-sub">{t("settings.visual")}</div>
          </div>
        </div>
        <div className="card-body">
          <div className="setting-row">
            <div>
              <div style={{ fontSize: 13, color: "var(--text)" }}>{t("settings.theme")}</div>
              <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.12em", textTransform: "uppercase", marginTop: 2 }}>
                {t("settings.darkObsidian")}
              </div>
            </div>
            <div style={{
              display: "inline-flex", padding: 3,
              background: "var(--bg-1)", border: "1px solid var(--line)", borderRadius: 10,
            }}>
              <button style={{
                appearance: "none", border: 0,
                background: "linear-gradient(180deg, var(--primary), var(--primary-deep))",
                color: "#fff", padding: "6px 14px", borderRadius: 7, fontSize: 12, cursor: "pointer",
                fontWeight: 600,
              }}>{t("settings.dark")}</button>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
