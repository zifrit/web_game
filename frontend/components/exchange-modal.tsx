"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Gem, X } from "lucide-react";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useI18n } from "@/components/providers";
import { LoadingLine } from "@/components/ui";
import { formatCopperCompact } from "@/lib/i18n";
import { useModalScrollLock, useSwipeToClose } from "@/lib/use-modal-scroll-lock";

export function ExchangeModal({ onClose }: { onClose: () => void }) {
  useModalScrollLock();
  const swipeToClose = useSwipeToClose(onClose);

  const { locale, t } = useI18n();
  const queryClient = useQueryClient();
  const [done, setDone] = useState(false);

  const offersQuery = useQuery({
    queryKey: ["billing", "exchange-offers"],
    queryFn: api.billingExchangeOffers,
    staleTime: 30_000,
  });

  const exchangeMutation = useMutation({
    mutationFn: (offerId: number) => api.exchangeCurrency(offerId),
    onSuccess: () => {
      setDone(true);
      void queryClient.invalidateQueries({ queryKey: ["me"] });
      void queryClient.invalidateQueries({ queryKey: ["character"] });
    },
  });

  const errorMessage = exchangeMutation.error instanceof ApiError ? exchangeMutation.error.message : null;
  const offers = offersQuery.data ?? [];

  return (
    /* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions */
    <div
      className="modal-backdrop"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      style={{ alignItems: "flex-start", paddingTop: "clamp(60px, 6vh, 80px)", paddingBottom: "clamp(16px, 3vh, 40px)" }}
    >
      <div className="modal" {...swipeToClose} style={{ width: "min(480px, 94vw)", maxHeight: "calc(100vh - clamp(76px, 9vh, 120px))", display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Header */}
        <div style={{
          padding: "20px 24px 14px", borderBottom: "1px solid var(--line-soft)",
          display: "flex", justifyContent: "space-between", alignItems: "flex-start",
          background: "linear-gradient(135deg, rgba(192,132,252,0.10), rgba(15,23,42,0))",
        }}>
          <div>
            <h2 style={{ fontFamily: "var(--font-cinzel, 'Cinzel', serif)", fontSize: 19, fontWeight: 600, margin: 0, letterSpacing: "0.04em", color: "var(--bone)" }}>
              {t("exchange.title")}
            </h2>
            <div className="mono" style={{ fontSize: 9, letterSpacing: "0.22em", color: "#C084FC", marginTop: 5, textTransform: "uppercase" }}>
              {t("exchange.subtitle")}
            </div>
          </div>
          <button onClick={onClose} aria-label="Close" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-mute)", padding: 4, borderRadius: 6 }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ overflowY: "auto", padding: "16px 24px" }}>
          {offersQuery.isLoading && <LoadingLine />}

          {!offersQuery.isLoading && offers.length === 0 && (
            <div className="mono" style={{ fontSize: 13, color: "var(--text-mute)", textAlign: "center", padding: "40px 0" }}>
              {t("exchange.empty")}
            </div>
          )}

          {done && (
            <div style={{ marginBottom: 12, padding: "12px 14px", borderRadius: 10, background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.25)", color: "var(--success)", fontSize: 13 }}>
              {t("exchange.success")}
            </div>
          )}
          {errorMessage && (
            <div style={{ marginBottom: 12, fontSize: 12, color: "var(--danger, #EF4444)" }}>{errorMessage}</div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {offers.map((offer) => (
              <button
                key={offer.id}
                disabled={exchangeMutation.isPending}
                onClick={() => exchangeMutation.mutate(offer.id)}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "14px 16px", borderRadius: 10, cursor: "pointer",
                  background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)",
                  color: "var(--text)", width: "100%",
                }}
              >
                <span className="mono" style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 15, fontWeight: 700, color: "#C084FC" }}>
                  <Gem size={15} /> {offer.premium_cost}
                </span>
                <ArrowRight size={16} color="var(--text-mute)" />
                <span className="mono" style={{ fontSize: 15, fontWeight: 700, color: "#FBBF24" }}>
                  {formatCopperCompact(offer.money_copper_reward, locale)}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ padding: "12px 24px", borderTop: "1px solid var(--line-soft)", display: "flex", justifyContent: "flex-end" }}>
          <button className="btn btn-secondary" onClick={onClose}>{t("shop.close")}</button>
        </div>
      </div>
    </div>
  );
}
