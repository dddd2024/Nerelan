import { Check, Circle, LoaderCircle, ShieldAlert } from "lucide-react";
import type { PlatformGoal } from "@/lib/platform-client";
import { cn } from "@/lib/cn";

function statusFor(raw: string) {
  if (raw === "READY_FOR_REVIEW" || raw === "READY_FOR_REVIEW_FIXTURE") return "done";
  if (raw === "RUNNING" || raw === "RUNNING_FIXTURE" || raw === "VALIDATING" || raw === "PREPARING_WORKSPACE") return "running";
  if (raw === "FAILED" || raw === "BLOCKED" || raw === "CANCELLED") return "blocked";
  return "queued";
}

export function GoalProgress({ goal }: { goal: PlatformGoal }) {
  const links = goal.task_links ?? goal.tasks.map((task) => ({
    task_id: task.id, plan_task_id: task.id, status: "QUEUED", title: task.title,
  }));
  return (
    <section aria-labelledby="goal-progress-heading" className="border-t border-ra-border/70 pt-6">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-ra-text-tertiary">Agent progress</p>
          <h2 id="goal-progress-heading" className="mt-1 text-lg font-medium text-ra-text">{goal.title}</h2>
        </div>
        <span className="rounded-full border border-ra-border px-3 py-1 text-xs text-ra-text-secondary">{goal.status}</span>
      </div>
      <ol className="space-y-1">
        {links.map((task, index) => {
          const state = statusFor(task.status);
          const Icon = state === "done" ? Check : state === "running" ? LoaderCircle : state === "blocked" ? ShieldAlert : Circle;
          return (
            <li key={task.task_id} className="group flex items-start gap-3 rounded-xl px-3 py-3 hover:bg-ra-light/60">
              <span className={cn(
                "mt-0.5 inline-flex h-6 w-6 items-center justify-center rounded-full border",
                state === "done" && "border-emerald-400/40 bg-emerald-400/10 text-emerald-300",
                state === "running" && "border-blue-400/50 bg-blue-400/10 text-blue-300",
                state === "blocked" && "border-red-400/50 bg-red-400/10 text-red-300",
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
