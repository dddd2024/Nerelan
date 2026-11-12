import type { PlatformGoal } from "@/lib/platform-client";
import { isReviewReady, statusFor } from "@/components/goal-progress";
import { goalStatusLabel } from "@/lib/goal-status-label";
import { failureText } from "@/lib/run-explain";

export type GoalProgressTone = "live" | "stopped" | "done" | "waiting" | "idle";

const WAITING_ON_OWNER: Record<string, string> = {
  DRAFT: "草稿：等你生成计划",
  PLANNED: "计划已生成：等你审阅",
  APPROVED: "已批准：等待开启执行窗口",
};

function short(text: string, limit = 80): string {
  const line = text.replace(/\s+/g, " ").trim();
  return line.length > limit ? `${line.slice(0, limit - 1)}…` : line;
}

/**
 * One sentence on where a goal stands, for lists: what the agent is doing now,
 * why it stopped, or what it waits for. Built from the list's own task links,
 * so a list row needs no extra request.
 */
export function goalProgressLine(goal: Pick<PlatformGoal, "status" | "task_links">): { tone: GoalProgressTone; text: string } {
  const links = goal.task_links ?? [];
  const running = links.find((link) => statusFor(link.status) === "running");
  if (running) {
    const doing = short(running.activity?.description || running.activity?.title || "");
    return { tone: "live", text: `正在做：${doing || "Agent 已启动，等待第一条动作"}` };
  }
  const stopped = links.find((link) => ["FAILED", "BLOCKED", "INTERRUPTED"].includes(link.status));
  if (stopped) {
    const tries = (stopped.attempts?.length ?? 0) + 1;
    return { tone: "stopped", text: `已停下：${failureText(stopped.failure).label}${tries > 1 ? `（已试 ${tries} 次）` : ""}` };
  }
  if (links.length > 0) {
    const ready = links.filter((link) => isReviewReady(statusFor(link.status))).length;
    if (ready === links.length) return { tone: "done", text: "执行完成，等你审查" };
    return { tone: "waiting", text: `排队中：已完成 ${ready}/${links.length} 步` };
  }
  const waiting = WAITING_ON_OWNER[goal.status];
  if (waiting) return { tone: "waiting", text: waiting };
  return { tone: "idle", text: goalStatusLabel(goal.status) };
}

export const GOAL_PROGRESS_TONE_CLASS: Record<GoalProgressTone, string> = {
  live: "text-ra-accent",
  stopped: "text-ra-status-error",
  done: "text-ra-status-running",
  waiting: "text-ra-text-secondary",
  idle: "text-ra-text-tertiary",
};
