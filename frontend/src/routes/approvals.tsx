import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { useSearchParams } from "react-router";
import {
  useApproveExistingGoal,
  useLaunchExistingGoal,
  usePlanExistingGoal,
} from "@/hooks/use-goal-continuation";
import { useGoal, useGoals } from "@/hooks/use-platform";
import { cn } from "@/lib/cn";
import type { GoalStatus, PlatformGoal } from "@/lib/platform-client";

const PENDING_STATUSES = new Set<GoalStatus>(["DRAFT", "PLANNED", "APPROVED"]);

const STATUS_LABELS: Record<GoalStatus, string> = {
  DRAFT: "草稿",
  PLANNED: "待审批",
  APPROVED: "已批准，待启动",
  RUNNING: "运行中",
  COMPLETED: "已完成",
  BLOCKED: "已阻塞",
  INVALIDATED: "已失效",
};

function mutationMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return "目标操作未完成，请读取最新状态后重试。";
}

function GoalDetail({
  goal,
  onPlan,
  onApprove,
  onLaunch,
  pending,
  error,
}: {
  goal: PlatformGoal;
  onPlan: () => void;
  onApprove: () => void;
  onLaunch: (hours: number) => void;
  pending: boolean;
  error: unknown;
}) {
  const [autonomyHours, setAutonomyHours] = useState(2);
  const canPlan = goal.status === "DRAFT";
  const canApprove = goal.status === "PLANNED";
  const canLaunch = goal.status === "APPROVED";

  return (
    <section
      data-testid="approval-goal-detail"
      className="min-w-0 rounded-2xl border border-ra-border bg-ra-base p-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-ra-text-tertiary">
            Goal
          </p>
          <h2 className="mt-1 text-xl font-semibold text-ra-text">{goal.title}</h2>
          <p className="mt-2 text-sm leading-6 text-ra-text-secondary">
            {goal.objective}
          </p>
        </div>
        <span className="rounded-full bg-ra-light px-2.5 py-1 text-xs text-ra-text-secondary">
          {STATUS_LABELS[goal.status]}
        </span>
      </div>

      <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs text-ra-text-tertiary">Repository</dt>
          <dd className="mt-1 break-all text-ra-text-secondary">{goal.repository}</dd>
        </div>
        <div>
          <dt className="text-xs text-ra-text-tertiary">Revision</dt>
          <dd className="mt-1 text-ra-text-secondary">{goal.revision}</dd>
        </div>
        <div>
          <dt className="text-xs text-ra-text-tertiary">Executor</dt>
          <dd className="mt-1 text-ra-text-secondary">{goal.executor_kind}</dd>
        </div>
        <div>
          <dt className="text-xs text-ra-text-tertiary">Binding</dt>
          <dd className="mt-1 break-all text-ra-text-secondary">
            {goal.binding_ref || "未绑定（当前持久化值为空）"}
          </dd>
        </div>
      </dl>

      {goal.status !== "DRAFT" && (
        <div className="mt-6">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-ra-text-tertiary">
            当前计划
          </p>
          <pre
            data-testid="approval-plan"
            className="mt-2 whitespace-pre-wrap rounded-xl border border-ra-border bg-ra-light/30 p-4 font-sans text-sm leading-6 text-ra-text-secondary"
          >
            {goal.plan_markdown || "当前 Goal 没有可显示的计划内容。"}
          </pre>
        </div>
      )}

      {goal.acceptance_criteria.length > 0 && goal.status !== "DRAFT" && (
        <div className="mt-5">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-ra-text-tertiary">
            验收标准
          </p>
          <ul className="mt-2 space-y-2 text-sm text-ra-text-secondary">
            {goal.acceptance_criteria.map((criterion) => (
              <li key={criterion} className="flex gap-2">
                <span aria-hidden="true">•</span>
                <span>{criterion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {error && (
        <p
          role="alert"
          data-testid="approval-error"
          className="mt-5 rounded-xl border border-red-400/20 bg-red-400/5 px-3 py-2 text-sm text-red-300"
        >
          {mutationMessage(error)}
        </p>
      )}

      <div className="mt-6 flex flex-wrap items-end gap-3">
        {canPlan && (
          <button
            type="button"
            data-testid="approval-plan-button"
            disabled={pending}
            onClick={onPlan}
            className="rounded-lg bg-ra-accent px-4 py-2 text-sm font-medium text-ra-base disabled:opacity-50"
          >
            生成计划
          </button>
        )}
        {canApprove && (
          <button
            type="button"
            data-testid="approval-approve-button"
            disabled={pending}
            onClick={onApprove}
            className="rounded-lg bg-ra-accent px-4 py-2 text-sm font-medium text-ra-base disabled:opacity-50"
          >
            批准当前计划
          </button>
        )}
        {canLaunch && (
          <>
            <label className="text-xs text-ra-text-tertiary">
              自治窗口
              <select
                aria-label="自治窗口时长"
                value={autonomyHours}
                onChange={(event) => setAutonomyHours(Number(event.target.value))}
                disabled={pending}
                className="ml-2 rounded-lg border border-ra-border bg-ra-base px-2 py-2 text-sm text-ra-text"
              >
                <option value={1}>1 小时</option>
                <option value={2}>2 小时</option>
                <option value={4}>4 小时</option>
              </select>
            </label>
            <button
              type="button"
              data-testid="approval-launch-button"
              disabled={pending}
              onClick={() => onLaunch(autonomyHours)}
              className="rounded-lg bg-ra-accent px-4 py-2 text-sm font-medium text-ra-base disabled:opacity-50"
            >
              启动运行
            </button>
          </>
        )}
        {!canPlan && !canApprove && !canLaunch && (
          <p className="text-sm text-ra-text-tertiary">
            当前状态只读；此页面不会对该 Goal 执行新的审批动作。
          </p>
        )}
      </div>
    </section>
  );
}

/**
 * Server-truth continuation surface for Inbox-promoted and other existing Goals.
 * The browser selects a Goal identity; lifecycle state stays owned by TaskStore.
 */
export function ApprovalsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const goalsQuery = useGoals();
  const planMutation = usePlanExistingGoal();
  const approveMutation = useApproveExistingGoal();
  const launchMutation = useLaunchExistingGoal();

  const pendingGoals = (goalsQuery.data ?? []).filter((goal) =>
    PENDING_STATUSES.has(goal.status),
  );
  const requestedGoalId = searchParams.get("goal") ?? "";
  const selectedGoalId = requestedGoalId || pendingGoals[0]?.id;
  const selectedGoalQuery = useGoal(selectedGoalId);
  const selectedGoal = selectedGoalQuery.data;
  const pending =
    planMutation.isPending || approveMutation.isPending || launchMutation.isPending;
  const error =
    planMutation.error ?? approveMutation.error ?? launchMutation.error ?? null;

  const resetMutations = () => {
    planMutation.reset();
    approveMutation.reset();
    launchMutation.reset();
  };

  const selectGoal = (goalId: string) => {
    resetMutations();
    setSearchParams({ goal: goalId });
  };

  return (
    <main
      data-testid="approvals-page"
      className={cn(
        "min-h-full bg-[var(--oh-surface)] px-4 py-7",
        "sm:px-8 lg:px-12 lg:py-10",
      )}
    >
      <div className="mx-auto w-full max-w-[1080px]">
        <header className="mb-8">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-ra-text-tertiary">
            Owner review
          </p>
          <h1 className="mt-2 flex items-center gap-2 text-3xl font-medium tracking-[-0.025em] text-ra-text sm:text-4xl">
            <ShieldCheck className="h-7 w-7" aria-hidden="true" />
            审批与继续
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-ra-text-secondary">
            这里直接读取 Goal 服务端真相。计划、批准和启动都是显式动作；刷新后会按同一个 Goal ID 恢复，而不是从浏览器状态猜测进度。
          </p>
        </header>

        {goalsQuery.isLoading && (
          <p className="text-sm text-ra-text-tertiary">正在读取待处理目标…</p>
        )}
        {goalsQuery.error && (
          <p role="alert" className="text-sm text-red-300">
            {mutationMessage(goalsQuery.error)}
          </p>
        )}

        {!goalsQuery.isLoading && !goalsQuery.error && (
          <div className="grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
            <aside className="rounded-2xl border border-ra-border bg-ra-light/20 p-3">
              <div className="flex items-center justify-between px-2 py-1">
                <h2 className="text-sm font-medium text-ra-text">待处理</h2>
                <span className="text-xs text-ra-text-tertiary">
                  {pendingGoals.length} 项
                </span>
              </div>
              <div className="mt-2 space-y-1" data-testid="approval-pending-list">
                {pendingGoals.map((goal) => (
                  <button
                    key={goal.id}
                    type="button"
                    onClick={() => selectGoal(goal.id)}
                    data-testid={`approval-goal-${goal.id}`}
                    className={cn(
                      "w-full rounded-xl px-3 py-3 text-left",
                      selectedGoalId === goal.id
                        ? "bg-ra-light text-ra-text"
                        : "text-ra-text-secondary hover:bg-ra-light/50",
                    )}
                  >
                    <span className="block truncate text-sm font-medium">{goal.title}</span>
                    <span className="mt-1 block text-xs text-ra-text-tertiary">
                      {STATUS_LABELS[goal.status]}
                    </span>
                  </button>
                ))}
                {pendingGoals.length === 0 && (
                  <p
                    data-testid="approval-empty"
                    className="px-3 py-8 text-center text-sm text-ra-text-tertiary"
                  >
                    无待处理审批。
                  </p>
                )}
              </div>
            </aside>

            <div className="min-w-0">
              {selectedGoalQuery.isLoading && selectedGoalId && (
                <p className="text-sm text-ra-text-tertiary">正在读取目标…</p>
              )}
              {selectedGoalQuery.error && (
                <p role="alert" className="text-sm text-red-300">
                  {mutationMessage(selectedGoalQuery.error)}
                </p>
              )}
              {selectedGoal && (
                <GoalDetail
                  goal={selectedGoal}
                  pending={pending}
                  error={error}
                  onPlan={() => {
                    resetMutations();
                    planMutation.mutate(selectedGoal);
                  }}
                  onApprove={() => {
                    resetMutations();
                    approveMutation.mutate(selectedGoal);
                  }}
                  onLaunch={(autonomyHours) => {
                    resetMutations();
                    launchMutation.mutate({
                      goal: selectedGoal,
                      autonomyHours,
                    });
                  }}
                />
              )}
              {!selectedGoal && !selectedGoalId && (
                <div className="rounded-2xl border border-dashed border-ra-border py-16 text-center text-sm text-ra-text-tertiary">
                  选择一个待处理 Goal 后可查看计划与继续操作。
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
