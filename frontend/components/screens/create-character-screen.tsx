"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useI18n, useSession } from "@/components/providers";
import { ErrorNotice, LoadingLine } from "@/components/ui";
import { api } from "@/lib/api";
import { formatStatName } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import type { CharacterClass } from "@/lib/types";

const characterSchema = (t: ReturnType<typeof useI18n>["t"]) => z.object({
  name:      z.string().min(3, t("validation.characterName")).max(32),
  class_key: z.string().min(1, t("validation.class")),
});
type CharacterValues = z.infer<ReturnType<typeof characterSchema>>;

const inputStyle: React.CSSProperties = {
  width: "100%", borderRadius: 8,
  border: "1px solid #2E3B5A",
  background: "rgba(11,16,32,0.8)",
  color: "#E5E7EB", padding: "10px 14px",
  outline: "none", fontSize: 14,
  transition: "border-color 150ms ease, box-shadow 150ms ease",
};

export function CreateCharacterScreen() {
  const { setUser } = useSession();
  const { locale, t } = useI18n();
  const queryClient = useQueryClient();
  const classesQuery = useQuery({ queryKey: ["character-classes"], queryFn: api.characterClasses });

  const form = useForm<CharacterValues>({
    resolver: zodResolver(characterSchema(t)),
    defaultValues: { name: "", class_key: "" },
  });

  useEffect(() => {
    const firstClass = classesQuery.data?.[0]?.key;
    if (firstClass && !form.getValues("class_key")) {
      form.setValue("class_key", firstClass, { shouldValidate: true });
    }
  }, [classesQuery.data, form]);

  const mutation = useMutation({
    mutationFn: (values: CharacterValues) => api.createCharacter(values.name, values.class_key),
    onSuccess: async () => {
      const me = await queryClient.fetchQuery({ queryKey: ["me"], queryFn: api.me });
      setUser(me);
      await queryClient.invalidateQueries({ queryKey: ["character"] });
    },
  });

  const selectedKey = form.watch("class_key");

  const classImage = (cls: CharacterClass) =>
    bestMediaUrl(cls.media, ["large_url", "medium_url", "small_url", "icon_url", "original_url"]);

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
            onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
          >
            <label style={{ display: "grid", gap: 6, fontSize: 13, color: "#94A3B8" }}>
              {t("character.heroName")}
              <input
                className="input"
                placeholder="Arthas"
                {...form.register("name")}
              />
              {form.formState.errors.name && (
                <span style={{ fontSize: 11, color: "#EF4444" }}>{form.formState.errors.name.message}</span>
              )}
            </label>

            <label style={{ display: "grid", gap: 6, fontSize: 13, color: "#94A3B8" }}>
              {t("character.class")}
              <select className="input" {...form.register("class_key")}>
                {classesQuery.data?.map((cls) => (
                  <option key={cls.key} value={cls.key}>{cls.name}</option>
                ))}
              </select>
              {form.formState.errors.class_key && (
                <span style={{ fontSize: 11, color: "#EF4444" }}>{form.formState.errors.class_key.message}</span>
              )}
            </label>

            <ErrorNotice message={
              (mutation.error as Error | null)?.message ??
              (classesQuery.error as Error | null)?.message
            } />

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
