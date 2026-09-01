import { Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { GoalComposer } from "@/components/goal-composer";
import { GoalCurrentActivity } from "@/components/goal-current-activity";
import { GoalProgress } from "@/components/goal-progress";
import { useGoal, useGoals, usePlatformStatus, useStartGoal } from "@/hooks/use-platform";
import { useRuns } from "@/hooks/use-runs";
import type { PlatformGoal } from "@/lib/platform-client";
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

function goalStatusLabel(status: PlatformGoal["status"]) {
  if (status === "RUNNING") return "正在执行";
  if (status === "COMPLETED") return "已完成";
  if (status === "BLOCKED") return "需要处理阻塞";
  if (status === "INVALIDATED") return "已失效";
  if (status === "APPROVED" || status === "PLANNED") return "等待启动";
  if (status === "DRAFT") return "草稿";
  return status;
}

export function HomePage() {
  const statusQuery = usePlatformStatus();
  const goalsQuery = useGoals();
  const runsQuery = useRuns();
  const startGoal = useStartGoal();
  const goals = useMemo(() => goalsQuery.data ?? [], [goalsQuery.data]);
  const runs = useMemo(() => runsQuery.data ?? [], [runsQuery.data]);
  const [selectedId, setSelectedId] = useState<string | undefined>();

  useEffect(() => {
    if (!selectedId && goals[0]) setSelectedId(goals[0].id);
  }, [goals, selectedId]);

  const detailQuery = useGoal(selectedId);
  const detailGoal = detailQuery.data;
  const recent = useMemo(() => goals.slice(0, 3), [goals]);
  const platform = statusQuery.data;
  const activeWindow = platform?.autonomy.active_window;
  const coordinatorError = platform?.coordinator.last_error;

  function handleStarted(goal: PlatformGoal) {
    setSelectedId(goal.id);
  }

  return (
    <main
      data-testid="platform-home"
      className="min-h-full bg-ra-workspace px-4 py-7 sm:px-8 lg:px-12 lg:py-9"
    >
      <div className="mx-auto max-w-[1080px]">
        {detailGoal ? (
          <header
            data-testid="active-goal-header"
            className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
          >
            <div className="min-w-0">
              <p className="truncate text-xs text-ra-text-tertiary">
                {detailGoal.repository || "Workspace"}
              </p>
              <h1 className="mt-1.5 text-[28px] font-medium tracking-[-0.03em] text-ra-text sm:text-[32px]">
                {detailGoal.title}
              </h1>
              {detailGoal.objective ? (
                <p className="mt-2 max-w-3xl text-sm leading-5 text-ra-text-secondary">
                  {detailGoal.objective}
                </p>
              ) : null}
              <h2 className="sr-only">今天想完成什么？</h2>
            </div>

            <div className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-2 pt-1 text-xs">
              <span
                data-testid="goal-state-label"
                className={cn("font-medium", goalStatusTextClass(detailGoal.status))}
              >
                {goalStatusLabel(detailGoal.status)}
              </span>
              {activeWindow ? (
                <span
                  data-testid="autonomy-status"
                  className="inline-flex items-center gap-1.5 text-ra-text-tertiary"
                >
                  <Loader2
                    className={cn(
                      "h-3.5 w-3.5",
                      activeWindow.status === "ACTIVE" && "animate-spin",
                    )}
                    aria-hidden="true"
                  />
                  自治 {activeWindow.tasks_completed}/{activeWindow.max_tasks}
                </span>
              ) : null}
              {platform ? (
                <span
                  data-testid="coordinator-status"
                  className={cn(
                    platform.coordinator.enabled
                      ? "sr-only"
                      : "inline-flex items-center gap-1.5 text-ra-status-error",
                  )}
                >
                  {platform.coordinator.enabled ? "协调器在线" : "手动模式"}
                </span>
              ) : null}
            </div>
          </header>
        ) : (
          <header className="mb-6">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-ra-text-tertiary">
              Workspace
            </p>
            <h1 className="mt-2 text-3xl font-medium tracking-[-0.03em] text-ra-text sm:text-4xl">
              今天想完成什么？
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-ra-text-secondary">
              给出最终目标。平台会生成规格与任务，协调 Agent，保存检查点，并把结果留给你审查。
            </p>
            {platform ? (
              <span
                data-testid="coordinator-status"
                className={cn(
                  platform.coordinator.enabled
                    ? "sr-only"
                    : "mt-3 inline-flex items-center gap-1.5 text-xs text-ra-status-error",
                )}
              >
                {platform.coordinator.enabled ? "协调器在线" : "手动模式"}
              </span>
            ) : null}
          </header>
        )}

        {coordinatorError && (
          <div
            role="alert"
            className="mb-5 flex items-start gap-3 rounded-xl border border-ra-status-error/30 bg-ra-status-error/10 px-4 py-3 text-sm text-ra-status-error"
          >
            <span
              className="mt-1 h-2 w-2 shrink-0 rounded-full bg-ra-status-error"
              aria-hidden="true"
            />
            <span>协调器需要处理：{coordinatorError}</span>
          </div>
        )}

        <section data-testid="goal-composer-section" className="mb-7">
          <GoalComposer
            busy={startGoal.isPending}
            onSubmit={(input) => startGoal.mutate(input, { onSuccess: handleStarted })}
          />
          {startGoal.isError && (
            <p role="alert" className="mt-3 text-sm text-ra-status-error">
              {startGoal.error.message}
            </p>
          )}
        </section>

        <section
          data-testid="current-execution-section"
          aria-label="Current execution"
          className="mb-9"
        >
          {selectedId && detailQuery.isPending ? (
            <div
              role="status"
              aria-live="polite"
              className="border-t border-ra-border/60 py-12 text-center text-sm text-ra-text-tertiary"
            >
              正在加载所选目标的执行进度…
            </div>
          ) : selectedId && detailQuery.isError ? (
            <div className="border-t border-ra-border/60 py-10 text-center">
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
            <div data-testid="active-goal-stream" className="border-t border-ra-border/60">
              <GoalProgress goal={detailGoal} />
              <GoalCurrentActivity goal={detailGoal} runs={runs} />
            </div>
          ) : !selectedId ? (
            <div className="border-t border-ra-border/60 py-12 text-center text-sm text-ra-text-tertiary">
              第一个目标会在这里显示 Agent 的执行进度。
            </div>
          ) : (
            <div
              role="status"
              aria-live="polite"
              className="border-t border-ra-border/60 py-12 text-center text-sm text-ra-text-tertiary"
            >
              正在加载所选目标的执行进度…
            </div>
          )}
        </section>

        <section
          data-testid="recent-goals-section"
          aria-label="Recent goals"
          className="border-t border-ra-border/60 pt-6"
        >
          <div className="mb-1 flex items-center justify-between">
            <h2 className="text-xs font-medium text-ra-text-secondary">最近目标</h2>
            <span className="text-[11px] tabular-nums text-ra-text-tertiary">
              {Math.min(goals.length, 3)} / {goals.length}
            </span>
          </div>

          <div className="divide-y divide-ra-border/50">
            {recent.map((goal) => (
              <button
                type="button"
                key={goal.id}
                onClick={() => setSelectedId(goal.id)}
                className={cn(
                  "group w-full px-1 py-2.5 text-left transition",
                  "hover:bg-ra-light/30 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                  detailGoal?.id === goal.id && "bg-ra-light/45",
                )}
              >
                <div className="flex items-baseline gap-4">
                  <p className="min-w-0 flex-1 text-sm leading-5 text-ra-text">
                    <span className="line-clamp-1">{goal.title}</span>
                  </p>
                  <span
                    className={cn(
                      "shrink-0 text-[10px] font-medium tracking-[0.04em]",
                      goalStatusTextClass(goal.status),
                    )}
                  >
                    {goal.status}
                  </span>
                </div>
                <div className="mt-0.5 flex items-center gap-4 text-[11px] text-ra-text-tertiary">
                  <span className="min-w-0 flex-1 truncate">{goal.objective}</span>
                  <span className="shrink-0 tabular-nums">{relativeTime(goal.updated_at)}</span>
                </div>
              </button>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
