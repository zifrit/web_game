import clsx from "clsx";

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
        "inline-flex min-h-11 items-center justify-center gap-2 rounded-md border px-4 py-2 text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-50",
        variant === "primary" &&
          "border-brass bg-brass text-ink shadow-lg shadow-black/20 hover:bg-[#efc76c]",
        variant === "secondary" &&
          "border-white/15 bg-white/10 text-parchment hover:bg-white/15",
        variant === "danger" &&
          "border-blood bg-blood text-white hover:bg-[#cf4b57]",
        variant === "ghost" &&
          "border-transparent bg-transparent text-parchment hover:bg-white/10",
        className
      )}
      {...props}
    />
  );
}

export function Panel({
  children,
  className
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={clsx(
        "rounded-lg border border-white/12 bg-[#191713]/88 p-5 shadow-iron backdrop-blur",
        className
      )}
    >
      {children}
    </section>
  );
}

export function Field({
  label,
  error,
  children
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="grid gap-2 text-sm text-parchment/82">
      <span className="font-bold text-parchment">{label}</span>
      {children}
      {error ? <span className="text-sm text-[#ff9aa3]">{error}</span> : null}
    </label>
  );
}

export const inputClassName =
  "min-h-11 w-full rounded-md border border-white/15 bg-black/25 px-3 py-2 text-parchment placeholder:text-parchment/35 shadow-inner shadow-black/20 transition focus:border-brass";

export function EmptyState({
  title,
  body
}: {
  title: string;
  body: string;
}) {
  return (
    <div className="rounded-lg border border-dashed border-white/15 bg-black/20 p-6 text-center">
      <p className="text-lg font-bold text-parchment">{title}</p>
      <p className="mt-2 text-sm text-parchment/65">{body}</p>
    </div>
  );
}

export function ErrorNotice({ message }: { message?: string }) {
  if (!message) {
    return null;
  }

  return (
    <div className="rounded-md border border-blood/60 bg-blood/15 px-4 py-3 text-sm text-[#ffd6d9]">
      {message}
    </div>
  );
}

export function StatBadge({
  label,
  value,
  tone = "plain"
}: {
  label: string;
  value: string | number;
  tone?: "plain" | "good" | "warn";
}) {
  return (
    <div
      className={clsx(
        "rounded-md border px-3 py-2",
        tone === "plain" && "border-white/10 bg-white/[0.06]",
        tone === "good" && "border-moss/50 bg-moss/20",
        tone === "warn" && "border-ember/50 bg-ember/15"
      )}
    >
      <div className="text-xs uppercase text-parchment/55">{label}</div>
      <div className="mt-1 text-lg font-bold text-parchment">{value}</div>
    </div>
  );
}

export function LoadingLine({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-parchment/65">
      <span className="h-2 w-2 animate-pulse rounded-full bg-brass" />
      {label}
    </div>
  );
}

export function ItemGlyph({
  src,
  rarity,
  broken,
  size = "md"
}: {
  src?: string;
  rarity: string;
  broken?: boolean;
  size?: "sm" | "md" | "lg";
}) {
  const initials = rarity.slice(0, 1).toUpperCase();

  return (
    <div
      className={clsx(
        "grid shrink-0 place-items-center overflow-hidden rounded-md border bg-black/35",
        size === "sm" && "h-10 w-10",
        size === "md" && "h-14 w-14",
        size === "lg" && "h-24 w-24",
        broken ? "border-blood/70" : "border-brass/45"
      )}
    >
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img alt="" className="h-full w-full object-cover" src={src} />
      ) : (
        <span className="text-xl font-bold text-brass">{initials}</span>
      )}
    </div>
  );
}

export function formatCopper(value?: number) {
  return `${new Intl.NumberFormat("en-US").format(value ?? 0)} cp`;
}

export function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;

  if (minutes <= 0) {
    return `${rest}s`;
  }

  return `${minutes}m ${rest.toString().padStart(2, "0")}s`;
}

export function formatStatName(key: string) {
  return key.replaceAll("_", " ");
}
