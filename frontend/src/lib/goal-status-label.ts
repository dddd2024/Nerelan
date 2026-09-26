import type { GoalStatus } from "@/lib/platform-client";

export function goalStatusLabel(status: GoalStatus | string): string {
  if (status === "RUNNING") return "正在执行";
  if (status === "COMPLETED") return "已完成";
  if (status === "BLOCKED") return "需要处理阻塞";
  if (status === "INVALIDATED") return "已失效";
  if (status === "APPROVED" || status === "PLANNED") return "等待启动";
  if (status === "DRAFT") return "草稿";
  return status;
}
