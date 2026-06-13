"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Gem, X } from "lucide-react";
import { useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useI18n } from "@/components/providers";
import { CopperDisplay, LoadingLine } from "@/components/ui";
import { type TranslationKey } from "@/lib/i18n";
import { rarityColor } from "@/lib/rarity";
import { useModalScrollLock, useSwipeToClose } from "@/lib/use-modal-scroll-lock";
import type { BuyShopOfferResponse, PaymentCurrency, ShopOfferDetail, ShopPurchaseResult, User } from "@/lib/types";

/** Shows the concrete rewards a purchase produced, resolving names from the offer's drop table. */
function ResultRewards({ result, offer }: { result: ShopPurchaseResult; offer: ShopOfferDetail }) {
  const { t } = useI18n();

  // Drop table is the source of names; purchase samples from it, so the join is complete.
  const infoByKey = new Map<string, { name: string; rarity_key?: string }>();
  offer.possible_rewards.forEach((reward) =>
    infoByKey.set(`${reward.type}:${reward.template_id}`, { name: reward.name, rarity_key: reward.rarity_key }),
  );

  type Row = { key: string; label: string; qty?: number; color?: string };
  const rows: Row[] = [];
  result.ingredients?.forEach((entry, idx) =>
    rows.push({ key: `ing-${idx}`, label: infoByKey.get(`ingredient:${entry.template_id}`)?.name ?? `#${entry.template_id}`, qty: entry.quantity }),
  );
  result.potions?.forEach((entry, idx) =>
    rows.push({ key: `pot-${idx}`, label: infoByKey.get(`potion:${entry.template_id}`)?.name ?? `#${entry.template_id}`, qty: entry.quantity }),
  );
  result.items?.forEach((entry, idx) =>
    rows.push({ key: `item-${idx}`, label: infoByKey.get(`item:${entry.template_id}`)?.name ?? `#${entry.template_id}`, color: rarityColor(entry.rarity_key) }),
  );

  return (
    <div style={{
      marginTop: 14, padding: "14px 16px", borderRadius: 10,
      background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.25)",
    }}>
      <div className="mono" style={{ fontSize: 10, letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--success)", marginBottom: 8 }}>
        {t("shop.youReceived")}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px 12px", fontSize: 13, color: "var(--bone)" }}>
        {rows.map((row) => (
          <span key={row.key} style={row.color ? { color: row.color } : undefined}>
            {row.label}{row.qty !== undefined ? ` ×${row.qty}` : ""}
          </span>
        ))}
      </div>
    </div>
  );
}

