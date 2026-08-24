import { Check, Circle, LoaderCircle, ShieldAlert } from "lucide-react";
import type { PlatformGoal } from "@/lib/platform-client";
import { cn } from "@/lib/cn";

function statusFor(raw: string) {
  if (raw === "READY_FOR_REVIEW" || raw === "READY_FOR_REVIEW_FIXTURE") return "done";
  if (raw === "RUNNING" || raw === "RUNNING_FIXTURE" || raw === "VALIDATING" || raw === "PREPARING_WORKSPACE") return "running";
  if (raw === "FAILED" || raw === "BLOCKED" || raw === "CANCELLED") return "blocked";
  return "queued";
}

type GoalStatusPresentation = {
  label: string;
  state: "done" | "running" | "blocked" | "queued";
  className: string;
  textClassName: string;
  progressClassName: string;
};

function goalStatusPresentation(raw: string): GoalStatusPresentation {
  switch (raw) {
    case "RUNNING":
      return {
        label: "正在执行",
        state: "running",
        className: "border-ra-accent/40 bg-ra-accent/10 text-ra-accent",
        textClassName: "text-ra-accent",
        progressClassName: "bg-ra-accent",
      };
    case "COMPLETED":
      return {
        label: "已完成",
        state: "done",
        className: "border-ra-status-running/40 bg-ra-status-running/10 text-ra-status-running",
        textClassName: "text-ra-status-running",
        progressClassName: "bg-ra-status-running",
      };
    case "BLOCKED":
      return {
        label: "需要处理阻塞",
        state: "blocked",
        className: "border-ra-status-error/40 bg-ra-status-error/10 text-ra-status-error",
        textClassName: "text-ra-status-error",
        progressClassName: "bg-ra-status-error",
      };
    case "INVALIDATED":
      return {
        label: "已失效",
        state: "blocked",
        className: "border-ra-status-error/40 bg-ra-status-error/10 text-ra-status-error",
        textClassName: "text-ra-status-error",
        progressClassName: "bg-ra-status-error",
      };
    case "APPROVED":
    case "PLANNED":
      return {
        label: "等待启动",
        state: "queued",
        className: "border-ra-border text-ra-text-secondary",
        textClassName: "text-ra-text-secondary",
        progressClassName: "bg-ra-border-strong",
      };
    case "DRAFT":
      return {
        label: "草稿",
        state: "queued",
        className: "border-ra-border text-ra-text-secondary",
        textClassName: "text-ra-text-secondary",
        progressClassName: "bg-ra-border-strong",
      };
    default:
      return {
        label: raw || "未知状态",
        state: "queued",
        className: "border-ra-border text-ra-text-secondary",
        textClassName: "text-ra-text-secondary",
        progressClassName: "bg-ra-border-strong",
      };
  }
}

export function GoalProgress({ goal }: { goal: PlatformGoal }) {
  const links = goal.task_links ?? goal.tasks.map((task) => ({
    task_id: task.id, plan_task_id: task.id, status: "QUEUED", title: task.title,
  }));
  const completed = links.filter((task) => statusFor(task.status) === "done").length;
  const progress = links.length ? Math.round((completed / links.length) * 100) : 0;
  const goalStatus = goalStatusPresentation(goal.status);
  return (
    <section aria-labelledby="goal-progress-heading" className="border-t border-ra-border/70 pt-7">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-ra-text-tertiary">
            <span>Agent progress</span>
            <span className={cn("ml-2", goalStatus.textClassName)}>
              {goalStatus.label}
            </span>
          </p>
          <h2 id="goal-progress-heading" className="mt-1 text-lg font-medium text-ra-text">{goal.title}</h2>
        </div>
        <span
          data-testid="goal-state-label"
          className={cn("shrink-0 rounded-full border px-3 py-1 text-xs", goalStatus.className)}
        >
          {goalStatus.label}
        </span>
      </div>
      <div className="mb-4 flex items-center gap-3" aria-label={`执行进度 ${completed}/${links.length}`}>
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-ra-tertiary" data-testid="goal-progress-bar">
          <div className={cn("h-full rounded-full transition-[width] duration-200", goalStatus.progressClassName)} style={{ width: `${progress}%` }} />
        </div>
        <span className="shrink-0 font-mono text-[10px] text-ra-text-tertiary">{completed}/{links.length || 0}</span>
      </div>
      <ol className="space-y-1">
        {links.map((task, index) => {
          const state = statusFor(task.status);
          const Icon = state === "done" ? Check : state === "running" ? LoaderCircle : state === "blocked" ? ShieldAlert : Circle;
          return (
            <li key={task.task_id} className="group flex items-start gap-3 rounded-xl px-3 py-3 hover:bg-ra-light/60">
              <span className={cn(
                "mt-0.5 inline-flex h-6 w-6 items-center justify-center rounded-full border",
                state === "done" && "border-ra-status-running/40 bg-ra-status-running/10 text-ra-status-running",
                state === "running" && "border-ra-accent/50 bg-ra-accent/10 text-ra-accent",
                state === "blocked" && "border-ra-status-error/50 bg-ra-status-error/10 text-ra-status-error",
                state === "queued" && "border-ra-border text-ra-text-tertiary",
              )}>
                <Icon className={cn("h-3.5 w-3.5", state === "running" && "animate-spin")} />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-3">
                  <p className="text-sm text-ra-text">{task.title.replace(/^\[[^\]]+\]\s*/, "")}</p>
                  <span className="shrink-0 font-mono text-[10px] text-ra-text-tertiary">{task.plan_task_id || `T${index + 1}`}</span>
                </div>
                <p className="mt-1 text-xs text-ra-text-tertiary">
                  {state === "done" ? "结果已验证" : state === "running" ? "Agent 正在执行" : state === "blocked" ? "需要处理阻塞" : "等待依赖完成"}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
