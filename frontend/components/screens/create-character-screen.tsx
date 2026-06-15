"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useI18n, useSession } from "@/components/providers";
import { useToast } from "@/components/toast";
import { LoadingLine } from "@/components/ui";
import { api } from "@/lib/api";
import { formatStatName } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import type { CharacterClass } from "@/lib/types";

const characterSchema = (t: ReturnType<typeof useI18n>["t"]) => z.object({
  name:      z.string().min(3, t("validation.characterName")).max(32),
  class_key: z.string().min(1, t("validation.class")),
  gender:    z.enum(["male", "female"]),
});
type CharacterValues = z.infer<ReturnType<typeof characterSchema>>;

export function CreateCharacterScreen() {
  const { logout, setUser } = useSession();
  const { locale, t } = useI18n();
  const queryClient = useQueryClient();
  const classesQuery = useQuery({ queryKey: ["character-classes"], queryFn: api.characterClasses });
  const iconsQuery = useQuery({ queryKey: ["iconAssets"], queryFn: api.iconAssets });
  const [selectedAvatarId, setSelectedAvatarId] = useState<number | null>(null);

  const form = useForm<CharacterValues>({
    resolver: zodResolver(characterSchema(t)),
    defaultValues: { name: "", class_key: "", gender: "male" },
  });

  useEffect(() => {
    const firstClass = classesQuery.data?.[0]?.key;
    if (firstClass && !form.getValues("class_key")) {
      form.setValue("class_key", firstClass, { shouldValidate: true });
    }
  }, [classesQuery.data, form]);

  const mutation = useMutation({
    mutationFn: (values: CharacterValues) => api.createCharacter(values.name, values.class_key, values.gender),
    onSuccess: async () => {
      if (selectedAvatarId != null) {
        try {
          await api.updateAvatar(selectedAvatarId);
        } catch {
          // Avatar is optional — ignore failures so character creation still completes.
        }
      }
      const me = await queryClient.fetchQuery({ queryKey: ["me"], queryFn: api.me });
      setUser(me);
      await queryClient.invalidateQueries({ queryKey: ["character"] });
    },
  });

  const selectedKey = form.watch("class_key");
  const selectedGender = form.watch("gender");

  const classImage = (cls: CharacterClass) =>
    bestMediaUrl(
      selectedGender === "female"
        ? (cls.female_media ?? cls.male_media ?? cls.media)
        : (cls.male_media ?? cls.female_media ?? cls.media),
      ["medium_url", "large_url", "small_url"],
    );

  const { showError } = useToast();

  const handleBackToAuth = () => {
    queryClient.clear();
    void logout();
  };

  return (
    <main style={{
      display: "flex", minHeight: "100vh",
      alignItems: "center", justifyContent: "center",
      padding: "48px 16px",
    }}>
      <div style={{
        display: "grid", width: "100%", maxWidth: 1100,
        gap: 24,
        gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
      }}>

        {/* Form panel */}
        <div className="card" style={{ padding: 28, alignSelf: "start" }}>
          <div style={{ marginBottom: 24 }}>
            <button
              type="button"
              className="btn"
              onClick={handleBackToAuth}
              style={{ padding: "8px 12px", fontSize: 12, marginBottom: 18 }}
            >
              <ArrowLeft size={14} />
              {t("common.back")}
            </button>
            <div className="mono" style={{
              fontSize: 11, letterSpacing: "0.20em", textTransform: "uppercase",
              color: "#3B82F6", marginBottom: 8,
            }}>{t("character.firstOath")}</div>
            <h1 style={{
              fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
              fontSize: 26, fontWeight: 700, color: "#E5E7EB", margin: 0,
            }}>
              {t("character.createHero")}
            </h1>
          </div>

          <form
            style={{ display: "grid", gap: 16 }}
            onSubmit={form.handleSubmit(
              (values) => mutation.mutate(values),
              (errors) => {
                const first = Object.values(errors)[0];
                if (first?.message) showError(String(first.message));
              }
            )}
          >
            <label style={{ display: "grid", gap: 6, fontSize: 13, color: "#94A3B8" }}>
              {t("character.heroName")}
              <input
                className="input"
                placeholder="Arthas"
                {...form.register("name")}
              />
            </label>

            <input type="hidden" {...form.register("class_key")} />

            <div style={{ display: "grid", gap: 8 }}>
              <div style={{ fontSize: 13, color: "#94A3B8" }}>{t("character.gender")}</div>
              <div style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 8,
                padding: 4,
                borderRadius: 12,
                background: "#111827",
                border: "1px solid var(--line)",
              }}>
                {(["male", "female"] as const).map((gender) => {
                  const active = selectedGender === gender;
                  return (
                    <button
                      key={gender}
                      type="button"
                      onClick={() => form.setValue("gender", gender, { shouldValidate: true })}
                      style={{
                        border: "1px solid",
                        borderColor: active ? "#3B82F6" : "transparent",
                        borderRadius: 9,
                        padding: "9px 12px",
                        cursor: "pointer",
                        color: active ? "#E5E7EB" : "#94A3B8",
                        background: active ? "rgba(59,130,246,0.18)" : "transparent",
                        fontSize: 13,
                        fontWeight: 700,
                        transition: "all 160ms ease",
                      }}
                    >
                      {t(gender === "male" ? "character.genderMale" : "character.genderFemale")}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Account avatar picker — horizontally scrollable */}
            <div style={{ display: "grid", gap: 8 }}>
              <div style={{ fontSize: 13, color: "#94A3B8" }}>{t("character.avatarLabel")}</div>
              <div className="mono" style={{ fontSize: 11, color: "#64748B" }}>{t("character.avatarHint")}</div>

              {iconsQuery.isLoading ? (
                <div style={{ display: "flex", flexWrap: "nowrap", overflowX: "auto", gap: 8, paddingBottom: 6, WebkitOverflowScrolling: "touch" }}>
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} style={{ flexShrink: 0, width: 64, height: 64, borderRadius: "50%", background: "#111827", animation: "shimmer 1.4s infinite" }} />
                  ))}
                </div>
              ) : (iconsQuery.data ?? []).length === 0 ? (
                <div className="mono" style={{ fontSize: 12, color: "#64748B" }}>{t("settings.avatarEmpty")}</div>
              ) : (
                <div style={{ display: "flex", flexWrap: "nowrap", overflowX: "auto", gap: 8, paddingBottom: 6, WebkitOverflowScrolling: "touch" }}>
                  {(iconsQuery.data ?? []).map((icon) => {
                    const iconUrl = bestMediaUrl(icon);
                    const isSelected = selectedAvatarId === icon.id;
                    return (
                      <button
                        key={icon.id}
                        type="button"
                        onClick={() => setSelectedAvatarId(isSelected ? null : icon.id)}
                        title={icon.name}
                        style={{
                          appearance: "none", padding: 0,
                          flexShrink: 0,
                          width: 64, height: 64,
                          borderRadius: "50%",
                          overflow: "hidden",
                          cursor: "pointer",
                          border: `2px solid ${isSelected ? "#3B82F6" : "var(--line)"}`,
                          background: isSelected ? "rgba(59,130,246,0.18)" : "#111827",
                          transition: "border-color 0.15s, background 0.15s, transform 0.1s",
                          transform: isSelected ? "scale(1.06)" : "scale(1)",
                          boxShadow: isSelected ? "0 0 0 2px rgba(59,130,246,0.30)" : "none",
                        }}
                      >
                        {iconUrl
                          ? <img src={iconUrl} alt={icon.name} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
                          : <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, color: "#64748B" }}>?</div>
                        }
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={mutation.isPending || classesQuery.isLoading}
              className="btn btn-primary"
              style={{ width: "100%", padding: "12px", fontSize: 14, fontWeight: 600 }}
            >
              {mutation.isPending ? t("character.forging") : t("character.startCampaign")}
            </button>
          </form>
        </div>

        {/* Class selection panel */}
        <div className="card" style={{ padding: 28 }}>
          {classesQuery.isLoading ? (
            <LoadingLine label={t("character.loadingClasses")} />
          ) : (
            <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}>
              {classesQuery.data?.map((cls) => {
                const selected = cls.key === selectedKey;
                return (
                  <button
                    key={cls.key}
                    type="button"
                    onClick={() => form.setValue("class_key", cls.key, { shouldValidate: true })}
                    style={{
                      borderRadius: 14, padding: 16, textAlign: "left",
                      cursor: "pointer", transition: "all 180ms ease",
                      border: `1px solid ${selected ? "#3B82F6" : "#2E3B5A"}`,
                      background: selected
                        ? "linear-gradient(180deg, rgba(59,130,246,0.12), var(--bg-2))"
                        : "#202B44",
                      boxShadow: selected ? "0 0 0 1px #3B82F6 inset, 0 0 20px rgba(59,130,246,0.20)" : "none",
                    }}
                  >
                    <div style={{
                      width: "100%",
                      aspectRatio: "1 / 1",
                      borderRadius: 12,
                      overflow: "hidden",
                      background: "linear-gradient(180deg, rgba(59,130,246,0.10), rgba(15,23,42,0.85))",
                      border: "1px solid var(--line)",
                      marginBottom: 14,
                      position: "relative",
                    }}>
                      {classImage(cls) ? (
                        <img
                          src={classImage(cls)}
                          alt={cls.name}
                          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                        />
                      ) : (
                        <div style={{
                          width: "100%", height: "100%",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          color: "#64748B", fontSize: 12, letterSpacing: "0.12em", textTransform: "uppercase",
                        }}>
                          {cls.name}
                        </div>
                      )}
                    </div>

                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 12 }}>
                      <h2 style={{
                        fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                        fontSize: 18, fontWeight: 700, color: "#E5E7EB", margin: 0,
                      }}>
                        {cls.name}
                      </h2>
                      {selected && <Check size={18} style={{ color: "#3B82F6", flexShrink: 0 }} />}
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                      {Object.entries(cls.start_stats).map(([key, val]) => (
                        <div key={key} style={{
                          borderRadius: 8, padding: "6px 10px",
                          background: "var(--bg-1)", border: "1px solid var(--line)",
                        }}>
                          <div className="mono" style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.12em", color: "#64748B" }}>
                            {formatStatName(key, locale)}
                          </div>
                          <div className="mono" style={{ fontSize: 14, fontWeight: 600, color: "#E5E7EB", marginTop: 2 }}>
                            {val}
                          </div>
                        </div>
                      ))}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
