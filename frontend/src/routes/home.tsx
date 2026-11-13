import { ArrowLeft, ExternalLink } from "lucide-react";
import { useMemo } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router";
import { NerelanMark } from "@/components/brand-logo";
import { GoalComposer } from "@/components/goal-composer";
import { GoalThread } from "@/components/goal-thread";
import { runtimeMessage } from "@/lib/runtime-labels";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { UnattendedStatus } from "@/components/unattended-status";
import { useGoal, useGoalTimeline, useGoals, usePlatformStatus, useCreateGoalDraft } from "@/hooks/use-platform";
import { cn } from "@/lib/cn";
import { recentGoals } from "@/components/sidebar";
import { GOAL_TONE_DOT, GOAL_TONE_TEXT, goalState, goalTitle, issueRef } from "@/lib/goal-view";

function relativeTime(value: string) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return "刚刚";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  return `${Math.floor(seconds / 86400)} 天前`;
}

function ReadFeedback({ query, label }: {
  query: { data: unknown; isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown };
  label: string;
}) {
  if (query.isPending) return <LoadingState label={`正在加载${label}…`} />;
  if (!query.isError) return null;
  return <ErrorState
    title={query.data === undefined ? `${label}加载失败` : `${label}更新失败，显示上次内容`}
    error={query.error}
    onRetry={() => void query.refetch()}
  />;
}

const RECENT_GOAL_LIMIT = 5;

/** "执行窗口：剩 23 小时 · 已开始 1/30 个任务". */
function windowLine(window: { expires_at: string; tasks_started?: number; tasks_completed: number; max_tasks: number }): string {
  const hours = Math.max(0, Math.round((new Date(window.expires_at).getTime() - Date.now()) / 3_600_000));
  const left = hours >= 1 ? `剩 ${hours} 小时` : "即将到期";
  const started = window.tasks_started ?? window.tasks_completed;
  return `执行窗口：${left} · 已开始 ${Math.min(started, window.max_tasks)}/${window.max_tasks} 个任务`;
}

/** "task_unsuccessful:task-…" reads as a sentence; the raw code stays in the tooltip. */
function coordinatorNotice(code: string): string {
  const message = runtimeMessage(code);
  return message.nextStep ? `${message.label}：${message.nextStep}` : `调度需要处理：${code}`;
}

