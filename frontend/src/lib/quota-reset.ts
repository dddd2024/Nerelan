import type { QuotaReset } from "@/lib/platform-client";

/** One reset as a sentence: "codex 的 7 days 额度提前重置：已用 91% → 0%". */
export function quotaResetText(reset: QuotaReset): string {
  const how = reset.kind === "early" ? "提前重置" : "已按时重置";
  return `${reset.provider} 的 ${reset.window} 额度${how}：已用 ${Math.round(reset.used_before)}% → ${Math.round(reset.used_after)}%`;
}

export function quotaResetKey(reset: QuotaReset): string {
  return `${reset.account_ref}:${reset.window}:${reset.previous_resets_at}`;
}
