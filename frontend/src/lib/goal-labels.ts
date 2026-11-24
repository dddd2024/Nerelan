import type { PlatformGoal } from "@/lib/platform-client";
import { modelName } from "@/lib/run-explain";

/**
 * What a goal's execution mode actually does, in the composer's words.
 * The stored pair (executor, orchestration) decides it: "opencode" alone runs
 * planner → coder → reviewer, so it must not be called "多 Agent".
 */
export function executionModeLabel(goal: Pick<PlatformGoal, "executor_kind" | "orchestration_mode"> & { binding_ref?: string }): string {
  if (goal.orchestration_mode === "agent_team") {
    // A team pinned to one binding runs every step on it (goal_service._task_route).
    return goal.binding_ref ? "多 Agent 分工（固定使用所选模型）" : "自动（按任务选择 Agent 和模型）";
  }
  switch (goal.executor_kind) {
    case "opencode":
      return goal.orchestration_mode === "sequential_team" ? "OpenCode：规划 → 编码 → 审查" : "OpenCode 单任务";
    case "claude_code":
      return "Claude Code 单任务（Claude 账号）";
    case "codex":
      return "Codex 单任务（ChatGPT 账号）";
    case "deterministic_fixture":
      return "无模型演练（只验证平台流程）";
    default:
      return goal.executor_kind;
  }
}

/** A binding as the Owner reads it: the model, without the account prefix. */
export function bindingLabel(goal: Pick<PlatformGoal, "binding_ref" | "orchestration_mode" | "executor_kind">): string {
  if (goal.binding_ref) return modelName(goal.binding_ref);
  if (goal.orchestration_mode === "agent_team") return "自动选择";
  if (goal.executor_kind === "deterministic_fixture") return "不需要模型";
  return "未选择";
}

export interface QuotaFit {
  status: string;
  uncertain?: boolean;
  estimated_at?: string;
}

const QUOTA_FIT_TEXT: Record<string, string> = {
  fits_now: "按预测，现有额度够完成全部步骤。",
  needs_a_reset: "按预测，额度要等下一次刷新后才够。",
  needs_another_model: "按预测，需要换一个模型或账户才够。",
  UNKNOWN: "还估算不出额度够不够（缺少账户用量数据，或有步骤还没分到账户）。",
};

/** The quota forecast as one sentence; it reserves nothing and promises nothing. */
export function quotaFitText(fit: QuotaFit | null | undefined): string {
  if (!fit) return "";
  const text = QUOTA_FIT_TEXT[fit.status] ?? `额度预测：${fit.status}`;
  return fit.uncertain && fit.status !== "UNKNOWN" ? `${text}（数据不完整，仅供参考）` : text;
}
