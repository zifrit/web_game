"use client";

import { useQuery } from "@tanstack/react-query";
import { useI18n } from "@/components/providers";
import { api } from "@/lib/api";
import type { Locale } from "@/lib/i18n";

export function SettingsScreen() {
  const { locale, setLocale, t } = useI18n();
  const characterQuery = useQuery({
    queryKey: ["character"],
    queryFn: api.character,
  });

  const character = characterQuery.data;

  return (
    <div className="col" style={{ maxWidth: 900 }}>

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

      {/* Appearance + Sound */}
      <div className="grid-2">
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

        <div className="card">
          <div className="card-h">
            <div>
              <div className="card-title">{t("settings.sound")}</div>
              <div className="card-sub">{t("settings.audio")}</div>
            </div>
          </div>
          <div className="card-body">
            <div className="setting-row" style={{ alignItems: "flex-start" }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, color: "var(--text)" }}>{t("settings.masterVolume")}</div>
                <div className="mono" style={{ fontSize: 10, color: "var(--text-mute)", letterSpacing: "0.12em", textTransform: "uppercase", marginTop: 2 }}>
                  72%
                </div>
                <div className="bar" style={{ height: 6, marginTop: 8 }}>
                  <i style={{ width: "72%", background: "linear-gradient(90deg, var(--primary-deep), var(--primary-bright))" }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Account */}
      <div className="card">
        <div className="card-h">
          <div>
            <div className="card-title">{t("settings.account")}</div>
            <div className="card-sub">{t("settings.accountSub")}</div>
          </div>
        </div>
        <div className="card-body">
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
                    {character.class?.name ?? "—"} · {t("common.levelShort")} {character.level}
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

    </div>
  );
}
