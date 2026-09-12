import { Check, Circle, LoaderCircle, PauseCircle, ShieldAlert } from "lucide-react";
import { Link } from "react-router";
import type { PlatformGoal, PlatformGoalTaskLink } from "@/lib/platform-client";
import { FUNCTIONAL_STATUS_LABELS, normalizeFunctionalValidation } from "@/lib/functional-validation";
import { FunctionalValidationView } from "@/components/functional-validation";
import { cn } from "@/lib/cn";

function statusFor(raw: string) {
  if (raw === "INTERRUPTED") return "interrupted";
  if (raw === "READY_FOR_REVIEW") return "review-ready";
  if (raw === "READY_FOR_REVIEW_FIXTURE") return "fixture-review-ready";
  if (["RUNNING", "RUNNING_FIXTURE", "VALIDATING", "PREPARING_WORKSPACE"].includes(raw)) return "running";
  if (["FAILED", "BLOCKED", "CANCELLED"].includes(raw)) return "blocked";
  return "queued";
}

function isReviewReady(state: string) {
  return state === "review-ready" || state === "fixture-review-ready";
}

function progressClassName(status: PlatformGoal["status"]) {
  if (status === "RUNNING") return "bg-ra-accent";
  if (status === "COMPLETED") return "bg-ra-status-running";
  if (status === "BLOCKED" || status === "INVALIDATED") return "bg-ra-status-error";
  return "bg-ra-border-strong";
}

function taskStateClass(state: string) {
  if (state === "interrupted" || state === "blocked") return "text-ra-status-error";
  if (isReviewReady(state)) return "text-ra-status-running";
  if (state === "running") return "text-ra-accent";
  return "text-ra-text-tertiary";
}

function taskStateText(state: string) {
  if (state === "interrupted") return "执行已中断";
  if (state === "review-ready") return "执行完成，待审查";
  if (state === "fixture-review-ready") return "Fixture 完成，待审查";
  if (state === "running") return "Agent 正在执行";
  if (state === "blocked") return "需要处理阻塞";
  return "等待依赖完成";
}

function publicationText(publication: PlatformGoalTaskLink["publication"]) {
  if (!publication) return "尚无发布记录";
  if (publication.status === "PENDING") return "等待发布";
  if (publication.status === "COMMIT_CREATED") return "提交已生成，尚未发布";
  if (publication.status === "PUSHED") return "分支已推送，Draft 尚未确认";
  if (publication.status === "FAILED") return "发布未完成";
  if (publication.status === "COMPLETE" && Number.isSafeInteger(publication.pr_number) && publication.pr_number > 0) {
    return `已记录 Draft PR #${publication.pr_number}`;
  }
  return "发布记录不完整，Draft 尚未确认";
}

export function GoalProgress({ goal }: { goal: PlatformGoal }) {
  const materialized = Boolean(goal.task_links?.length);
  const links: PlatformGoalTaskLink[] = materialized ? goal.task_links! : goal.tasks.map((task) => ({
    task_id: task.id, plan_task_id: task.id, status: "QUEUED", title: task.title,
  }));
  const reviewReady = links.filter((task) => isReviewReady(statusFor(task.status))).length;
  const progress = links.length ? Math.round((reviewReady / links.length) * 100) : 0;

  return (
    <section aria-label="执行进度" className="pt-4">
      <span className="sr-only">Agent progress</span>
      <div className="mb-2.5 flex items-center gap-3" aria-label={`执行进度 ${reviewReady}/${links.length}`}>
        <div className="h-1 flex-1 overflow-hidden rounded-full bg-ra-tertiary" data-testid="goal-progress-bar">
          <div className={cn("h-full rounded-full transition-[width] duration-200", progressClassName(goal.status))} style={{ width: `${progress}%` }} />
        </div>
        <span data-testid="goal-progress-summary" className="shrink-0 font-mono text-[10px] tabular-nums text-ra-text-tertiary">
          {reviewReady}/{links.length}
        </span>
      </div>
      {materialized && <p className="mb-2 text-xs leading-5 text-ra-text-secondary">
        执行进度不代表功能验证或交付完成。远端审查、合并与交付尚未确认。
      </p>}
      <ol className="divide-y divide-ra-border/45">
        {links.map((task, index) => {
          const state = statusFor(task.status);
          const Icon = isReviewReady(state) ? Check : state === "running" ? LoaderCircle
            : state === "interrupted" ? PauseCircle : state === "blocked" ? ShieldAlert : Circle;
          // A fixture lifecycle can never promote malformed evidence to real acceptance.
          const executor = task.status.endsWith("_FIXTURE") ? "deterministic_fixture" : task.executor_kind;
          const proof = normalizeFunctionalValidation(task.functional_validation, executor);
          return <li key={task.task_id} data-testid={`goal-task-${task.task_id}`} className="px-1 py-3 hover:bg-ra-light/30">
            <div className="flex min-w-0 items-start gap-3">
              <span aria-hidden="true" className={cn("mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center", taskStateClass(state))}>
                <Icon className={cn(state === "queued" ? "h-2.5 w-2.5" : "h-3.5 w-3.5", state === "running" && "animate-spin")} />
              </span>
              <p className="min-w-0 flex-1 break-words text-sm text-ra-text">{task.title.replace(/^\[[^\]]+\]\s*/, "")}</p>
              <span className="shrink-0 font-mono text-[10px] text-ra-text-tertiary">{task.plan_task_id || `T${index + 1}`}</span>
            </div>
            <div className="ml-7 mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px]">
              <span className={taskStateClass(state)}>{materialized ? taskStateText(state) : "尚未启动"}</span>
              {materialized && <>
                <span data-testid={`goal-functional-status-${task.task_id}`} className={proof.verified ? "text-ra-status-running" : proof.status === "FAILED" ? "text-ra-status-error" : "text-ra-text-secondary"}>
                  {FUNCTIONAL_STATUS_LABELS[proof.status]}
                </span>
                <Link to={`/runs?task=${encodeURIComponent(task.task_id)}`}
                  aria-label={`查看 ${task.title} 的${state === "interrupted" ? "中断" : ""}运行`}
                  className="rounded text-ra-accent underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
                  查看运行
                </Link>
              </>}
            </div>
            {materialized && <div className="ml-7 mt-1 space-y-2">
              <p data-testid={`goal-publication-${task.task_id}`} className="text-[11px] text-ra-text-secondary">{publicationText(task.publication)}</p>
              <details className="text-xs text-ra-text-secondary">
                <summary className="w-fit cursor-pointer rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">查看功能检查</summary>
                <FunctionalValidationView evidence={proof} executor={executor} />
              </details>
            </div>}
          </li>;
        })}
      </ol>
    </section>
  );
}
