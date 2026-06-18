"use client";

import { useI18n } from "@/components/providers";
import { CopperDisplay } from "@/components/ui";
import { formatNumber } from "@/lib/i18n";
import type { AutoRunDurabilityChange, AutoRunState } from "@/lib/types";
import { useModalScrollLock } from "@/lib/use-modal-scroll-lock";
import { useEffect, useRef, type KeyboardEvent as ReactKeyboardEvent } from "react";

function itemName(item: { name?: string; fallback_name?: string }, fallbackLabel: string) {
  return item.name || item.fallback_name || fallbackLabel;
}

function ingredientName(
  ingredient: { name?: string; fallback_name?: string; code?: string },
  fallbackLabel: string,
) {
  return ingredient.name || ingredient.fallback_name || ingredient.code || fallbackLabel;
}

function durabilityName(change: AutoRunDurabilityChange) {
  return change.name || change.fallback_name || change.slot;
}

function getFocusableElements(container: HTMLElement) {
  return Array.from(
    container.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => !element.hasAttribute("disabled") && element.getAttribute("aria-hidden") !== "true");
}

export function AutoRunSummaryModal({
  autoRun,
  pending,
  onAcknowledge,
  onOpenInventory,
  onOpenConsumables,
}: {
  autoRun: AutoRunState;
  pending: boolean;
  onAcknowledge: () => void;
  onOpenInventory?: () => void;
  onOpenConsumables?: () => void;
}) {
  useModalScrollLock();

  const { locale, t } = useI18n();
  const dialogRef = useRef<HTMLDivElement | null>(null);
  const acknowledgeButtonRef = useRef<HTMLButtonElement | null>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const items = autoRun.summary.items_preview?.slice(0, 3) ?? [];
  const ingredients = autoRun.summary.ingredients_preview?.slice(0, 5) ?? [];
  const durabilityChanges = autoRun.durability_changes.length > 0
    ? autoRun.durability_changes
    : autoRun.summary.durability_changes ?? [];
  const stopReason = autoRun.stop_reason_message || autoRun.reason;
  const errorText = autoRun.error_message || autoRun.error;
  const hpLossTotal = autoRun.hp_loss_total ?? autoRun.summary.hp_loss_total ?? 0;
  const unknownItemLabel = t("autoRun.unknownItem");
  const unknownIngredientLabel = t("autoRun.unknownIngredient");
  const showItemsMore = Boolean(onOpenInventory) && (autoRun.items_total > items.length || (autoRun.summary.items_preview?.length ?? 0) > items.length);
  const showIngredientsMore = Boolean(onOpenConsumables) && (
    autoRun.ingredients_total > ingredients.length || (autoRun.summary.ingredients_preview?.length ?? 0) > ingredients.length
  );

  useEffect(() => {
    previousFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const frameId = window.requestAnimationFrame(() => {
      if (acknowledgeButtonRef.current) {
        acknowledgeButtonRef.current.focus();
        return;
      }
      dialogRef.current?.focus();
    });
    return () => {
      window.cancelAnimationFrame(frameId);
      if (previousFocusRef.current && document.contains(previousFocusRef.current)) {
        previousFocusRef.current.focus();
      }
    };
  }, []);

  const handleKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Tab") return;
    const dialog = dialogRef.current;
    if (!dialog) return;
    const focusable = getFocusableElements(dialog);
    if (focusable.length === 0) {
      event.preventDefault();
      dialog.focus();
      return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const activeElement = document.activeElement;
    if (event.shiftKey) {
      if (activeElement === first || !dialog.contains(activeElement)) {
        event.preventDefault();
        last.focus();
      }
      return;
    }
    if (activeElement === last || !dialog.contains(activeElement)) {
      event.preventDefault();
      first.focus();
    }
  };

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="auto-run-summary-title" onKeyDown={handleKeyDown}>
      <div ref={dialogRef} className="modal reward-modal auto-run-summary-modal" tabIndex={-1}>
        <div className="card-h">
          <div>
            <div id="auto-run-summary-title" className="card-title">{t("autoRun.summaryTitle")}</div>
            <div className="card-sub">{t("autoRun.summaryRequired")}</div>
          </div>
        </div>

        <div className="card-body">
          <div className="reward-summary-grid auto-run-summary-grid">
            <div className="reward-metric reward-metric-xp">
              <span>{t("autoRun.runs")}</span>
              <strong>{formatNumber(autoRun.runs_claimed, locale)}</strong>
            </div>
            <div className="reward-metric reward-metric-success">
              <span>{t("autoRun.successes")}</span>
              <strong>{formatNumber(autoRun.success_count, locale)}</strong>
            </div>
            <div className="reward-metric reward-metric-failed">
              <span>{t("autoRun.failures")}</span>
              <strong>{formatNumber(autoRun.failure_count, locale)}</strong>
            </div>
            <div className="reward-metric reward-metric-durability">
              <span>{t("common.hp")}</span>
              <strong>{formatNumber(autoRun.current_hp, locale)} / {formatNumber(autoRun.max_hp, locale)}</strong>
            </div>
            <div className="reward-metric reward-metric-failed">
              <span>{t("reward.hpLoss")}</span>
              <strong>{hpLossTotal > 0 ? `-${formatNumber(hpLossTotal, locale)}` : "0"}</strong>
            </div>
            <div className="reward-metric reward-metric-xp">
              <span>{t("reward.experience")}</span>
              <strong>+{formatNumber(autoRun.experience_total, locale)} {t("common.xp")}</strong>
            </div>
            <div className="reward-metric reward-metric-money">
              <span>{t("reward.money")}</span>
              <strong><CopperDisplay value={autoRun.money_total_copper} locale={locale} compact={false} /></strong>
            </div>
            <div className="reward-metric reward-metric-durability">
              <span>{t("reward.durabilityLoss")}</span>
              <strong>{autoRun.durability_loss_total > 0 ? `-${formatNumber(autoRun.durability_loss_total, locale)}` : "0"}</strong>
            </div>
          </div>

          {stopReason && (
            <div className="auto-run-summary-note">
              <div className="card-sub">{t("autoRun.stopReason")}</div>
              <div className="auto-run-summary-note-body">{stopReason}</div>
            </div>
          )}

          {errorText && (
            <div className="auto-run-summary-note auto-run-summary-note-error">
              <div className="card-sub">{t("autoRun.error")}</div>
              <div className="auto-run-summary-note-body">{errorText}</div>
            </div>
          )}

          {items.length > 0 && (
            <div className="reward-durability-breakdown">
              <div className="card-sub" style={{ marginBottom: 8 }}>
                {t("common.loot")} ({formatNumber(autoRun.items_total, locale)})
              </div>
              <div className="stat-list" style={{ gridTemplateColumns: "1fr" }}>
                {items.map((item, index) => {
                  const meta = [
                    item.rarity ? String(item.rarity).toUpperCase() : null,
                    item.item_level != null ? `${t("common.levelShort")} ${formatNumber(item.item_level, locale)}` : null,
                  ].filter(Boolean);

                  return (
                    <div key={`${item.item_id ?? item.id ?? itemName(item, unknownItemLabel)}-${index}`} className="sl-row auto-run-loot-row">
                      <span className="lbl auto-run-summary-label">
                        <span>{itemName(item, unknownItemLabel)}</span>
                        {meta.length > 0 && <span className="auto-run-summary-meta">{meta.join(" · ")}</span>}
                      </span>
                    </div>
                  );
                })}
              </div>
              {showItemsMore && (
                <div className="auto-run-summary-action">
                  <button type="button" className="btn btn-secondary" onClick={onOpenInventory}>
                    {t("autoRun.itemsMore")}
                  </button>
                </div>
              )}
            </div>
          )}

          {ingredients.length > 0 && (
            <div className="reward-durability-breakdown">
              <div className="card-sub" style={{ marginBottom: 8 }}>
                {t("reward.ingredients")} ({formatNumber(autoRun.ingredients_total, locale)})
              </div>
              <div className="stat-list" style={{ gridTemplateColumns: "1fr" }}>
                {ingredients.map((ingredient, index) => (
                  <div key={`${ingredient.ingredient_id ?? ingredient.id ?? ingredientName(ingredient, unknownIngredientLabel)}-${index}`} className="sl-row">
                    <span className="lbl">{ingredientName(ingredient, unknownIngredientLabel)}</span>
                    <span className="val">×{formatNumber(ingredient.quantity, locale)}</span>
                  </div>
                ))}
              </div>
              {showIngredientsMore && (
                <div className="auto-run-summary-action">
                  <button type="button" className="btn btn-secondary" onClick={onOpenConsumables}>
                    {t("autoRun.ingredientsMore")}
                  </button>
                </div>
              )}
            </div>
          )}

          {durabilityChanges.length > 0 && (
            <div className="reward-durability-breakdown">
              <div className="card-sub" style={{ marginBottom: 8 }}>{t("reward.durabilityBreakdown")}</div>
              <div className="stat-list" style={{ gridTemplateColumns: "1fr" }}>
                {durabilityChanges.map((change, index) => (
                  <div key={`${change.item_id ?? change.id ?? durabilityName(change)}-${index}`} className="sl-row">
                    <span className="lbl">{durabilityName(change)}</span>
                    <span className="val">
                      {formatNumber(change.durability.current, locale)} / {formatNumber(change.durability.max, locale)}
                      <span className="reward-durability-delta" style={{ color: "var(--error)" }}>
                        {" "}−{formatNumber(change.removed, locale)}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 18 }}>
            <button
              ref={acknowledgeButtonRef}
              type="button"
              className="btn btn-primary"
              disabled={pending}
              onClick={onAcknowledge}
            >
              {t("autoRun.acknowledge")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
