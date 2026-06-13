import clsx from "clsx";
import { splitCopper } from "@/lib/i18n";
import type { Locale } from "@/lib/i18n";

/* ─────────────────────────────────────────
   Button
───────────────────────────────────────── */
export function Button({
  className,
  variant = "primary",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost";
}) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-[10px] px-4 py-2.5 text-sm font-semibold transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-45",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3B82F6]/50",
        variant === "primary" &&
          "bg-[#2563EB] text-white shadow-[0_0_12px_rgba(59,130,246,0.2)] hover:-translate-y-px hover:bg-[#3B82F6] hover:shadow-[0_0_18px_rgba(59,130,246,0.35)] disabled:translate-y-0",
        variant === "secondary" &&
          "border border-[#3B82F6] bg-transparent text-[#60A5FA] hover:-translate-y-px hover:bg-[#3B82F6]/10 disabled:translate-y-0",
        variant === "danger" &&
          "bg-[#EF4444] text-white hover:-translate-y-px hover:bg-[#DC2626] disabled:translate-y-0",
        variant === "ghost" &&
          "border border-transparent bg-transparent text-[#94A3B8] hover:bg-[#3B82F6]/10 hover:text-white",
        className
      )}
      {...props}
    />
  );
}

/* ─────────────────────────────────────────
   Panel
───────────────────────────────────────── */
export function Panel({
  children,
  className,
  glow,
}: {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
}) {
  return (
    <section
      className={clsx(
        "rounded-xl border border-[#2E3B5A] bg-[#1A2235] p-5 shadow-[0_4px_24px_rgba(0,0,0,0.4)]",
        glow && "animate-pulse-glow",
        className
      )}
    >
      {children}
    </section>
  );
}

/* ─────────────────────────────────────────
   Field
───────────────────────────────────────── */
export function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="grid gap-1.5 text-sm">
      <span className="font-medium text-[#94A3B8]">{label}</span>
      {children}
      {error ? (
        <span className="text-xs text-[#EF4444]">{error}</span>
      ) : null}
    </label>
  );
}

export const inputClassName =
  "min-h-11 w-full rounded-lg border border-[#2E3B5A] bg-[#0B1020]/80 px-3 py-2.5 text-[#E2E8F0] placeholder:text-[#64748B] transition focus:border-[#3B82F6] focus:outline-none focus:ring-2 focus:ring-[#3B82F6]/15";

/* ─────────────────────────────────────────
   EmptyState
───────────────────────────────────────── */
export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-xl border border-dashed border-[#2E3B5A] bg-[#111827]/60 p-6 text-center">
      <p className="font-semibold text-[#E2E8F0]">{title}</p>
      <p className="mt-1.5 text-sm text-[#64748B]">{body}</p>
    </div>
  );
}

/* ─────────────────────────────────────────
   ErrorNotice
───────────────────────────────────────── */
export function ErrorNotice({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <div className="rounded-lg border border-[#EF4444]/40 bg-[#EF4444]/10 px-4 py-3 text-sm text-[#FCA5A5]">
      {message}
    </div>
  );
}

