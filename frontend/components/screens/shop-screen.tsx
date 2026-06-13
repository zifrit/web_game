"use client";

import { useQuery } from "@tanstack/react-query";
import { Gem } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { useI18n } from "@/components/providers";
import { CopperDisplay, LoadingLine } from "@/components/ui";
import { type TranslationKey } from "@/lib/i18n";
import { bestMediaUrl } from "@/lib/media";
import type { ShopOffer } from "@/lib/types";
import { ShopOfferModal } from "@/components/shop-offer-modal";
import { useIsMobile } from "@/lib/use-is-mobile";

function PriceTags({ offer }: { offer: ShopOffer }) {
  const { locale } = useI18n();
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
      {offer.prices.money_copper !== undefined && (
        <span className="mono" style={{
          fontSize: 12, fontWeight: 700,
          padding: "3px 9px", borderRadius: 6,
          background: "rgba(251,191,36,0.10)", border: "1px solid rgba(251,191,36,0.25)",
        }}>
          <CopperDisplay value={offer.prices.money_copper} locale={locale} />
        </span>
      )}
      {offer.prices.premium_currency !== undefined && (
        <span className="mono" style={{
          display: "inline-flex", alignItems: "center", gap: 4,
          fontSize: 12, fontWeight: 700, color: "#C084FC",
          padding: "3px 9px", borderRadius: 6,
          background: "rgba(192,132,252,0.10)", border: "1px solid rgba(192,132,252,0.25)",
        }}>
          <Gem size={12} /> {offer.prices.premium_currency}
        </span>
      )}
    </div>
  );
}

function ShopCard({ offer, onOpen }: { offer: ShopOffer; onOpen: (offer: ShopOffer) => void }) {
  const { t } = useI18n();
  const imageUrl = bestMediaUrl(offer.media, ["medium_url", "large_url", "small_url"]);

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", height: "100%", padding: 16, gap: 4 }}>
      <div style={{
        width: "100%", aspectRatio: "1 / 1", borderRadius: 10, overflow: "hidden",
        background: "#202B44", border: "1px solid #2E3B5A", position: "relative", marginBottom: 8,
      }}>
        {imageUrl && (
          <img src={imageUrl} alt={offer.name} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
        )}
      </div>

      {/* Content grows so the button below stays bottom-aligned across the row */}
      <div style={{ display: "flex", flexDirection: "column", gap: 4, flex: 1, minHeight: 0 }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          <span className="mono" style={{
            fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase",
            padding: "2px 7px", borderRadius: 4, color: "#94A3B8",
            background: "rgba(148,163,184,0.10)", border: "1px solid rgba(148,163,184,0.22)",
          }}>
            {t(`shop.rewardKind.${offer.reward_kind}` as TranslationKey)}
          </span>
          <span className="mono" style={{
            fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase",
            padding: "2px 7px", borderRadius: 4, color: "#60A5FA",
            background: "rgba(96,165,250,0.10)", border: "1px solid rgba(96,165,250,0.22)",
          }}>
            {t(`shop.deliveryMode.${offer.delivery_mode}` as TranslationKey)}
            {offer.delivery_mode === "chest" ? ` ×${offer.quantity}` : ""}
          </span>
        </div>

        <h3 style={{
          fontFamily: "var(--font-cinzel, 'Cinzel', serif)", fontSize: 16, fontWeight: 600,
          margin: "8px 0 0", color: "var(--bone)",
        }}>{offer.name}</h3>
        {offer.description && (
          <p style={{ fontSize: 12, color: "var(--text-mute)", margin: "4px 0 0", lineHeight: 1.4 }}>
            {offer.description}
          </p>
        )}

        <PriceTags offer={offer} />
      </div>

      <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={() => onOpen(offer)}>
        {t("shop.details")}
      </button>
    </div>
  );
}

export function ShopScreen() {
  const { t } = useI18n();
  const isMobile = useIsMobile();
  const [selected, setSelected] = useState<ShopOffer | null>(null);
  const offersQuery = useQuery({
    queryKey: ["shop", "offers"],
    queryFn: api.shopOffers,
    staleTime: 30_000,
  });

  if (offersQuery.isLoading) return <LoadingLine />;

  const offers = offersQuery.data ?? [];
  if (offers.length === 0) {
    return (
      <div className="mono" style={{ fontSize: 13, color: "var(--text-mute)", textAlign: "center", padding: "60px 0" }}>
        {t("shop.empty")}
      </div>
    );
  }

  return (
    <>
      <div style={{
        display: "grid",
        // Mobile: 2 compact cards per row (comp). Desktop: up to 5 (capped via max-width).
        gridTemplateColumns: isMobile
          ? "repeat(2, minmax(0, 1fr))"
          : "repeat(auto-fill, minmax(242px, 1fr))",
        gap: isMobile ? 11 : 16,
        maxWidth: 1274, // 5 × 242 + 4 × 16 gap
        marginInline: "auto",
      }}>
        {offers.map((offer) => (
          <ShopCard key={offer.id} offer={offer} onOpen={setSelected} />
        ))}
      </div>
      {selected && <ShopOfferModal offerId={selected.id} onClose={() => setSelected(null)} />}
    </>
  );
}
