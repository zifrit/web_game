import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Browser Async RPG",
  description: "Idle dungeon RPG MVP",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
