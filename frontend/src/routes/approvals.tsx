import { useCallback, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Link, useSearchParams } from "react-router";
import { GoalReviewEditor } from "@/components/goal-review-editor";
import { PageHeader, PageSurface } from "@/components/page-header";
import type { GoalConfigurationInput, GoalPlanInput } from "@/lib/goal-continuation-operation";
import {
  usePlanExistingGoal,
  useSaveGoalConfiguration,
  useSaveGoalPlan,
} from "@/hooks/use-goal-continuation";
import { useGoal, useGoals } from "@/hooks/use-platform";
import { StartCard } from "@/components/start-card";
import { cn } from "@/lib/cn";
import { PlanSteps } from "@/components/plan-steps";
import { goalTitle, issueRef, objectiveText } from "@/lib/goal-view";
import { bindingLabel, executionModeLabel } from "@/lib/goal-labels";
import type { GoalStatus, PlatformGoal } from "@/lib/platform-client";

const PENDING_STATUSES = new Set<GoalStatus>(["DRAFT", "PLANNED", "APPROVED"]);

/*
 * Empty-state navigation actions. Both keep a 24px minimum hit area so the
 * affordances stay reachable by touch (`#448` §12 / accessibility baseline).
 */
const APPROVAL_ACTION_CLASS = cn(
  "inline-flex min-h-9 items-center justify-center rounded-lg bg-ra-accent px-3.5 py-2 text-sm font-medium text-ra-base transition-colors hover:bg-ra-accent-hover",
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
);

const APPROVAL_SECONDARY_CLASS = cn(
  "inline-flex min-h-9 items-center justify-center rounded-lg border border-ra-border px-3.5 py-2 text-sm font-medium text-ra-text-secondary transition-colors hover:bg-ra-light",
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
);

const STATUS_LABELS: Record<GoalStatus, string> = {
  DRAFT: "草稿",
  PLANNED: "待审批",
  APPROVED: "已批准，待启动",
  RUNNING: "运行中",
  COMPLETED: "执行完成，待审查",
  BLOCKED: "已阻塞",
  INVALIDATED: "已失效",
  SUPERSEDED: "来源 Issue 已关闭",
};

function mutationMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return "目标操作未完成，请读取最新状态后重试。";
}

