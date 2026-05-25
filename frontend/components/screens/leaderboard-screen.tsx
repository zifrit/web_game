"use client";

import { useQuery } from "@tanstack/react-query";
import { useI18n } from "@/components/providers";
import { ErrorNotice, LoadingLine } from "@/components/ui";
import { api } from "@/lib/api";
import { bestMediaUrl } from "@/lib/media";

function rankStyle(rank: number): { borderColor: string; background: string; color: string } {
  if (rank === 1) return { borderColor: "rgba(245,158,11,0.5)", background: "rgba(245,158,11,0.12)", color: "#F59E0B" };
  if (rank === 2) return { borderColor: "rgba(148,163,184,0.35)", background: "rgba(148,163,184,0.08)", color: "#94A3B8" };
  if (rank === 3) return { borderColor: "rgba(205,124,69,0.45)", background: "rgba(205,124,69,0.12)", color: "#CD7C45" };
  return { borderColor: "var(--line)", background: "var(--bg-3)", color: "var(--text-mute)" };
}

export function LeaderboardScreen() {
  const { t } = useI18n();
  const boardQuery = useQuery({
    queryKey: ["leaderboard", "level"],
    queryFn: api.leaderboard,
  });

  return (
    <div className="col animate-fade-in">
      <div className="card">
        <div className="card-h">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 22 }}>🏅</span>
            <div>
              <div className="card-sub">{t("leaderboard.top")}</div>
              <div className="card-title">{t("nav.leaderboard")}</div>
            </div>
          </div>

          {boardQuery.data?.my_rank && (
            <div style={{
              borderRadius: 12, border: "1px solid rgba(59,130,246,0.3)",
              background: "rgba(59,130,246,0.10)", padding: "8px 16px", textAlign: "right",
            }}>
              <div className="mono" style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.12em", color: "var(--text-mute)" }}>
                {t("leaderboard.myRank")}
              </div>
              <div style={{ fontWeight: 700, color: "var(--text)", marginTop: 2 }}>
                #{boardQuery.data.my_rank.rank} · {t("common.level")} {boardQuery.data.my_rank.level}
              </div>
            </div>
          )}
        </div>

        <div className="card-body">
          {boardQuery.isLoading && <LoadingLine label={t("leaderboard.loading")} />}
          <ErrorNotice message={(boardQuery.error as Error | null)?.message} />

          {boardQuery.data?.items.length === 0 && !boardQuery.isLoading && (
            <div style={{
              textAlign: "center", padding: "40px 20px",
              border: "1px dashed var(--line)", borderRadius: 10,
            }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-dim)" }}>{t("leaderboard.empty")}</div>
              <div style={{ fontSize: 12, color: "var(--text-mute)", marginTop: 6 }}>
                {t("leaderboard.emptyBody")}
              </div>
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {boardQuery.data?.items.map((entry) => {
              const rs = rankStyle(entry.rank);
              const avatarUrl = bestMediaUrl(entry.avatar, ["small_url", "medium_url", "large_url"]);
              return (
                <div
                  key={entry.character_id}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "56px 48px 1fr auto",
                    alignItems: "center",
                    gap: 12,
                    minHeight: 72,
                    borderRadius: 12,
                    border: "1px solid var(--line)",
                    background: "var(--bg-3)",
                    padding: 12,
                    transition: "border-color 150ms ease",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--line-hover)")}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--line)")}
                  >
                  {/* Rank badge */}
                  <div style={{
                    width: 44, height: 44, display: "grid", placeItems: "center",
                    borderRadius: 10, border: `1px solid ${rs.borderColor}`,
                    background: rs.background, color: rs.color,
                    fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                    fontSize: 14, fontWeight: 700,
                  }}>
                    #{entry.rank}
                  </div>

                  <div style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    overflow: "hidden",
                    border: "1px solid var(--line)",
                    background: "var(--bg-3)",
                    display: "grid",
                    placeItems: "center",
                  }}>
                    {avatarUrl ? (
                      <img
                        src={avatarUrl}
                        alt={entry.character_name}
                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                      />
                    ) : (
                      <span style={{ color: "var(--text-mute)", fontWeight: 700 }}>
                        {entry.character_name.slice(0, 1).toUpperCase()}
                      </span>
                    )}
                  </div>

                  {/* Name + class */}
                  <div style={{ minWidth: 0 }}>
                    <div style={{
                      fontWeight: 600, color: "var(--text)",
                      overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                    }}>
                      {entry.character_name}
                    </div>
                    <div style={{ fontSize: 12, color: "var(--text-mute)", marginTop: 2 }}>
                      {entry.class.name}
                    </div>
                  </div>

                  {/* Level */}
                  <div style={{ textAlign: "right" }}>
                    <div className="mono" style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.12em", color: "var(--text-mute)" }}>
                      {t("common.level")}
                    </div>
                    <div style={{
                      fontFamily: "var(--font-cinzel, 'Cinzel', serif)",
                      fontSize: 22, fontWeight: 700, color: "var(--bone)", lineHeight: 1,
                    }}>
                      {entry.level}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