/* ─────────────────────────────────────────
   StatBadge
───────────────────────────────────────── */
export function StatBadge({
  label,
  value,
  tone = "plain",
}: {
  label: string;
  value: string | number;
  tone?: "plain" | "good" | "warn";
}) {
  return (
    <div
      className={clsx(
        "rounded-lg border px-3 py-2",
        tone === "plain" && "border-[#2E3B5A] bg-[#202B44]",
        tone === "good"  && "border-[#22C55E]/30 bg-[#22C55E]/10",
        tone === "warn"  && "border-[#F59E0B]/30 bg-[#F59E0B]/10"
      )}
    >
      <div className="text-[11px] uppercase tracking-wider text-[#64748B]">{label}</div>
      <div
        className={clsx(
          "mt-0.5 text-base font-bold",
          tone === "plain" && "text-[#E2E8F0]",
          tone === "good"  && "text-[#22C55E]",
          tone === "warn"  && "text-[#F59E0B]"
        )}
      >
        {value}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────
   LoadingLine
───────────────────────────────────────── */
export function LoadingLine({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-[#64748B]">
      <span className="h-2 w-2 animate-pulse rounded-full bg-[#3B82F6]" />
      {label}
    </div>
  );
}

/* ─────────────────────────────────────────
   ItemGlyph — rarity-aware item icon cell
───────────────────────────────────────── */
const rarityBorder: Record<string, string> = {
  f: "border-[#94A3B8]/40",
  e: "border-[#22C55E]/50 shadow-[0_0_8px_rgba(34,197,94,0.2)]",
  d: "border-[#38BDF8]/50 shadow-[0_0_8px_rgba(56,189,248,0.22)]",
  c: "border-[#3B82F6]/50 shadow-[0_0_8px_rgba(59,130,246,0.25)]",
  b: "border-[#A855F7]/50 shadow-[0_0_10px_rgba(168,85,247,0.3)]",
  a: "border-[#F59E0B]/50 shadow-[0_0_10px_rgba(245,158,11,0.3)]",
  s: "border-[#EF4444]/50 shadow-[0_0_12px_rgba(239,68,68,0.32)]",
  ex: "border-[#F8FAFC]/70 shadow-[0_0_14px_rgba(248,250,252,0.35)]",
};

const rarityText: Record<string, string> = {
  f: "text-[#94A3B8]",
  e: "text-[#22C55E]",
  d: "text-[#38BDF8]",
  c: "text-[#3B82F6]",
  b: "text-[#A855F7]",
  a: "text-[#F59E0B]",
  s: "text-[#EF4444]",
  ex: "text-[#F8FAFC]",
};

export function ItemGlyph({
  src,
  rarity,
  broken,
  size = "md",
}: {
  src?: string;
  rarity: string;
  broken?: boolean;
  size?: "sm" | "md" | "lg";
}) {
  const borderClass = broken
    ? "border-[#EF4444]/60"
    : (rarityBorder[rarity.toLowerCase()] ?? rarityBorder.f);

  return (
    <div
      className={clsx(
        "relative grid shrink-0 place-items-center overflow-hidden rounded-lg border bg-[#0B1020]/60",
        size === "sm" && "h-10 w-10",
        size === "md" && "h-14 w-14",
        size === "lg" && "h-24 w-24",
        borderClass,
        broken && "opacity-70"
      )}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img alt="" className="h-full w-full object-cover" src={src} />
      ) : (
        <span
          className={clsx(
            "text-xl font-bold",
            rarityText[rarity.toLowerCase()] ?? rarityText.f
          )}
        >
          {rarity.slice(0, 1).toUpperCase()}
        </span>
      )}
      {broken && (
        <span className="absolute bottom-0.5 right-0.5 text-[10px] leading-none text-[#EF4444]">
          X
        </span>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────
   RarityLabel
───────────────────────────────────────── */
export function RarityLabel({ rarity }: { rarity: string }) {
  return (
    <span
      className={clsx(
        "text-xs font-bold uppercase tracking-widest",
        rarityText[rarity.toLowerCase()] ?? rarityText.f
      )}
    >
      {rarity}
    </span>
  );
}

/* ─────────────────────────────────────────
   Skeleton primitives
───────────────────────────────────────── */

/** Generic shimmer block. Pass className for shape/size. */
export function Skeleton({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={clsx("skeleton", className)} style={style} />;
}

/** One or several lines of skeleton text. */
export function SkeletonText({
  lines = 1,
  widths,
  className,
}: {
  lines?: number;
  widths?: (string | number)[];
  className?: string;
}) {
  return (
    <div className={clsx("flex flex-col gap-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          style={{
            height: 12,
            width: widths?.[i] ?? (i === lines - 1 && lines > 1 ? "60%" : "100%"),
          }}
        />
      ))}
    </div>
  );
}

/* ── CharacterScreen skeleton ── */
export function CharacterScreenSkeleton() {
  return (
    <div className="dashboard animate-fade-in">

      {/* LEFT: character panel */}
      <div className="card">
        <div className="card-h">
          <div style={{ display: "flex", flexDirection: "column", gap: 6, flex: 1 }}>
            <Skeleton style={{ height: 18, width: "60%" }} />
            <Skeleton style={{ height: 10, width: "40%" }} />
          </div>
        </div>
        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Portrait */}
          <Skeleton className="skeleton-portrait" style={{ width: "100%" }} />
          {/* Name + class */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
            <Skeleton style={{ height: 18, width: "55%" }} />
            <Skeleton style={{ height: 10, width: "70%" }} />
          </div>
          {/* XP + HP bars */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {[0, 1].map((i) => (
              <div key={i} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <Skeleton style={{ height: 10, width: 60 }} />
                  <Skeleton style={{ height: 10, width: 50 }} />
                </div>
                <Skeleton style={{ height: 8, width: "100%", borderRadius: 100 }} />
              </div>
            ))}
          </div>
          <div className="divider" />
          {/* Stats grid */}
          <div className="stat-list" style={{ gridTemplateColumns: "1fr 1fr" }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="sl-row">
                <Skeleton style={{ height: 10, width: 50 }} />
                <Skeleton style={{ height: 12, width: 30 }} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CENTER: equipment + quick dungeons */}
      <div className="col">
        <div className="card">
          <div className="card-h">
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <Skeleton style={{ height: 18, width: 130 }} />
              <Skeleton style={{ height: 10, width: 90 }} />
            </div>
          </div>
          <div className="card-body">
            <div className="equipment-layout">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="skeleton-slot" />
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-h">
            <div style={{ display: "flex", flexDirection: "column", gap: 6, flex: 1 }}>
              <Skeleton style={{ height: 18, width: 140 }} />
              <Skeleton style={{ height: 10, width: 100 }} />
            </div>
            <Skeleton style={{ height: 32, width: 64, borderRadius: 10 }} />
          </div>
          <div className="card-body">
            <div className="quick-dungeons">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="quick-d" style={{ cursor: "default" }}>
                  <Skeleton style={{ width: 64, height: 64, borderRadius: 8, flexShrink: 0 }} />
                  <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
                    <Skeleton style={{ height: 14, width: "55%" }} />
                    <Skeleton style={{ height: 10, width: "80%" }} />
                  </div>
                  <Skeleton style={{ height: 34, width: 60, borderRadius: 10 }} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT: inventory mini-grid */}
      <div className="card">
        <div className="card-h">
          <div style={{ display: "flex", flexDirection: "column", gap: 6, flex: 1 }}>
            <Skeleton style={{ height: 18, width: 90 }} />
            <Skeleton style={{ height: 10, width: 130 }} />
          </div>
          <Skeleton style={{ height: 28, width: 28, borderRadius: 8 }} />
        </div>
        <div className="card-body">
          <div className="inv-grid">
            {Array.from({ length: 24 }).map((_, i) => (
              <Skeleton key={i} className="skeleton-inv" />
            ))}
          </div>
          <div className="divider" />
          {[0, 1].map((i) => (
            <div key={i} className="log-line">
              <Skeleton style={{ height: 10, width: 40 }} />
              <Skeleton style={{ height: 10, flex: 1 }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── InventoryScreen skeleton ── */
export function InventoryScreenSkeleton() {
  return (
    <div className="col animate-fade-in">
      {/* Top stat cards */}
      <div className="grid-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="card">
            <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <Skeleton style={{ height: 10, width: 80 }} />
              <Skeleton style={{ height: 26, width: "50%" }} />
            </div>
          </div>
        ))}
      </div>

      <div className="inventory-main-layout">
        {/* Pack grid */}
        <div className="card">
          <div className="card-h">
            <Skeleton style={{ height: 18, width: 100 }} />
            <Skeleton style={{ height: 10, width: 80 }} />
          </div>
          <div className="card-body">
            <div className="inv-grid inventory-pack-grid">
              {Array.from({ length: 24 }).map((_, i) => (
                <Skeleton key={i} className="skeleton-inv" style={{ width: 102 }} />
              ))}
            </div>
          </div>
        </div>

        {/* Detail pane placeholder */}
        <aside className="inventory-detail-pane">
          <div style={{
            borderRadius: 14, border: "1px dashed var(--line)",
            background: "rgba(17,24,39,0.6)", padding: 24,
            display: "flex", flexDirection: "column", gap: 14,
          }}>
            <Skeleton style={{ height: 14, width: "50%", margin: "0 auto" }} />
            <Skeleton style={{ height: 11, width: "80%", margin: "0 auto" }} />
          </div>
        </aside>
      </div>
    </div>
  );
}

/* ── Sidebar avatar skeleton ── */
export function SidebarAvatarSkeleton({ size = 36 }: { size?: number }) {
  return (
    <Skeleton
      className="skeleton-avatar"
      style={{ width: size, height: size, borderRadius: 8 }}
    />
  );
}

/* ─────────────────────────────────────────
   CopperDisplay
───────────────────────────────────────── */
const GOLD_COLOR = "#FBBF24";
const SILVER_COLOR = "#CBD5E1";
const COPPER_COLOR = "#CD7C45";

export function CopperDisplay({
  value,
  locale,
  compact = true,
  style,
}: {
  value: number | undefined | null;
  locale: Locale;
  compact?: boolean;
  style?: React.CSSProperties;
}) {
  if (value === undefined || value === null) {
    return <span style={{ color: "var(--text-mute)", ...style }}>?</span>;
  }
  const { gold, silver, copper } = splitCopper(value);
  const labels = locale === "ru"
    ? { gold: "з", silver: "с", copper: "м" }
    : { gold: "g", silver: "s", copper: "c" };

  const parts: React.ReactNode[] = [];
  if (compact) {
    if (gold > 0) parts.push(<span key="g" style={{ color: GOLD_COLOR }}>{gold}{labels.gold}</span>);
    if (silver > 0) parts.push(<span key="s" style={{ color: SILVER_COLOR }}>{silver}{labels.silver}</span>);
    if (copper > 0 || parts.length === 0) parts.push(<span key="c" style={{ color: COPPER_COLOR }}>{copper}{labels.copper}</span>);
  } else {
    parts.push(<span key="g" style={{ color: GOLD_COLOR }}>{gold}{labels.gold}</span>);
    parts.push(<span key="s" style={{ color: SILVER_COLOR }}>{silver}{labels.silver}</span>);
    parts.push(<span key="c" style={{ color: COPPER_COLOR }}>{copper}{labels.copper}</span>);
  }

  return (
    <span style={{ display: "inline-flex", alignItems: "baseline", gap: 3, ...style }}>
      {parts}
    </span>
  );
}

/* ─────────────────────────────────────────
   Helpers
───────────────────────────────────────── */
export function formatCopper(value?: number) {
  return `${new Intl.NumberFormat("en-US").format(value ?? 0)} cp`;
}

export function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  if (minutes <= 0) return `${rest}s`;
  return `${minutes}m ${rest.toString().padStart(2, "0")}s`;
}

export function formatStatName(key: string) {
  return key.replaceAll("_", " ");
}
