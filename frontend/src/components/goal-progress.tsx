import { Check, Circle, LoaderCircle, ShieldAlert } from "lucide-react";
import type { PlatformGoal } from "@/lib/platform-client";
import { cn } from "@/lib/cn";

function statusFor(raw: string) {
  if (raw === "READY_FOR_REVIEW" || raw === "READY_FOR_REVIEW_FIXTURE") return "done";
  if (
    raw === "RUNNING" ||
    raw === "RUNNING_FIXTURE" ||
    raw === "VALIDATING" ||
    raw === "PREPARING_WORKSPACE"
  ) {
    return "running";
  }
  if (raw === "FAILED" || raw === "BLOCKED" || raw === "CANCELLED") return "blocked";
  return "queued";
}

function progressClassName(status: PlatformGoal["status"]) {
  if (status === "RUNNING") return "bg-ra-accent";
  if (status === "COMPLETED") return "bg-ra-status-running";
  if (status === "BLOCKED" || status === "INVALIDATED") return "bg-ra-status-error";
  return "bg-ra-border-strong";
}

function taskStateClass(state: string) {
  if (state === "done") return "text-ra-status-running";
  if (state === "running") return "text-ra-accent";
  if (state === "blocked") return "text-ra-status-error";
  return "text-ra-text-tertiary";
}

function taskStateText(state: string) {
  if (state === "done") return "结果已验证";
  if (state === "running") return "Agent 正在执行";
  if (state === "blocked") return "需要处理阻塞";
  return "等待依赖完成";
}

export function GoalProgress({ goal }: { goal: PlatformGoal }) {
  const links =
    goal.task_links ??
    goal.tasks.map((task) => ({
      task_id: task.id,
      plan_task_id: task.id,
      status: "QUEUED",
      title: task.title,
    }));
  const completed = links.filter((task) => statusFor(task.status) === "done").length;
  const progress = links.length ? Math.round((completed / links.length) * 100) : 0;

  return (
    <section aria-label="执行进度" className="pt-4">
      <span className="sr-only">Agent progress</span>

      <div
        className="mb-2.5 flex items-center gap-3"
        aria-label={`执行进度 ${completed}/${links.length}`}
      >
        <div
          className="h-1 flex-1 overflow-hidden rounded-full bg-ra-tertiary"
          data-testid="goal-progress-bar"
        >
          <div
            className={cn(
              "h-full rounded-full transition-[width] duration-200",
              progressClassName(goal.status),
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
        <span
          data-testid="goal-progress-summary"
          className="shrink-0 font-mono text-[10px] tabular-nums text-ra-text-tertiary"
        >
          {completed}/{links.length || 0}
        </span>
      </div>

      <ol className="divide-y divide-ra-border/45">
        {links.map((task, index) => {
          const state = statusFor(task.status);
          const Icon =
            state === "done"
              ? Check
              : state === "running"
                ? LoaderCircle
                : state === "blocked"
                  ? ShieldAlert
                  : Circle;
          const statusText = taskStateText(state);
          return (
            <li
              key={task.task_id}
              className="group flex min-h-9 items-center gap-3 px-1 py-2 hover:bg-ra-light/30"
            >
              <span
                aria-hidden="true"
                className={cn(
                  "inline-flex h-4 w-4 shrink-0 items-center justify-center",
                  taskStateClass(state),
                )}
              >
                <Icon
                  className={cn(
                    state === "queued" ? "h-2.5 w-2.5" : "h-3.5 w-3.5",
                    state === "running" && "animate-spin",
                  )}
                />
              </span>
              <p className="min-w-0 flex-1 truncate text-sm text-ra-text">
                {task.title.replace(/^\[[^\]]+\]\s*/, "")}
              </p>
              <span
                className={cn(
                  "shrink-0 text-[11px]",
                  state === "running" || state === "blocked"
                    ? taskStateClass(state)
                    : "sr-only",
                )}
              >
                {statusText}
              </span>
              <span className="shrink-0 font-mono text-[10px] text-ra-text-tertiary">
                {task.plan_task_id || `T${index + 1}`}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
