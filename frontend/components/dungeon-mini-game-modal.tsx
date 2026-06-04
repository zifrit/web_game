"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useI18n } from "@/components/providers";
import { api } from "@/lib/api";
import { formatDuration } from "@/lib/i18n";
import { useCardFaces } from "@/lib/use-card-faces";
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

/** Карточка лица: рендерит inline-SVG из каталога, с фоллбэком на статику. */
function CardFace({ code, svg }: { code: string; svg?: string }) {
  if (svg) {
    return <span className="mini-card-face" aria-hidden dangerouslySetInnerHTML={{ __html: svg }} />;
  }
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={`/memory-faces/${code}.svg`} alt="" draggable={false} />;
}

export function DungeonMiniGameDifficultyModal({
  onSelect,
  onClose,
  pending,
}: {
  onSelect: (configId: number) => void;
  onClose: () => void;
  pending?: boolean;
}) {
  const { t } = useI18n();
  const configsQuery = useQuery({
    queryKey: ["mini-game-configs"],
    queryFn: () => api.miniGameConfigs(),
    staleTime: 60 * 60 * 1000,
  });

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal mini-game-modal">
        <div className="mini-game-head">
          <div>
            <div className="card-sub">{t("miniGame.chooseSubtitle")}</div>
            <div className="card-title">{t("miniGame.chooseTitle")}</div>
          </div>
          <button className="mini-game-close" onClick={onClose} aria-label={t("miniGame.close")}>
            <X size={18} />
          </button>
        </div>

        <div className="mini-game-difficulty-list">
          {(configsQuery.data ?? []).map((config) => (
            <button
              key={config.id}
              type="button"
              className="mini-game-difficulty-card"
              disabled={pending}
              onClick={() => onSelect(config.id)}
            >
              <div className="mini-game-difficulty-name">{config.difficulty}</div>
              <div className="mini-game-difficulty-meta">
                <span>{t("miniGame.cardCount", { count: config.pairs_count * 2 })}</span>
                <span>{t("miniGame.timeLimit", { time: formatTime(config.time_limit_seconds) })}</span>
              </div>
              <div className="mini-game-difficulty-boost">
                {t("miniGame.boost", { percent: config.reward_duration_reduction_percent })}
              </div>
            </button>
          ))}
        </div>
        <div className="mini-game-result-copy">{t("miniGame.chooseHint")}</div>
      </div>
    </div>
  );
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
  const { t } = useI18n();
  const { facesByCode } = useCardFaces();
  const [currentAttempt, setCurrentAttempt] = useState(attempt);
  const [visibleCards, setVisibleCards] = useState<DungeonMiniGameCard[]>(attempt.board ?? []);
  const [openIds, setOpenIds] = useState<string[]>([]);
  const [locked, setLocked] = useState(false);
  const [revealingId, setRevealingId] = useState<string | null>(null);
  const finishedRef = useRef(false);

  const totalPairs = currentAttempt.config.pairs_count;
  const remaining = useAttemptSeconds(currentAttempt);
  const rewardLabel = t("miniGame.rewardPercent", { percent: currentAttempt.config.reward_duration_reduction_percent });

  const revealMutation = useMutation({
    mutationFn: (cardId: string) => api.revealMiniGameCard(currentAttempt.id, cardId),
  });

  const moveMutation = useMutation({
    mutationFn: (payload: { first_card_id: string; second_card_id: string }) =>
      api.moveMiniGame(currentAttempt.id, payload),
  });

  const finishAttempt = useCallback((nextAttempt: DungeonMiniGameAttempt) => {
    if (finishedRef.current) return;
    finishedRef.current = true;
    setCurrentAttempt(nextAttempt);
    onFinished(nextAttempt);
  }, [onFinished]);

  const isAttemptExpired = useCallback(() => {
    return new Date(currentAttempt.expires_at).getTime() <= Date.now();
  }, [currentAttempt.expires_at]);

  const failAttempt = useCallback(() => {
    finishAttempt({
      ...currentAttempt,
      status: "FAILED",
      completed_at: currentAttempt.completed_at ?? new Date().toISOString(),
      board: visibleCards,
    });
  }, [currentAttempt, finishAttempt, visibleCards]);

  useEffect(() => {
    if (currentAttempt.status !== "IN_PROGRESS") {
      finishAttempt(currentAttempt);
      return;
    }
    if (remaining === 0 && currentAttempt.status === "IN_PROGRESS") {
      failAttempt();
    }
  }, [currentAttempt, failAttempt, finishAttempt, remaining]);

  function mergeOpenedCards(cards: DungeonMiniGameCard[]) {
    setVisibleCards((current) =>
      current.map((item) => cards.find((opened) => opened.id === item.id) ?? item)
    );
  }

  function hideOpenCards(cardIds: string[]) {
    setVisibleCards((current) =>
      current.map((item) =>
        cardIds.includes(item.id) && item.state !== "matched"
          ? { ...item, state: "hidden", code: null }
          : item
      )
    );
  }

  function reveal(cardId: string) {
    if (locked || finishedRef.current || moveMutation.isPending || revealMutation.isPending) return;
    const card = visibleCards.find((item) => item.id === cardId);
    if (!card || card.state === "matched" || openIds.includes(cardId) || openIds.length >= 2) return;

    if (openIds.length === 0) {
      setOpenIds([cardId]);
      setRevealingId(cardId);
      setVisibleCards((current) =>
        current.map((item) => item.id === cardId ? { ...item, state: "temporary_open" } : item)
      );
      revealMutation.mutate(cardId, {
        onSuccess: (result) => {
          if (result.finished) {
            finishAttempt(result.attempt);
            return;
          }
          mergeOpenedCards([result.card]);
        },
        onError: () => {
          if (isAttemptExpired()) {
            failAttempt();
            return;
          }
          setOpenIds([]);
          hideOpenCards([cardId]);
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
          mergeOpenedCards(result.opened_cards);
          if (result.finished) {
            finishAttempt(result.attempt);
            return;
          }
          setCurrentAttempt((prev) => ({
            ...prev,
            moves_count: result.attempt.moves_count,
            matched_pairs_count: result.attempt.matched_pairs_count,
          }));
          if (result.matched) {
            setOpenIds([]);
            setLocked(false);
            return;
          }
          window.setTimeout(() => {
            hideOpenCards(nextOpen);
            setOpenIds([]);
            setLocked(false);
          }, 700);
        },
        onError: () => {
          if (isAttemptExpired()) {
            failAttempt();
            return;
          }
          hideOpenCards(nextOpen);
          setOpenIds([]);
          setLocked(false);
        },
      }
    );
  }

  const status = currentAttempt.status;

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
          <span>{rewardLabel}</span>
        </div>

        <div className={`mini-game-grid pairs-${totalPairs}`}>
          {visibleCards.map((card) => {
            const revealed = openIds.includes(card.id) || card.state === "matched" || card.state === "open" || card.state === "temporary_open" || status !== "IN_PROGRESS";
            return (
              <button
                key={card.id}
                type="button"
                className={`mini-card${revealed ? " revealed" : ""}${card.state === "matched" ? " matched" : ""}`}
                disabled={status !== "IN_PROGRESS" || locked || moveMutation.isPending || revealMutation.isPending}
                onClick={() => reveal(card.id)}
                aria-label={card.code ?? undefined}
              >
                {revealed && card.code && <CardFace code={card.code} svg={facesByCode.get(card.code)} />}
                {revealed && revealingId === card.id && !card.code && <span className="mini-card-loading" />}
              </button>
            );
          })}
        </div>

        {moveMutation.isPending && <div className="mini-game-result">{t("miniGame.trying")}</div>}
      </div>
    </div>
  );
}

