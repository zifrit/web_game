"use client";

import { useMutation } from "@tanstack/react-query";
import { X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useI18n } from "@/components/providers";
import { api } from "@/lib/api";
import { formatDuration } from "@/lib/i18n";
import type { DungeonMiniGameAttempt, DungeonMiniGameCard, DungeonRun } from "@/lib/types";

function formatTime(secs: number) {
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h > 0) return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function useAttemptSeconds(attempt?: DungeonMiniGameAttempt | null) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!attempt?.expires_at || attempt.status !== "IN_PROGRESS") return;
    const t = window.setInterval(() => setNow(Date.now()), 500);
    return () => window.clearInterval(t);
  }, [attempt?.expires_at, attempt?.status]);
  return useMemo(() => {
    if (!attempt || attempt.status !== "IN_PROGRESS") return 0;
    return Math.max(0, Math.ceil((new Date(attempt.expires_at).getTime() - now) / 1000));
  }, [attempt, now]);
}

export function canOpenMiniGame(run: DungeonRun) {
  if (run.status !== "IN_PROGRESS") return false;
  const state = run.mini_game;
  return Boolean(state?.available || (state?.started && state.status === "IN_PROGRESS"));
}

export function DungeonMiniGameModal({
  attempt,
  onClose,
  onFinished,
}: {
  attempt: DungeonMiniGameAttempt;
  onClose: () => void;
  onFinished: (attempt: DungeonMiniGameAttempt) => void;
}) {
  const { locale, t } = useI18n();
  const [currentAttempt, setCurrentAttempt] = useState(attempt);
  const [visibleCards, setVisibleCards] = useState<DungeonMiniGameCard[]>(attempt.board ?? []);
  const [openIds, setOpenIds] = useState<string[]>([]);
  const [locked, setLocked] = useState(false);
  const [revealingId, setRevealingId] = useState<string | null>(null);
  const [finished, setFinished] = useState<DungeonMiniGameAttempt | null>(attempt.status === "IN_PROGRESS" ? null : attempt);

  const totalPairs = currentAttempt.config.pairs_count;
  const remaining = useAttemptSeconds(currentAttempt);
  const rewardLabel = formatDuration(currentAttempt.config.reward_duration_reduction_seconds, locale);

  const revealMutation = useMutation({
    mutationFn: (cardId: string) => api.revealMiniGameCard(currentAttempt.id, cardId),
  });

  const moveMutation = useMutation({
    mutationFn: (payload: { first_card_id: string; second_card_id: string }) =>
      api.moveMiniGame(currentAttempt.id, payload),
  });

  useEffect(() => {
    if (!finished && remaining === 0 && currentAttempt.status === "IN_PROGRESS") {
      setFinished({ ...currentAttempt, status: "FAILED", board: visibleCards });
    }
  }, [currentAttempt, finished, remaining, visibleCards]);

  function mergeOpenedCards(cards: DungeonMiniGameCard[]) {
    setVisibleCards((current) =>
      current.map((item) => cards.find((opened) => opened.id === item.id) ?? item)
    );
  }

  function reveal(cardId: string) {
    if (locked || finished || moveMutation.isPending || revealMutation.isPending) return;
    const card = visibleCards.find((item) => item.id === cardId);
    if (!card || card.state === "matched" || openIds.includes(cardId) || openIds.length >= 2) return;

    if (openIds.length === 0) {
      setOpenIds([cardId]);
      setRevealingId(cardId);
      setVisibleCards((current) =>
        current.map((item) => item.id === cardId ? { ...item, state: "temporary_open" } : item)
      );
      revealMutation.mutate(cardId, {
        onSuccess: (opened) => mergeOpenedCards([opened]),
        onError: () => {
          setOpenIds([]);
          setVisibleCards((current) =>
            current.map((item) => item.id === cardId ? { ...item, state: "hidden", face: null, image_url: null } : item)
          );
        },
        onSettled: () => setRevealingId(null),
      });
      return;
    }

    const nextOpen = [openIds[0], cardId];
    setOpenIds(nextOpen);
    setLocked(true);
    setVisibleCards((current) =>
      current.map((item) => item.id === cardId ? { ...item, state: "temporary_open" } : item)
    );
    moveMutation.mutate(
      { first_card_id: nextOpen[0], second_card_id: nextOpen[1] },
      {
        onSuccess: (result) => {
          setCurrentAttempt(result.attempt);
          mergeOpenedCards(result.opened_cards);
          if (result.matched) {
            setVisibleCards(result.attempt.board ?? []);
            if (result.attempt.status === "SUCCESS") {
              setFinished(result.attempt);
              onFinished(result.attempt);
            }
            setOpenIds([]);
            setLocked(false);
            return;
          }
          window.setTimeout(() => {
            setVisibleCards(result.attempt.board ?? []);
            setOpenIds([]);
            setLocked(false);
          }, 700);
        },
        onError: () => {
          setOpenIds([]);
          setLocked(false);
        },
      }
    );
  }

  const status = finished?.status ?? currentAttempt.status;

  return (
    <div className="modal-backdrop">
      <div className="modal mini-game-modal">
        <div className="mini-game-head">
          <div>
            <div className="card-sub">{t("miniGame.subtitle", { difficulty: currentAttempt.config.difficulty })}</div>
            <div className="card-title">{t("miniGame.title")}</div>
          </div>
          <button className="mini-game-close" onClick={onClose} aria-label={t("miniGame.close")}>
            <X size={18} />
          </button>
        </div>

        <div className="mini-game-stats">
          <span>{t("miniGame.timer", { time: formatTime(remaining) })}</span>
          <span>{t("miniGame.pairs", { found: currentAttempt.matched_pairs_count, total: totalPairs })}</span>
          <span>{t("miniGame.moves", { count: currentAttempt.moves_count })}</span>
          <span>{t("miniGame.reward", { time: rewardLabel })}</span>
        </div>

        <div className={`mini-game-grid pairs-${totalPairs}`}>
          {visibleCards.map((card) => {
            const revealed = openIds.includes(card.id) || card.state === "matched" || card.state === "temporary_open" || status !== "IN_PROGRESS";
            return (
              <button
                key={card.id}
                type="button"
                className={`mini-card${revealed ? " revealed" : ""}${card.state === "matched" ? " matched" : ""}`}
                disabled={status !== "IN_PROGRESS" || locked || moveMutation.isPending || revealMutation.isPending}
                onClick={() => reveal(card.id)}
              >
                {revealed && card.image_url && (
                  <img src={card.image_url} alt={card.face ?? ""} draggable={false} />
                )}
                {revealed && revealingId === card.id && !card.image_url && <span className="mini-card-loading" />}
              </button>
            );
          })}
        </div>

        {status !== "IN_PROGRESS" && (
          <div className={`mini-game-result ${status === "SUCCESS" ? "success" : "failed"}`}>
            {status === "SUCCESS" ? t("miniGame.success") : t("miniGame.failed")}
          </div>
        )}
        {moveMutation.isPending && <div className="mini-game-result">{t("miniGame.trying")}</div>}
      </div>
    </div>
  );
}
