import { AlertTriangle, LoaderCircle } from "lucide-react";
import { Link } from "react-router";
import type { PlatformGoal, PlatformGoalTaskLink, PlatformTaskFailure } from "@/lib/platform-client";
import { formatRelativeTime } from "@/lib/format";
import { runtimeMessage } from "@/lib/runtime-labels";
import { displayTitle } from "@/lib/display-title";
import { cn } from "@/lib/cn";

const RUNNING = new Set(["RUNNING", "RUNNING_FIXTURE", "VALIDATING", "PREPARING_WORKSPACE"]);
const STOPPED = new Set(["FAILED", "BLOCKED", "INTERRUPTED", "CANCELLED"]);

const EXECUTORS: Record<string, string> = {
  opencode: "OpenCode", codex: "Codex", claude_code: "Claude Code", deterministic_fixture: "无模型验证",
};

/** A short, readable model name: the binding without its gateway prefix. */
export function modelName(binding?: string): string {
  if (!binding) return "";
  return binding.replace(/^magpie-/, "").replace(/^opencode-zen-free-/, "").replace(/^coding-/, "");
}

/** Why one attempt stopped, in product language, with the host's own words underneath. */
export function failureText(failure?: PlatformTaskFailure | null): { label: string; nextStep: string; detail: string } {
  if (!failure) return { label: "已停止", nextStep: "", detail: "" };
  // The class decides the label; a known code inside the detail (e.g. opencode_stalled) is more specific.
  const detailCode = /(?:^|[:\s])(opencode_stalled|opencode_timeout|functional_check_failed|executor_stalled)/.exec(failure.detail)?.[1];
  const primary = runtimeMessage(failure.classification || "failed");
  const specific = detailCode ? runtimeMessage(detailCode) : null;
  const chosen = specific && specific.nextStep ? specific : primary.nextStep ? primary : specific ?? primary;
  const label = chosen.label === (failure.classification || "failed") ? "已停止" : chosen.label;
  return { label, nextStep: chosen.nextStep, detail: failure.message || failure.detail };
}

function attemptLine(attempt: NonNullable<PlatformGoalTaskLink["attempts"]>[number], index: number) {
  const who = [EXECUTORS[attempt.executor_kind ?? ""] ?? attempt.executor_kind, modelName(attempt.binding_ref)]
    .filter(Boolean).join(" · ");
  const outcome = attempt.failure ? failureText(attempt.failure).label : runtimeMessage(attempt.status).label;
  return `第 ${index + 1} 次：${who || "未知 Agent"} — ${outcome}`;
}

/**
 * The one question a goal page must answer first: what is happening now, or
 * why it stopped and what to do. Built only from fields the host returns.
 */
export function GoalAttention({ goal }: { goal: PlatformGoal }) {
  const links = goal.task_links ?? [];
  const running = links.filter((link) => RUNNING.has(link.status));
  const stopped = links.filter((link) => STOPPED.has(link.status));
  if (running.length === 0 && stopped.length === 0) return null;
  return (
    <section aria-label="当前状况" data-testid="goal-attention" className="space-y-3">
      {running.map((link) => {
        const activity = link.activity;
        return (
          <div key={link.task_id} data-testid={`goal-now-${link.task_id}`}
            className="flex items-start gap-3 rounded-2xl border border-ra-accent/25 bg-ra-accent/5 px-4 py-3">
            <LoaderCircle className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-ra-accent" aria-hidden="true" />
            <div className="min-w-0 flex-1 space-y-0.5">
              <p className="text-sm font-medium text-ra-text">
                正在做：{activity?.description || activity?.title || "Agent 已启动，等待第一条动作"}
              </p>
              <p className="text-xs text-ra-text-secondary">
                {[displayTitle(link.title, 60), EXECUTORS[link.executor_kind ?? ""], modelName(link.binding_ref),
                  activity?.timestamp ? `最近动作 ${formatRelativeTime(activity.timestamp)}` : ""].filter(Boolean).join(" · ")}
              </p>
            </div>
          </div>
        );
      })}
      {stopped.map((link) => {
        const reason = failureText(link.failure);
        const attempts = link.attempts ?? [];
        return (
          <div key={link.task_id} role="alert" data-testid={`goal-stopped-${link.task_id}`}
            className="rounded-2xl border border-ra-status-error/30 bg-ra-status-error/5 px-4 py-3">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-ra-status-error" aria-hidden="true" />
              <div className="min-w-0 flex-1 space-y-1">
                <p className="text-sm font-semibold text-ra-text">为什么停下：{reason.label}</p>
                {reason.nextStep && <p className="text-sm text-ra-text-secondary">下一步：{reason.nextStep}</p>}
                {reason.detail && (
                  <p className="break-words font-mono text-[11px] leading-5 text-ra-text-tertiary" data-testid={`goal-stopped-detail-${link.task_id}`}>
                    {reason.detail}
                  </p>
                )}
                <p className="text-xs text-ra-text-secondary">
                  {[displayTitle(link.title, 60), EXECUTORS[link.executor_kind ?? ""], modelName(link.binding_ref)].filter(Boolean).join(" · ")}
                  {" · "}
                  <Link to={`/runs?task=${encodeURIComponent(link.task_id)}`} className="text-ra-accent underline-offset-4 hover:underline">查看这次运行</Link>
                </p>
              </div>
            </div>
            {attempts.length > 0 && (
              <ol className={cn("mt-3 space-y-1 border-t border-ra-status-error/15 pt-2 text-xs text-ra-text-secondary")}
                aria-label="之前的尝试" data-testid={`goal-attempts-${link.task_id}`}>
                {attempts.map((attempt, index) => (
                  <li key={attempt.task_id} title={attempt.failure?.message || attempt.failure?.detail || ""}>
                    {attemptLine(attempt, index)}
                  </li>
                ))}
                <li className="font-medium text-ra-text">第 {attempts.length + 1} 次（本次）：{reason.label}</li>
              </ol>
            )}
          </div>
        );
      })}
    </section>
  );
}
