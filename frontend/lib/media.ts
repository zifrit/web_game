import type { MediaAssetUrls } from "@/lib/types";

export function bestMediaUrl(
  media?: MediaAssetUrls | null,
  priority: Array<keyof MediaAssetUrls> = ["large_url", "medium_url", "small_url"],
) {
  if (!media) return "";
  for (const key of priority) {
    const value = media[key];
    if (value) return value;
  }
  return "";
}
