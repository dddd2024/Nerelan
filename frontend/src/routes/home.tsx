import { ArrowLeft, ChevronRight, Loader2 } from "lucide-react";
import { useMemo } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { NerelanMark } from "@/components/brand-logo";
import { GoalComposer } from "@/components/goal-composer";
import { ReadinessChecklist } from "@/components/readiness-checklist";
import { GoalCurrentActivity } from "@/components/goal-current-activity";
import { GoalProgress } from "@/components/goal-progress";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { useGoal, useGoals, usePlatformStatus, useCreateGoalDraft } from "@/hooks/use-platform";
import { useRuns } from "@/hooks/use-runs";
import { goalStatusLabel } from "@/lib/goal-status-label";
import { displayTitle } from "@/lib/display-title";
import { cn } from "@/lib/cn";

function relativeTime(value: string) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return "刚刚";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  return `${Math.floor(seconds / 86400)} 天前`;
}

function goalStatusTextClass(status: string) {
  if (status === "COMPLETED") return "text-ra-status-running";
  if (status === "BLOCKED" || status === "INVALIDATED") return "text-ra-status-error";
  if (status === "RUNNING") return "text-ra-accent";
  return "text-ra-text-tertiary";
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

/** Objectives are long machine-written paragraphs: keep them to a summary. */
const OBJECTIVE_CLAMP_THRESHOLD = 140;

/**
 * Goal objective on the workspace header.
 *
 * The objective is context for the goal, not the page subject, so a long one
 * is clamped to two lines with an explicit expansion. Short objectives render
 * as ordinary prose with no affordance to learn.
 */
function ObjectiveDisclosure({ objective }: { objective: string }) {
  if (objective.length <= OBJECTIVE_CLAMP_THRESHOLD) {
    return (
      <p className="ra-measure text-sm leading-5 text-ra-text">
        {objective}
      </p>
    );
  }
  return (
    <details className="group" data-testid="goal-objective-disclosure">
      <summary
        className={cn(
          "cursor-pointer list-none",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
          "[&::-webkit-details-marker]:hidden",
        )}
      >
        <p className="ra-measure line-clamp-2 text-sm leading-5 text-ra-text group-open:line-clamp-none">
          {objective}
        </p>
        <span className="mt-1 inline-flex items-center gap-1 text-xs text-ra-text-tertiary">
          <ChevronRight
            className="h-3 w-3 transition-transform group-open:rotate-90"
            aria-hidden="true"
          />
          展开目标全文
        </span>
      </summary>
    </details>
  );
}

export function HomePage() {
  const statusQuery = usePlatformStatus();
  const goalsQuery = useGoals();
  const runsQuery = useRuns();
  const startGoal = useCreateGoalDraft();
  const navigate = useNavigate();
  const goals = useMemo(() => goalsQuery.data ?? [], [goalsQuery.data]);
  const runs = useMemo(() => runsQuery.data ?? [], [runsQuery.data]);
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedId = searchParams.get("goal") || undefined;
  const setSelectedId = (goalId: string) => setSearchParams((previous) => {
    const next = new URLSearchParams(previous);
    next.set("goal", goalId);
    return next;
  });

  const detailQuery = useGoal(selectedId);
  const detailGoal = detailQuery.data;
  const recent = useMemo(() => goals.slice(0, RECENT_GOAL_LIMIT), [goals]);
  const platform = statusQuery.data;
  const activeWindow = platform?.autonomy.active_window;
  const coordinatorError = platform?.coordinator.last_error;

  const coordinatorStatus = platform ? (
    <span
      data-testid="coordinator-status"
      className={cn(
        platform.coordinator.enabled && !statusQuery.isError
          ? "sr-only"
          : "inline-flex items-center gap-1.5 text-xs text-ra-status-error",
      )}
    >
      {statusQuery.isError ? "平台状态待刷新" : platform.coordinator.enabled ? "协调器在线" : "手动模式"}
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
          <span>协调器需要处理：{coordinatorError}</span>
        </div>
      )}
    </>
  );

  const composer = (dock: boolean) => (
    <section data-testid="goal-composer-section">
      <ReadinessChecklist />
      <GoalComposer
        busy={startGoal.isPending}
        compact={dock}
        placeholder={dock ? "下达一个新目标…" : undefined}
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
        className="flex min-h-full flex-col justify-center bg-ra-workspace px-4 py-10 sm:px-8"
      >
        <div className="mx-auto w-full max-w-[720px]">
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
              {recent.map((goal) => (
                <button
                  type="button"
                  key={goal.id}
                  onClick={() => setSelectedId(goal.id)}
                  title={goal.objective}
                  className="flex min-h-9 w-full items-center gap-3 rounded-md px-2.5 py-1.5 text-left transition-colors hover:bg-ra-tertiary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
                >
                  <span className="min-w-0 flex-1 truncate text-sm text-ra-text" title={displayTitle(goal.title, 160)}>
                    {displayTitle(goal.title)}
                  </span>
                  {/* A terminal COMPLETED row states the product meaning
                      ("execution finished, review still pending"), because a
                      bare `COMPLETED` reads as delivery. Non-terminal states
                      keep their machine name: it is the honest value while the
                      run is in flight, and the tone carries the urgency. */}
                  <span className={cn("shrink-0 text-[11px] font-medium", goalStatusTextClass(goal.status))}>
                    {goal.status === "COMPLETED" ? goalStatusLabel(goal.status) : goal.status}
                  </span>
                  <span className="w-16 shrink-0 text-right text-[11px] tabular-nums text-ra-text-tertiary">
                    {relativeTime(goal.updated_at)}
                  </span>
                </button>
              ))}
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
          <h1 className="truncate text-[15px] font-semibold leading-6 text-ra-text">
            {detailGoal ? displayTitle(detailGoal.title, 120) : "目标"}
          </h1>
          {detailGoal ? (
            <p className="truncate text-[11px] text-ra-text-tertiary">
              {detailGoal.repository || "Workspace"}
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-wrap items-center justify-end gap-x-3 gap-y-1 text-xs">
          {detailGoal ? (
            <span
              data-testid="goal-state-label"
              className={cn("font-medium", goalStatusTextClass(detailGoal.status))}
            >
              {goalStatusLabel(detailGoal.status)}
            </span>
          ) : null}
          {activeWindow ? (
            <span
              data-testid="autonomy-status"
              className="inline-flex items-center gap-1.5 text-ra-text-tertiary"
              title={`自治窗口已完成 ${activeWindow.tasks_completed} 项任务，本窗口上限 ${activeWindow.max_tasks} 项`}
            >
              <Loader2
                className={cn(
                  "h-3.5 w-3.5",
                  activeWindow.status === "ACTIVE" && "animate-spin",
                )}
                aria-hidden="true"
              />
              {/* The absolute count is cumulative but `max_tasks` is the
                  per-window budget, so a raw "8/1" ratio asserts an impossible
                  "8 of 1" once the window has been exceeded. Below the budget
                  the ratio is denser; above it the ratio is dropped. */}
              {activeWindow.tasks_completed <= activeWindow.max_tasks
                ? `自治 ${activeWindow.tasks_completed}/${activeWindow.max_tasks}`
                : `自治已完成 ${activeWindow.tasks_completed}`}
            </span>
          ) : null}
          {coordinatorStatus}
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto custom-scrollbar">
        <div className="mx-auto w-full max-w-[820px] px-4 py-5 sm:px-6">
          {notices}

          {detailGoal?.objective ? (
            <div className="mb-5 flex justify-end">
              <div
                data-testid="goal-thread-objective"
                className="max-w-[85%] rounded-2xl rounded-br-md bg-ra-tertiary px-3.5 py-2.5"
              >
                <ObjectiveDisclosure objective={detailGoal.objective} />
              </div>
            </div>
          ) : null}

          <section data-testid="current-execution-section" aria-label="当前执行">
            {detailQuery.isPending ? (
              <div
                role="status"
                aria-live="polite"
                className="py-12 text-center text-sm text-ra-text-tertiary"
              >
                正在加载所选目标的执行进度…
              </div>
            ) : detailQuery.isError && !detailGoal ? (
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
            ) : detailGoal ? (
              <div data-testid="active-goal-stream" className="space-y-5">
                <ReadFeedback query={detailQuery} label="目标详情" />
                <GoalProgress goal={detailGoal} />
                <ReadFeedback query={runsQuery} label="运行活动" />
                {runsQuery.data !== undefined && <GoalCurrentActivity goal={detailGoal} runs={runs} />}
              </div>
            ) : null}
          </section>
        </div>
      </div>

      <div className="shrink-0 px-4 pb-3 pt-1 sm:px-6">
        <div className="mx-auto w-full max-w-[820px]">{composer(true)}</div>
      </div>
    </main>
  );
}