export function HomePage() {
  const statusQuery = usePlatformStatus();
  const goalsQuery = useGoals();
  const startGoal = useCreateGoalDraft();
  const navigate = useNavigate();
  const location = useLocation();
  const newGoalRequest = (location.state as { newGoal?: number } | null)?.newGoal;
  const goals = useMemo(() => goalsQuery.data ?? [], [goalsQuery.data]);
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedId = searchParams.get("goal") || undefined;
  const setSelectedId = (goalId: string) => setSearchParams((previous) => {
    const next = new URLSearchParams(previous);
    next.set("goal", goalId);
    return next;
  });

  const detailQuery = useGoal(selectedId);
  const timelineQuery = useGoalTimeline(selectedId);
  const detailGoal = detailQuery.data;
  const detailState = detailGoal ? goalState(detailGoal) : null;
  const detailIssue = detailGoal ? issueRef(detailGoal) : null;
  const recent = useMemo(() => recentGoals(goals, RECENT_GOAL_LIMIT), [goals]);
  const platform = statusQuery.data;
  const activeWindow = platform?.autonomy.active_window;
  const coordinatorError = platform?.coordinator.last_error;

  const coordinatorStatus = platform ? (
    <span
      data-testid="coordinator-status"
      className={cn(
        platform.coordinator.enabled && !statusQuery.isError
          ? "sr-only"
          : cn("inline-flex items-center gap-1.5 text-xs", statusQuery.isError ? "text-ra-status-error" : "text-ra-text-secondary"),
      )}
    >
      {statusQuery.isError ? "平台状态待刷新" : platform.coordinator.enabled ? "协调器在线" : "协调器未运行"}
    </span>
  ) : null;

  const notices = (
    <>
      <ReadFeedback query={statusQuery} label="平台状态" />
      {coordinatorError && (
        <div
          role="alert"
          className="mb-4 flex items-start gap-3 rounded-lg border border-ra-status-error/30 bg-ra-status-error/10 px-3.5 py-2.5 text-sm text-ra-status-error"
        >
          <span
            className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-ra-status-error"
            aria-hidden="true"
          />
          <span title={coordinatorError}>{coordinatorNotice(coordinatorError)}</span>
        </div>
      )}
    </>
  );

  const composer = (dock: boolean) => (
    <section data-testid="goal-composer-section">
      <GoalComposer
        busy={startGoal.isPending}
        compact={dock}
        focusKey={dock ? undefined : newGoalRequest}
        placeholder={dock ? "另起一个新目标…" : undefined}
        onSubmit={async (input) => {
          const goal = await startGoal.mutateAsync(input);
          setSelectedId(goal.id);
          navigate(`/approvals?goal=${encodeURIComponent(goal.id)}`);
        }}
      />
      {startGoal.isError && (
        <p role="alert" className="mt-2 text-sm text-ra-status-error">
          {startGoal.error.message}
        </p>
      )}
    </section>
  );

  if (!selectedId) {
    return (
      <main
        data-testid="platform-home"
        className="flex min-h-full flex-col bg-ra-workspace"
      >
        {platform && <UnattendedStatus status={platform} />}
        <div className="mx-auto my-auto w-full max-w-[784px] px-4 py-10 sm:px-8">
          <header className="mb-5 text-center">
            <NerelanMark className="mx-auto mb-4 h-8 w-8 text-ra-text-tertiary" />
            <h1 className="text-2xl font-medium tracking-[-0.02em] text-ra-text">
              今天想完成什么？
            </h1>
            <p className="mt-2 text-sm text-ra-text-secondary">
              给出最终目标。平台会生成规格与任务，协调 Agent，保存检查点，并把结果留给你审查。
            </p>
            {coordinatorStatus}
          </header>

          {notices}
          {composer(false)}

          <section
            data-testid="recent-goals-section"
            aria-label="最近目标"
            className="mt-8"
          >
            <div className="mb-1.5 flex items-center justify-between gap-3 px-2.5">
              <h2 className="text-xs font-medium text-ra-text-tertiary">最近目标</h2>
              <Link to="/goals" className="inline-flex min-h-6 items-center rounded px-1 text-xs text-ra-text-tertiary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">所有目标</Link>
            </div>

            <ReadFeedback query={goalsQuery} label="目标列表" />
            {goalsQuery.isSuccess && recent.length === 0 && (
              <p className="px-2.5 py-3 text-sm text-ra-text-tertiary">还没有目标。</p>
            )}
            <div className="flex flex-col gap-0.5">
              {recent.map((goal) => {
                const state = goalState(goal);
                return (
                <button
                  type="button"
                  key={goal.id}
                  data-testid={`recent-goal-${goal.id}`}
                  onClick={() => setSelectedId(goal.id)}
                  className="flex min-h-9 w-full items-center gap-3 rounded-md px-2.5 py-1.5 text-left transition-colors hover:bg-ra-tertiary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
                >
                  <span aria-hidden="true" className={cn("h-2 w-2 shrink-0 rounded-full", GOAL_TONE_DOT[state.tone])} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm text-ra-text" title={goalTitle(goal, 300)}>
                      {goalTitle(goal)}
                    </span>
                    <span data-testid={`goal-progress-line-${goal.id}`} className={cn("block truncate text-xs", GOAL_TONE_TEXT[state.tone])}>
                      {state.label}{state.detail ? `：${state.detail}` : ""}
                    </span>
                  </span>
                  <span className="w-16 shrink-0 text-right text-xs tabular-nums text-ra-text-tertiary">
                    {relativeTime(goal.updated_at)}
                  </span>
                </button>
                );
              })}
            </div>
          </section>
        </div>
      </main>
    );
  }

  return (
    <main
      data-testid="platform-home"
      className="flex h-full min-h-0 flex-col bg-ra-workspace"
    >
      {platform && <UnattendedStatus status={platform} />}
      <header
        data-testid="active-goal-header"
        className="flex shrink-0 items-center gap-3 border-b border-ra-border px-4 py-2.5 sm:px-5"
      >
        <Link
          to="/"
          aria-label="返回新目标"
          data-testid="goal-thread-back"
          className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-ra-text-tertiary hover:bg-ra-tertiary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        </Link>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-[15px] font-semibold leading-6 text-ra-text" title={detailGoal ? goalTitle(detailGoal, 300) : undefined}>
            {detailGoal ? goalTitle(detailGoal, 120) : "目标"}
          </h1>
          {detailGoal ? (
            <p className="flex min-w-0 items-center gap-2 truncate text-xs text-ra-text-tertiary">
              {detailIssue ? (
                <a href={detailIssue.url} target="_blank" rel="noreferrer" data-testid="goal-issue-link"
                  className="inline-flex items-center gap-0.5 hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
                  Issue #{detailIssue.number}<ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              ) : null}
              <span className="truncate">{detailGoal.repository}</span>
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-wrap items-center justify-end gap-x-3 gap-y-1 text-xs">
          {detailState ? (
            <span
              data-testid="goal-state-label"
              className={cn("inline-flex items-center gap-1.5 rounded-full bg-ra-light px-2.5 py-1 font-medium", GOAL_TONE_TEXT[detailState.tone])}
            >
              <span aria-hidden="true" className={cn("h-1.5 w-1.5 rounded-full", GOAL_TONE_DOT[detailState.tone])} />
              {detailState.label}
            </span>
          ) : null}
          {activeWindow && detailGoal?.window_id === activeWindow.id ? (
            <span
              data-testid="autonomy-status"
              className="text-ra-text-tertiary"
              title="这个目标所在的执行窗口：窗口到期、任务数或 Token 用完就会停下"
            >
              {windowLine(activeWindow)}
            </span>
          ) : null}
          {coordinatorStatus}
        </div>
      </header>

      {detailGoal ? (
        // The goal as an agent conversation: thread, docked composer and side panel.
        <section data-testid="current-execution-section" aria-label="当前执行" className="flex min-h-0 flex-1 flex-col">
          <div data-testid="active-goal-stream" className="flex min-h-0 flex-1 flex-col">
            <div className="mx-auto w-full max-w-[760px] px-4 sm:px-6 empty:hidden">
              {notices}
              <ReadFeedback query={detailQuery} label="目标详情" />
              <ReadFeedback query={timelineQuery} label="执行过程" />
            </div>
            <GoalThread goal={detailGoal} timeline={timelineQuery.data} composer={composer(true)} />
          </div>
        </section>
      ) : (
        <div className="min-h-0 flex-1 overflow-y-auto custom-scrollbar">
          <div className="mx-auto w-full max-w-[760px] px-4 py-5 sm:px-6">
            {notices}
            <section data-testid="current-execution-section" aria-label="当前执行">
              {detailQuery.isError ? (
                <div className="py-10 text-center">
                  <p role="alert" className="text-sm text-ra-status-error">
                    当前所选目标的执行进度暂时无法加载，请重试。
                  </p>
                  <button
                    type="button"
                    onClick={() => void detailQuery.refetch()}
                    disabled={detailQuery.isFetching}
                    className="mt-4 rounded-lg border border-ra-border px-3 py-2 text-xs text-ra-text-secondary transition hover:bg-ra-light/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent disabled:cursor-wait disabled:opacity-60"
                  >
                    {detailQuery.isFetching ? "正在重试…" : "重试加载当前目标"}
                  </button>
                </div>
              ) : (
                <div role="status" aria-live="polite" className="py-12 text-center text-sm text-ra-text-tertiary">
                  正在加载所选目标的执行进度…
                </div>
              )}
            </section>
          </div>
        </div>
      )}
    </main>
  );
}
