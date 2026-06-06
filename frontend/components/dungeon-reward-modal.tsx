"use client";

import { useI18n } from "@/components/providers";
import { ErrorNotice } from "@/components/ui";
import { formatCopper, formatNumber, formatStatName, type TranslationKey } from "@/lib/i18n";
import { rarityColor } from "@/lib/rarity";
import type { ClaimResponse } from "@/lib/types";

function rarityLabel(rarity: string, t: (key: TranslationKey) => string) {
  return t(`rarity.${rarity.toLowerCase()}` as TranslationKey);
}

export function DungeonRewardModal({
  result,
  error,
  onClose,
}: {
  result: ClaimResponse;
  error?: string;
  onClose: () => void;
}) {
  const { locale, t } = useI18n();
  const item = result.rewards.items[0];
  const statusColor = result.is_success ? "var(--success)" : "var(--error)";
  const rarity = item?.rarity.toLowerCase() ?? "f";
  const stats = item ? Object.entries(item.stats ?? {}).filter(([, value]) => typeof value === "number" && value !== 0) : [];

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="dungeon-reward-title">
      <div className="modal reward-modal">
        <div className="card-h">
          <div>
            <div id="dungeon-reward-title" className="card-title">{t("reward.title")}</div>
            <div className="card-sub" style={{ color: statusColor }}>
              {result.is_success ? t("reward.success") : t("reward.failed")}
            </div>
          </div>
        </div>

        <div className="card-body">
          <div className="reward-summary-grid">
            <div className="reward-metric reward-metric-xp">
              <span>{t("reward.experience")}</span>
              <strong>+{formatNumber(result.rewards.experience, locale)} XP</strong>
            </div>
            <div className="reward-metric reward-metric-money">
              <span>{t("reward.money")}</span>
              <strong>{formatCopper(result.rewards.money_copper, locale)}</strong>
            </div>
            <div className={`reward-metric ${result.is_success ? "reward-metric-success" : "reward-metric-failed"}`}>
              <span>{t("reward.successChance")}</span>
              <strong>{formatNumber(Math.round(result.success_chance ?? 0), locale)}%</strong>
            </div>
            <div className="reward-metric reward-metric-durability">
              <span>{t("reward.durabilityLoss")}</span>
              <strong>{result.rewards.durability_loss > 0 ? `-${result.rewards.durability_loss}` : "0"}</strong>
            </div>
            <div className="reward-metric reward-metric-hp">
              <span>{t("reward.hpLoss")}</span>
              <strong style={{ color: result.rewards.hp_loss > 0 ? "var(--error)" : undefined }}>
                {result.rewards.hp_loss > 0 ? `-${result.rewards.hp_loss}` : "0"}
                {result.hp ? ` (${result.hp.current}/${result.hp.max})` : ""}
              </strong>
            </div>
          </div>

          {result.rewards.durability_changes.length > 0 && (
            <div className="reward-durability-breakdown">
              <div className="card-sub" style={{ marginBottom: 8 }}>{t("reward.durabilityBreakdown")}</div>
              <div className="stat-list" style={{ gridTemplateColumns: "1fr" }}>
                {result.rewards.durability_changes.map((change) => (
                  <div key={change.slot} className="sl-row">
                    <span className="lbl">{change.name}</span>
                    <span className="val">
                      {change.durability.current} / {change.durability.max}
                      <span className="reward-durability-delta" style={{ color: "var(--error)" }}> −{change.removed}</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.level_up && result.level_up.new_level > result.level_up.old_level && (
            <div className="reward-levelup">
              {t("reward.levelUp", { old: result.level_up.old_level, next: result.level_up.new_level })}
            </div>
          )}

          <div className="reward-item-panel">
            <div className="card-sub" style={{ marginBottom: 10 }}>
              {item ? t("reward.itemFound") : t("reward.noItem")}
            </div>
            {item ? (
              <>
                <div className="reward-item-head">
                  <div>
                    <div className="reward-item-name">{item.name}</div>
                    <div className="mono reward-item-meta">
                      {t("common.rank")} <span style={{ color: rarityColor(rarity) }}>{rarityLabel(item.rarity, t)}</span>
                      {" · "}
                      {t("common.itemLevel")} {item.item_level}
                    </div>
                  </div>
                  <div className="reward-rank-badge" style={{ borderColor: rarityColor(rarity) }}>
                    {rarityLabel(item.rarity, t)}
                  </div>
                </div>
                <div className="stat-list" style={{ gridTemplateColumns: "1fr", marginTop: 14 }}>
                  <div className="sl-row">
                    <span className="lbl">{t("common.durability")}</span>
                    <span className="val">{item.durability.current} / {item.durability.max}</span>
                  </div>
                  {stats.map(([key, value]) => (
                    <div key={key} className="sl-row">
                      <span className="lbl">{formatStatName(key, locale)}</span>
                      <span className="val">+{formatNumber(Number(value), locale)}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="reward-empty">{t("reward.noItemBody")}</div>
            )}
          </div>

          <ErrorNotice message={error} />
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 18 }}>
            <button className="btn btn-primary" onClick={onClose}>{t("reward.okay")}</button>
          </div>
        </div>
      </div>
    </div>
  );
}
