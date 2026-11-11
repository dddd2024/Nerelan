import type { GoalStatus } from "@/lib/platform-client";
import { runtimeMessage } from "@/lib/runtime-labels";

export function goalStatusLabel(status: GoalStatus | string): string {
  /*
   * "执行完成，待审查" rather than a bare "已完成".
   *
   * The runtime's COMPLETED means the Agent finished executing. It does not
   * mean the change was verified, reviewed or delivered, and the Runs page, the
   * Goal header, the task list and the roadmap all have to agree on one
   * authoritative state (`#448` §9). The longer wording is the one the
   * lifecycle contract tests pin, so it is the single shared mapping here.
   */
  return runtimeMessage(status).label;
}
