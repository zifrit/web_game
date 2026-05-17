import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Backgrounds
        "bg-main":      "#0B1020",
        "bg-secondary": "#111827",
        "bg-card":      "#1A2235",
        "bg-elevated":  "#202B44",

        // Borders
        "border-base":  "#2E3B5A",
        "border-hover": "#4B6AA3",

        // Blue accents
        "blue-primary": "#3B82F6",
        "blue-deep":    "#2563EB",
        "blue-bright":  "#60A5FA",
        "cyan-accent":  "#38BDF8",

        // Rarity colours (used as text/border)
        "rarity-common":   "#9CA3AF",
        "rarity-uncommon": "#22C55E",
        "rarity-rare":     "#3B82F6",
        "rarity-epic":     "#A855F7",

        // Status
        success: "#22C55E",
        danger:  "#EF4444",
        warning: "#F59E0B",
        info:    "#38BDF8",

        // Legacy aliases kept so any leftover references compile
        ember:     "#d66a2f",
        ink:       "#101314",
        moss:      "#526f55",
        brass:     "#b99a57",
        parchment: "#efe5d0",
      },
      fontFamily: {
        cinzel: ["var(--font-cinzel)", "Cinzel", "serif"],
        inter:  ["var(--font-inter)",  "Inter",  "sans-serif"],
        mono:   ["var(--font-mono)",   "JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        "blue-glow":    "0 0 12px rgba(59, 130, 246, 0.15)",
        "blue-glow-md": "0 0 24px rgba(59, 130, 246, 0.25)",
        "card":         "0 4px 24px rgba(0, 0, 0, 0.4)",
        "panel":        "0 8px 40px rgba(0, 0, 0, 0.5)",
      },
      keyframes: {
        "fade-in": {
          "0%":   { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-blue": {
          "0%, 100%": { boxShadow: "0 0 8px rgba(59,130,246,0.3)" },
          "50%":      { boxShadow: "0 0 20px rgba(59,130,246,0.6)" },
        },
      },
      animation: {
        "fade-in":    "fade-in 200ms ease both",
        "pulse-blue": "pulse-blue 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
