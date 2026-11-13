import { useState } from "react";
import { RotateCcw } from "lucide-react";
import { useRetryGoalStep } from "@/hooks/use-platform";
import { cn } from "@/lib/cn";
import { httpErrorMessage } from "@/lib/http-errors";
import { PlatformClientError, type PlatformRetryOptions } from "@/lib/platform-client";

const RETRY_ERRORS: Record<string, string> = {
  owner_retry_no_active_window: "执行窗口已结束，先开一个新窗口再重试。",
  owner_retry_not_agent_team: "只有按计划分步执行的目标能单独重试一步。",
  owner_retry_step_not_stopped: "这一步已经在跑了。",
  owner_retry_step_not_found: "计划里找不到这一步，刷新后再试。",
  owner_retry_host_check: "这一步是主机检查，不由模型完成，不能换模型重试。",
  owner_retry_review_unresolved: "上一次审查结果还没确定，先等它结束。",
  owner_retry_step_recovering: "主机还在收尾上一次尝试，稍后再试。",
  owner_retry_cleanup_unconfirmed: "上一次尝试的清理还没确认，先在运行详情里处理。",
  owner_retry_model_outside_window: "这个模型不在本窗口确认过的模型里。",
  owner_retry_model_choice_unavailable: "这个窗口没有确认过的模型列表，只能自动选模型。",
  owner_retry_model_unavailable: "这个模型现在不可用，换一个或自动选择。",
  owner_retry_no_model_in_window: "本窗口确认过的模型现在都不可用。",
  owner_retry_window_receipt_invalid: "找不到这个窗口的确认记录，不能重试。",
  goal_revision_conflict: "目标刚被修改过，刷新后再试。",
};

function retryError(error: unknown): string {
  if (error instanceof PlatformClientError) {
    return RETRY_ERRORS[error.code] ?? httpErrorMessage(error.status, error.code);
  }
  return "没能重试，请检查 Nerelan 是否在运行。";
}

export function poolLabel(entry: PlatformRetryOptions["pool"][number]): string {
  const model = entry.model_id || entry.binding_ref;
  return entry.executor_id ? `${model} · ${entry.executor_id}` : model;
}

/**
 * Owner decision 2026-11-12 A: retry a stopped step inside the goal's active window,
 * with the router's choice or a model the Owner confirmed for that window.
 */
export function StepRetry({ goalId, planTaskId, options }: {
  goalId: string;
  planTaskId: string;
  options?: PlatformRetryOptions;
}) {
  const mutation = useRetryGoalStep(goalId);
  const [binding, setBinding] = useState("");
  if (!options) return null;
  const left = options.automatic_retries_left[planTaskId];
  if (!options.available) {
    return (
      <p data-testid={`goal-retry-unavailable-${planTaskId}`} className="ml-7 mt-2 text-xs text-ra-text-secondary">
        {options.reason === "owner_retry_no_active_window"
          ? "要重试这一步，先开一个执行窗口。"
          : RETRY_ERRORS[options.reason] ?? "这一步现在不能重试。"}
      </p>
    );
  }
  const retry = (bindingRef: string) =>
    mutation.mutate({ planTaskId, revision: options.revision, bindingRef });
  return (
    <div data-testid={`goal-retry-${planTaskId}`} className="ml-7 mt-2 space-y-1.5 text-xs">
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" disabled={mutation.isPending} onClick={() => retry("")}
          className="inline-flex min-h-7 items-center gap-1.5 rounded-md border border-ra-border bg-ra-workspace px-2.5 font-medium text-ra-text hover:bg-ra-light disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
          <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
          重试（自动选模型）
        </button>
        {options.pool.length > 0 && (
          <>
            <label className="sr-only" htmlFor={`goal-retry-model-${planTaskId}`}>换一个模型</label>
            <select id={`goal-retry-model-${planTaskId}`} value={binding} disabled={mutation.isPending}
              onChange={(event) => setBinding(event.target.value)}
              className="min-h-7 max-w-[16rem] rounded-md border border-ra-border bg-ra-workspace px-2 text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
              <option value="">换一个模型…</option>
              {options.pool.map((entry) => (
                <option key={entry.binding_ref} value={entry.binding_ref}>{poolLabel(entry)}</option>
              ))}
            </select>
            <button type="button" disabled={!binding || mutation.isPending} onClick={() => retry(binding)}
              className="inline-flex min-h-7 items-center rounded-md px-2 font-medium text-ra-accent underline-offset-4 hover:underline disabled:text-ra-text-tertiary disabled:no-underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
              用这个模型重试
            </button>
          </>
        )}
      </div>
      <p className={cn("text-ra-text-tertiary", mutation.isError && "text-ra-status-error")} role={mutation.isError ? "alert" : undefined}>
        {mutation.isError ? retryError(mutation.error)
          : `重试算进窗口的任务数和 Token。${typeof left === "number" ? `这一步出现非模型原因的失败时，还会自动重试 ${left} 次。` : ""}`}
      </p>
    </div>
  );
}
