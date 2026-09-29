import type { GoalStatus } from "@/lib/platform-client";

export function goalStatusLabel(status: GoalStatus | string): string {
  if (status === "RUNNING") return "正在执行";
  /*
   * "执行完成，待审查" rather than a bare "已完成".
   *
   * The runtime's COMPLETED means the Agent finished executing. It does not
   * mean the change was verified, reviewed or delivered, and the Runs page, the
   * Goal header, the task list and the roadmap all have to agree on one
   * authoritative state (`#448` §9). The longer wording is the one the
   * lifecycle contract tests pin, so it is the single shared mapping here.
   */
  if (status === "COMPLETED") return "执行完成，待审查";
  if (status === "BLOCKED") return "需要处理阻塞";
  if (status === "INVALIDATED") return "已失效";
  if (status === "APPROVED" || status === "PLANNED") return "等待启动";
  if (status === "DRAFT") return "草稿";
  return status;
}