function GoalDetail({
  goal,
  onPlan,
  pending,
  error,
  onSaveConfiguration,
  onSavePlan,
}: {
  goal: PlatformGoal;
  onPlan: () => void;
  pending: boolean;
  error: unknown;
  onSaveConfiguration: (goal: PlatformGoal, input: GoalConfigurationInput) => Promise<unknown>;
  onSavePlan: (goal: PlatformGoal, input: GoalPlanInput) => Promise<unknown>;
}) {
  const [editing, setEditing] = useState(false);
  const [configurationReady, setConfigurationReady] = useState(goal.executor_kind === "deterministic_fixture");
  const [configurationIssue, setConfigurationIssue] = useState("");
  const onConfigurationReady = useCallback((ready: boolean, issue?: string) => {
    setConfigurationReady(ready);
    setConfigurationIssue(issue ?? "");
  }, []);
  const canPlan = goal.status === "DRAFT";
  const cardStart = goal.status === "PLANNED";
  const issue = issueRef(goal);
  const legacyApproved = goal.status === "APPROVED";

  return (
    <section
      data-testid="approval-goal-detail"
      className="min-w-0 rounded-2xl border border-ra-border bg-ra-base p-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium text-ra-text-tertiary">
            {issue ? (
              <a href={issue.url} target="_blank" rel="noreferrer" className="hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
                目标 · 来自 Issue #{issue.number}
              </a>
            ) : "目标"}
          </p>
          <h2 className="mt-1 text-xl font-semibold text-ra-text" title={goal.title}>{goalTitle(goal, 160)}</h2>
          <details className="group mt-2">
            <summary className="cursor-pointer list-none focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent [&::-webkit-details-marker]:hidden">
              <p className="ra-measure line-clamp-6 whitespace-pre-line text-sm leading-6 text-ra-text-secondary group-open:line-clamp-none">
                {objectiveText(goal) || goal.objective}
              </p>
              <span className="mt-1 inline-block text-xs text-ra-text-tertiary group-open:hidden">展开全文</span>
            </summary>
          </details>
        </div>
        <span className="rounded-full bg-ra-light px-2.5 py-1 text-xs text-ra-text-secondary">
          {STATUS_LABELS[goal.status]}
        </span>
      </div>

      <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs text-ra-text-tertiary">仓库</dt>
          <dd className="mt-1 break-all text-ra-text-secondary">{goal.repository}</dd>
        </div>
        <div>
          <dt className="text-xs text-ra-text-tertiary">修订</dt>
          <dd className="mt-1 text-ra-text-secondary">{goal.revision}</dd>
        </div>
        <div>
          <dt className="text-xs text-ra-text-tertiary">执行模式</dt>
          <dd className="mt-1 text-ra-text-secondary" title={`${goal.executor_kind} · ${goal.orchestration_mode}`}>{executionModeLabel(goal)}</dd>
        </div>
        <div>
          <dt className="text-xs text-ra-text-tertiary">模型绑定</dt>
          <dd className="mt-1 break-all text-ra-text-secondary" title={goal.binding_ref || undefined}>
            {bindingLabel(goal)}
          </dd>
        </div>
      </dl>

      <GoalReviewEditor goal={goal} busy={pending} onEditingChange={setEditing}
        onConfigurationReady={onConfigurationReady} onSaveConfiguration={onSaveConfiguration} onSavePlan={onSavePlan} />
      {!configurationReady && canPlan && <p className="mt-3 text-sm text-ra-text-secondary">
        {configurationIssue || "当前执行配置尚不可用，请编辑目标配置并核对仓库和模型绑定。"}
      </p>}

      {goal.status !== "DRAFT" && (
        <div className="mt-6">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-ra-text-tertiary">
            当前计划
          </p>
          <PlanSteps goal={goal} />
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

      {error !== null && (
        <p
          role="alert"
          data-testid="approval-error"
          className="mt-5 rounded-xl border border-ra-status-error/20 bg-ra-status-error/5 px-3 py-2 text-sm text-ra-status-error"
        >
          {mutationMessage(error)}
        </p>
      )}

      {cardStart && !editing ? <StartCard goal={goal} /> : null}

      <div className="mt-6 flex flex-wrap items-end gap-3">
        {canPlan && (
          <button
            type="button"
            data-testid="approval-plan-button"
            disabled={pending || editing || !configurationReady}
            onClick={onPlan}
            className="rounded-lg bg-ra-accent px-4 py-2 text-sm font-medium text-ra-base disabled:opacity-50"
          >
            生成计划
          </button>
        )}
        {legacyApproved && (
          <p data-testid="approval-legacy-approved" className="text-sm text-ra-text-secondary">
            这个目标是按旧流程批准的，执行窗口只接受「计划已生成、尚未批准」的目标。
            编辑目标配置并保存后会回到草稿，重新生成计划就能在这里开始执行。
          </p>
        )}
        {!canPlan && !cardStart && !legacyApproved && (
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
  const configurationMutation = useSaveGoalConfiguration();
  const editPlanMutation = useSaveGoalPlan();

  const pendingGoals = (goalsQuery.data ?? []).filter((goal) =>
    PENDING_STATUSES.has(goal.status),
  );
  const requestedGoalId = searchParams.get("goal") ?? "";
  const selectedGoalId = requestedGoalId || pendingGoals[0]?.id;
  const selectedGoalQuery = useGoal(selectedGoalId);
  const selectedGoal = selectedGoalQuery.data;
  /*
   * `#448` §10 — the queue and the detail pane are two different states, and
   * only the combination of "no pending Goal" *and* "no Goal selected" is the
   * genuinely empty one. A deep link (`?goal=…`) to a Goal that already left
   * the queue still owns a right-hand pane with live server state.
   */
  const hasPendingGoals = pendingGoals.length > 0;
  const hasNothingToShow = !hasPendingGoals && !selectedGoalId;
  const pending = planMutation.isPending || configurationMutation.isPending || editPlanMutation.isPending;
  const error =
    planMutation.error ?? configurationMutation.error ?? editPlanMutation.error ?? null;

  const resetMutations = () => {
    planMutation.reset();
    configurationMutation.reset();
    editPlanMutation.reset();
  };

  const selectGoal = (goalId: string) => {
    resetMutations();
    setSearchParams({ goal: goalId });
  };

  return (
    <PageSurface data-testid="approvals-page" measureClassName="max-w-[1080px]">
      <PageHeader
        title="审批与继续"
        icon={ShieldCheck}
        description="在这里核对目标计划，然后确认并启动无人值守窗口。"
      />

        {goalsQuery.isLoading && (
          <p className="text-sm text-ra-text-tertiary">正在读取待处理目标…</p>
        )}
        {goalsQuery.error && (
          <p role="alert" className="text-sm text-ra-status-error">
            {mutationMessage(goalsQuery.error)}
          </p>
        )}

        {!goalsQuery.isLoading && (goalsQuery.data !== undefined || !goalsQuery.error)
          && (hasNothingToShow ? (
            /*
             * One empty state, not two.
             *
             * The previous layout kept the two-pane grid for an empty queue, so
             * a first-time visitor saw a narrow "0 项" card *and* a large
             * dashed panel instructing them to "选择一个待处理 Goal" — an
             * instruction for an action that was impossible, because there was
             * nothing to select (`#448` §10: normal state stays quiet and must
             * not be dressed up as an exception).
             *
             * The collapse is gated on "nothing pending AND nothing selected":
             * a deep link to a Goal that has already left the queue must keep
             * rendering that Goal's real state (`#448` §9 forbids hiding live
             * server truth), so only the truly empty case is replaced.
             */
            <div
              data-testid="approval-empty"
              className="rounded-2xl border border-dashed border-ra-border px-6 py-12 text-center"
            >
              <ShieldCheck className="mx-auto h-6 w-6 text-ra-text-tertiary" aria-hidden="true" />
              <p className="mt-3 text-sm font-medium text-ra-text">当前没有待处理的目标</p>
              <p className="mx-auto mt-1.5 max-w-md text-sm leading-6 text-ra-text-secondary">
                待生成计划、待确认或需要重新规划的目标会出现在这里。
              </p>
              <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                <Link to="/goals" className={APPROVAL_ACTION_CLASS}>查看所有目标</Link>
                <Link to="/inbox" className={APPROVAL_SECONDARY_CLASS}>打开想法收件箱</Link>
              </div>
            </div>
          ) : (
          <div
            className={cn(
              "grid gap-5",
              hasPendingGoals && "lg:grid-cols-[280px_minmax(0,1fr)]",
            )}
          >
            {hasPendingGoals && (
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
                    <span className="block truncate text-sm font-medium" title={goal.title}>{goalTitle(goal)}</span>
                    <span className="mt-1 block text-xs text-ra-text-tertiary">
                      {STATUS_LABELS[goal.status]}
                    </span>
                  </button>
                ))}
              </div>
            </aside>
            )}

            <div className="min-w-0">
              {!hasPendingGoals && selectedGoalId && (
                <p className="mb-3 text-sm text-ra-text-tertiary">
                  该目标当前不在待处理队列中，下面显示它的最新状态（只读）。
                </p>
              )}
              {selectedGoalQuery.isLoading && selectedGoalId && (
                <p className="text-sm text-ra-text-tertiary">正在读取目标…</p>
              )}
              {selectedGoalQuery.error && (
                <p role="alert" className="text-sm text-ra-status-error">
                  {mutationMessage(selectedGoalQuery.error)}
                </p>
              )}
              {selectedGoal && (
                <GoalDetail
                  key={selectedGoal.id}
                  goal={selectedGoal}
                  pending={pending}
                  error={error}
                  onSaveConfiguration={(goal, input) => {
                    resetMutations();
                    return configurationMutation.mutateAsync({ goal, input });
                  }}
                  onSavePlan={(goal, input) => {
                    resetMutations();
                    return editPlanMutation.mutateAsync({ goal, input });
                  }}
                  onPlan={() => {
                    resetMutations();
                    planMutation.mutate(selectedGoal);
                  }}
                />
              )}
              {!selectedGoal && selectedGoalId && !selectedGoalQuery.isLoading && !selectedGoalQuery.error && (
                <div className="rounded-2xl border border-dashed border-ra-border py-16 text-center text-sm text-ra-text-tertiary">
                  无法显示该目标：服务没有返回它的内容。
                </div>
              )}
            </div>
          </div>
          ))}
    </PageSurface>
  );
}