export function ShopOfferModal({ offerId, onClose }: { offerId: number; onClose: () => void }) {
  useModalScrollLock();
  const swipeToClose = useSwipeToClose(onClose);

  const { locale, t } = useI18n();
  const queryClient = useQueryClient();
  const [purchaseCount, setPurchaseCount] = useState(1);
  const [currency, setCurrency] = useState<PaymentCurrency | null>(null);
  const [result, setResult] = useState<BuyShopOfferResponse["purchase"]["result"] | null>(null);

  const me = queryClient.getQueryData<User>(["me"]);
  const detailQuery = useQuery({
    queryKey: ["shop", "offer", offerId],
    queryFn: () => api.shopOffer(offerId),
    staleTime: 30_000,
  });

  const offer = detailQuery.data;
  const availableCurrencies = useMemo<PaymentCurrency[]>(() => {
    if (!offer) return [];
    const list: PaymentCurrency[] = [];
    if (offer.prices.money_copper !== undefined) list.push("money_copper");
    if (offer.prices.premium_currency !== undefined) list.push("premium_currency");
    return list;
  }, [offer]);

  const activeCurrency: PaymentCurrency | null = currency ?? availableCurrencies[0] ?? null;
  const unitPrice = activeCurrency && offer ? offer.prices[activeCurrency] ?? 0 : 0;
  const totalPrice = unitPrice * Math.max(purchaseCount, 1);

  const balance = activeCurrency === "premium_currency" ? me?.premium_currency ?? 0 : me?.money_copper ?? 0;
  const notEnough = totalPrice > balance;

  const buyMutation = useMutation({
    mutationFn: () =>
      api.buyShopOffer(offerId, { purchase_count: purchaseCount, payment_currency: activeCurrency as PaymentCurrency }),
    onSuccess: (data) => {
      setResult(data.purchase.result);
      void queryClient.invalidateQueries({ queryKey: ["me"] });
      void queryClient.invalidateQueries({ queryKey: ["character"] });
      void queryClient.invalidateQueries({ queryKey: ["inventory"] });
      void queryClient.invalidateQueries({ queryKey: ["ingredients"] });
      void queryClient.invalidateQueries({ queryKey: ["potions"] });
      void queryClient.invalidateQueries({ queryKey: ["shop", "purchases"] });
    },
  });

  const canBuy =
    !!activeCurrency && purchaseCount >= 1 && !notEnough && !buyMutation.isPending && !result;

  const errorMessage = buyMutation.error instanceof ApiError ? buyMutation.error.message : null;

  return (
    /* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions */
    <div
      className="modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      style={{ alignItems: "flex-start", paddingTop: "clamp(60px, 6vh, 80px)", paddingBottom: "clamp(16px, 3vh, 40px)" }}
    >
      <div className="modal" {...swipeToClose} style={{ width: "min(560px, 94vw)", maxHeight: "calc(100vh - clamp(76px, 9vh, 120px))", display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Header */}
        <div style={{
          padding: "20px 24px 14px", borderBottom: "1px solid var(--line-soft)",
          display: "flex", justifyContent: "space-between", alignItems: "flex-start",
          background: "linear-gradient(135deg, rgba(59,130,246,0.08), rgba(15,23,42,0))",
        }}>
          <div>
            <h2 style={{ fontFamily: "var(--font-cinzel, 'Cinzel', serif)", fontSize: 19, fontWeight: 600, margin: 0, letterSpacing: "0.04em", color: "var(--bone)" }}>
              {offer?.name ?? "…"}
            </h2>
            {offer && (
              <div className="mono" style={{ fontSize: 10, letterSpacing: "0.18em", color: "var(--primary-bright)", marginTop: 5, textTransform: "uppercase" }}>
                {t(`shop.rewardKind.${offer.reward_kind}` as TranslationKey)} · {t(`shop.deliveryMode.${offer.delivery_mode}` as TranslationKey)}
              </div>
            )}
          </div>
          <button onClick={onClose} aria-label="Close" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-mute)", padding: 4, borderRadius: 6 }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ overflowY: "auto", padding: "16px 24px" }}>
          {detailQuery.isLoading && <LoadingLine />}

          {offer && (
            <>
              {offer.description && (
                <p style={{ fontSize: 13, color: "var(--text-dim)", margin: "0 0 14px", lineHeight: 1.5 }}>{offer.description}</p>
              )}

              {result ? (
                <ResultRewards result={result} offer={offer} />
              ) : (
                <>
                  {/* Possible rewards (only before purchase — hidden once a result exists) */}
                  <div className="mono" style={{ fontSize: 10, letterSpacing: "0.18em", color: "var(--text-mute)", marginBottom: 10, textTransform: "uppercase" }}>
                    {t("shop.possibleRewards")}
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 18 }}>
                    {offer.possible_rewards.map((reward, idx) => (
                      <div key={idx} style={{
                        display: "flex", justifyContent: "space-between", alignItems: "center",
                        padding: "10px 12px", borderRadius: 8,
                        background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)",
                      }}>
                        <span style={{ fontSize: 13, color: "var(--bone)" }}>
                          {reward.name}
                          {reward.rarity_key && (
                            <span className="mono" style={{ marginLeft: 8, fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--text-mute)" }}>
                              {reward.rarity_key}
                            </span>
                          )}
                        </span>
                        <span className="mono" style={{ fontSize: 12, fontWeight: 600, color: "var(--success)" }}>
                          {reward.chance_percent}%
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Purchase count */}
                  <label className="mono" style={{ display: "block", fontSize: 10, letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--text-mute)", marginBottom: 6 }}>
                    {t("shop.purchaseCount")}
                  </label>
                  <input
                    className="input"
                    type="number"
                    min={1}
                    value={purchaseCount}
                    onChange={(e) => setPurchaseCount(Math.max(1, Number(e.target.value) || 1))}
                    style={{ width: 120, marginBottom: 16 }}
                  />

                  {/* Payment currency selector */}
                  {availableCurrencies.length > 0 && (
                    <>
                      <div className="mono" style={{ fontSize: 10, letterSpacing: "0.18em", textTransform: "uppercase", color: "var(--text-mute)", marginBottom: 6 }}>
                        {t("shop.paymentCurrency")}
                      </div>
                      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
                        {availableCurrencies.map((cur) => {
                          const isActive = activeCurrency === cur;
                          return (
                            <button
                              key={cur}
                              onClick={() => setCurrency(cur)}
                              className={`btn ${isActive ? "btn-primary" : "btn-secondary"}`}
                              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
                            >
                              {cur === "premium_currency" ? <Gem size={13} /> : null}
                              {cur === "premium_currency"
                                ? offer.prices.premium_currency
                                : <CopperDisplay value={offer.prices.money_copper} locale={locale} />}
                            </button>
                          );
                        })}
                      </div>
                    </>
                  )}

                  {/* Total */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                    <span className="mono" style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.18em", color: "var(--text-mute)" }}>
                      {t("shop.quantity")}: {offer.quantity * purchaseCount}
                    </span>
                    <span className="mono" style={{ fontSize: 14, fontWeight: 700 }}>
                      {activeCurrency === "premium_currency"
                        ? <span style={{ color: "#C084FC" }}>{totalPrice} 💎</span>
                        : <CopperDisplay value={totalPrice} locale={locale} />}
                    </span>
                  </div>

                  {notEnough && (
                    <div style={{ fontSize: 12, color: "var(--danger, #EF4444)", marginBottom: 8 }}>{t("shop.insufficient")}</div>
                  )}
                  {errorMessage && (
                    <div style={{ fontSize: 12, color: "var(--danger, #EF4444)", marginBottom: 8 }}>{errorMessage}</div>
                  )}
                </>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: "12px 24px", borderTop: "1px solid var(--line-soft)", display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <button className="btn btn-secondary" onClick={onClose}>{t("shop.close")}</button>
          {!result && (
            <button className="btn btn-primary" disabled={!canBuy} onClick={() => buyMutation.mutate()}>
              {buyMutation.isPending ? t("shop.buying") : t("shop.buy")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
