import type { Metadata } from "next";
import { Forum, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});

// Display serif. Cinzel has no Cyrillic glyphs, so Russian titles fell back
// to Times. Forum is an engraved-capitals serif (same feel) WITH Cyrillic.
const cinzel = Forum({
  subsets: ["latin", "cyrillic"],
  weight: "400",
  variable: "--font-cinzel",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Ashreach — Async Dungeon RPG",
  description: "Idle dungeon RPG MVP",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${cinzel.variable} ${jetbrainsMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
