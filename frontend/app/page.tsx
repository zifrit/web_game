"use client";

import { AppProviders } from "@/components/providers";
import { RpgClient } from "@/components/rpg-client";

export default function Home() {
  return (
    <AppProviders>
      <RpgClient />
    </AppProviders>
  );
}
