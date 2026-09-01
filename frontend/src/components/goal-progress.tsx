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

type GoalStatusPresentation = {
  label: string;
  state: "done" | "running" | "blocked" | "queued";
  textClassName: string;
  progressClassName: string;
};

function goalStatusPresentation(raw: string): GoalStatusPresentation {
  switch (raw) {
    case "RUNNING":
      return {
        label: "正在执行",
        state: "running",
        textClassName: "text-ra-accent",
        progressClassName: "bg-ra-accent",
      };
    case "COMPLETED":
      return {
        label: "已完成",
        state: "done",
        textClassName: "text-ra-status-running",
        progressClassName: "bg-ra-status-running",
      };
    case "BLOCKED":
      return {
        label: "需要处理阻塞",
        state: "blocked",
        textClassName: "text-ra-status-error",
        progressClassName: "bg-ra-status-error",
      };
    case "INVALIDATED":
      return {
        label: "已失效",
        state: "blocked",
        textClassName: "text-ra-status-error",
        progressClassName: "bg-ra-status-error",
      };
    case "APPROVED":
    case "PLANNED":
      return {
        label: "等待启动",
        state: "queued",
        textClassName: "text-ra-text-secondary",
        progressClassName: "bg-ra-border-strong",
      };
    case "DRAFT":
      return {
        label: "草稿",
        state: "queued",
        textClassName: "text-ra-text-secondary",
        progressClassName: "bg-ra-border-strong",
      };
    default:
      return {
        label: raw || "未知状态",
        state: "queued",
        textClassName: "text-ra-text-secondary",
        progressClassName: "bg-ra-border-strong",
      };
  }
}

function taskStateClass(state: string) {
  if (state === "done") return "text-ra-status-running";
  if (state === "running") return "text-ra-accent";
  if (state === "blocked") return "text-ra-status-error";
  return "text-ra-text-tertiary";
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
  const goalStatus = goalStatusPresentation(goal.status);

  return (
    <section
      aria-labelledby="goal-progress-heading"
      className="border-t border-ra-border/70 pt-7"
    >
      <div className="mb-3 flex items-baseline justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-ra-text-tertiary">
            Agent progress
          </p>
          <h2
            id="goal-progress-heading"
            className="mt-1 truncate text-lg font-medium tracking-[-0.01em] text-ra-text"
          >
            {goal.title}
          </h2>
        </div>
        <span
          data-testid="goal-state-label"
          className={cn("shrink-0 text-xs font-medium", goalStatus.textClassName)}
        >
          {goalStatus.label}
        </span>
      </div>

      <div
        className="mb-3 flex items-center gap-3"
        aria-label={`执行进度 ${completed}/${links.length}`}
      >
        <div
          className="h-1 flex-1 overflow-hidden rounded-full bg-ra-tertiary"
          data-testid="goal-progress-bar"
        >
          <div
            className={cn(
              "h-full rounded-full transition-[width] duration-200",
              goalStatus.progressClassName,
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="shrink-0 font-mono text-[10px] tabular-nums text-ra-text-tertiary">
          {completed}/{links.length || 0}
        </span>
      </div>

      <ol className="divide-y divide-ra-border/50">
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
          return (
            <li
              key={task.task_id}
              className="group flex items-start gap-3 px-1 py-2.5 hover:bg-ra-light/35"
            >
              <span
                aria-hidden="true"
                className={cn(
                  "mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center",
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
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-3">
                  <p className="min-w-0 truncate text-sm text-ra-text">
                    {task.title.replace(/^\[[^\]]+\]\s*/, "")}
                  </p>
                  <span className="shrink-0 font-mono text-[10px] text-ra-text-tertiary">
                    {task.plan_task_id || `T${index + 1}`}
                  </span>
                </div>
                <p className={cn("mt-0.5 text-[11px]", taskStateClass(state))}>
                  {state === "done"
                    ? "结果已验证"
                    : state === "running"
                      ? "Agent 正在执行"
                      : state === "blocked"
                        ? "需要处理阻塞"
                        : "等待依赖完成"}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