export function DungeonMiniGameResultModal({
  attempt,
  onClose,
}: {
  attempt: DungeonMiniGameAttempt;
  onClose: () => void;
}) {
  const { locale, t } = useI18n();
  const success = attempt.status === "SUCCESS";
  const reductionLabel = formatDuration(attempt.duration_reduction_seconds, locale);

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="mini-game-result-title">
      <div className={`modal mini-game-result-modal ${success ? "success" : "failed"}`}>
        <div className="mini-game-result-head">
          <div>
            <div className="card-sub">{t("miniGame.title")}</div>
            <div id="mini-game-result-title" className="card-title">
              {success ? t("miniGame.resultSuccessTitle") : t("miniGame.resultFailedTitle")}
            </div>
          </div>
          <button className="mini-game-close" onClick={onClose} aria-label={t("miniGame.close")}>
            <X size={18} />
          </button>
        </div>

        <div className="mini-game-result-body">
          {success ? (
            <>
              <div className="mini-game-result-value">-{reductionLabel}</div>
              <div className="mini-game-result-copy">{t("miniGame.resultSuccessBody")}</div>
            </>
          ) : (
            <>
              <div className="mini-game-result-value">{t("miniGame.failed")}</div>
              <div className="mini-game-result-copy">{t("miniGame.resultFailedBody")}</div>
            </>
          )}
          <button className="btn btn-primary" onClick={onClose}>{t("reward.okay")}</button>
        </div>
      </div>
    </div>
  );
}
