import { Loader2, PlayCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { GoalComposer } from "@/components/goal-composer";
import { GoalProgress } from "@/components/goal-progress";
import { useGoal, useGoals, usePlatformStatus, useStartGoal } from "@/hooks/use-platform";
import type { PlatformGoal } from "@/lib/platform-client";
import { cn } from "@/lib/cn";

function relativeTime(value: string) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return "刚刚";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  return `${Math.floor(seconds / 86400)} 天前`;
}

const ACTIVE_STATUSES = new Set(["RUNNING"]);

export function HomePage() {
  const statusQuery = usePlatformStatus();
  const goalsQuery = useGoals();
  const startGoal = useStartGoal();
  const goals = useMemo(() => goalsQuery.data ?? [], [goalsQuery.data]);
  const [selectedId, setSelectedId] = useState<string | undefined>();

  useEffect(() => {
    if (!selectedId && goals[0]) setSelectedId(goals[0].id);
  }, [goals, selectedId]);

  const detailQuery = useGoal(selectedId);
  const detailGoal = detailQuery.data;
  const recent = useMemo(() => goals.slice(0, 3), [goals]);
  const platform = statusQuery.data;
  const activeWindow = platform?.autonomy.active_window;

  function handleStarted(goal: PlatformGoal) {
    setSelectedId(goal.id);
  }

  return (
    <main data-testid="platform-home" className="min-h-full bg-[var(--oh-surface)] px-4 py-7 sm:px-8 lg:px-12 lg:py-10">
      <div className="mx-auto max-w-[1400px]">
        {/* 现代化仪表板头部 */}
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-ra-text-tertiary">
              Agent 控制中心
            </p>
            <h1 className="mt-2 text-3xl font-medium tracking-[-0.025em] text-ra-text sm:text-4xl">
              今天想完成什么？
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-ra-text-secondary">
              给出最终目标。平台会生成规格与任务，协调 Agent，保存检查点，并把结果留给你审查。
            </p>
          </div>
          <div className="flex items-center gap-3">
            {activeWindow && (
              <span className="flex items-center gap-2 rounded-full border border-ra-border bg-ra-light/70 px-3 py-1.5 text-xs text-ra-text-secondary">
                <Loader2 className={cn("h-3 w-3", activeWindow.status === "ACTIVE" && "animate-spin")} />
                {activeWindow.tasks_completed}/{activeWindow.max_tasks}
              </span>
            )}
            <span className="flex items-center gap-2 rounded-full border border-ra-border bg-ra-light/70 px-3 py-1.5 text-xs text-ra-text-secondary">
              <span className={cn("h-2 w-2 rounded-full", platform?.coordinator.enabled ? "bg-emerald-400" : "bg-amber-300")} />
              {platform?.coordinator.enabled ? "协调器在线" : "手动模式"}
            </span>
            <span className="flex items-center gap-2 rounded-full border border-ra-border bg-ra-light/70 px-3 py-1.5 text-xs text-ra-text-secondary">
              <PlayCircle className="h-3 w-3" />
              {platform?.capability_count ?? "—"} 能力
            </span>
          </div>
        </header>

        {/* 快速状态概览 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="rounded-xl border border-ra-border bg-ra-light p-4 hover:border-ra-accent/50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-400/10 text-blue-400">
                <PlayCircle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-ra-text">
                  {goals.filter(g => g.status === "RUNNING").length}
                </h3>
                <p className="text-sm text-ra-text-secondary">运行中</p>
              </div>
            </div>
          </div>
          <div className="rounded-xl border border-ra-border bg-ra-light p-4 hover:border-ra-accent/50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-400/10 text-emerald-400">
                <PlayCircle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-ra-text">
                  {goals.filter(g => g.status === "COMPLETED").length}
                </h3>
                <p className="text-sm text-ra-text-secondary">已完成</p>
              </div>
            </div>
          </div>
          <div className="rounded-xl border border-ra-border bg-ra-light p-4 hover:border-ra-accent/50 transition-colors">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-400/10 text-purple-400">
                <PlayCircle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-ra-text">{goals.length}</h3>
                <p className="text-sm text-ra-text-secondary">总目标数</p>
              </div>
            </div>
          </div>
        </div>

        {/* 目标创建区域 */}
        <section data-testid="goal-composer-section" className="mb-10">
          <div className="rounded-xl border border-ra-border bg-ra-light p-6">
            <h2 className="text-lg font-medium text-ra-text mb-4">创建新目标</h2>
            <GoalComposer
              busy={startGoal.isPending}
              onSubmit={(input) => startGoal.mutate(input, { onSuccess: handleStarted })}
            />
            {startGoal.isError && (
              <p role="alert" className="mt-3 text-sm text-red-300">{startGoal.error.message}</p>
            )}
          </div>
        </section>

        {/* 当前执行进度 */}
        <section data-testid="current-execution-section" aria-label="Current execution" className="mb-10">
          {detailGoal ? (
            <div className="rounded-xl border border-ra-border bg-ra-light p-6">
              <h2 className="text-lg font-medium text-ra-text mb-4">当前执行</h2>
              <GoalProgress goal={detailGoal} />
            </div>
          ) : (
            <div className="rounded-xl border border-ra-border bg-ra-light p-6 text-center">
              <div className="py-8">
                <PlayCircle className="h-12 w-12 text-ra-text-tertiary mx-auto mb-4" />
                <h3 className="text-lg font-medium text-ra-text mb-2">准备就绪</h3>
                <p className="text-sm text-ra-text-tertiary">
                  创建您的第一个目标，Agent将开始工作。
                </p>
              </div>
            </div>
          )}
        </section>

        {detailGoal && ACTIVE_STATUSES.has(detailGoal.status) && (
          <div className="mb-6 min-h-[28px]" data-testid="activity-stream-slot" aria-hidden="true" />
        )}

        {/* 最近目标 */}
        <section data-testid="recent-goals-section" aria-label="Recent goals" className="mb-8">
          <div className="rounded-xl border border-ra-border bg-ra-light p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-medium text-ra-text">最近目标</h2>
              <span className="text-sm text-ra-text-tertiary">
                {Math.min(goals.length, 5)} / {goals.length}
              </span>
            </div>
            <div className="space-y-3">
              {goals.slice(0, 5).map((goal) => (
                <button
                  type="button"
                  key={goal.id}
                  onClick={() => setSelectedId(goal.id)}
                  className={cn(
                    "w-full rounded-lg border border-ra-border/70 px-4 py-3 text-left transition hover:bg-ra-tertiary/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    detailGoal?.id === goal.id && "border-ra-accent/60 bg-ra-tertiary/30",
                  )}
                >
                  <div className="flex items-start justify-between gap-4">
                    <p className="min-w-0 flex-1 text-sm leading-5 text-ra-text">
                      <span className="line-clamp-1">{goal.title}</span>
                    </p>
                    <span className={cn(
                      "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium",
                      goal.status === "COMPLETED" && "border border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
                      goal.status === "RUNNING" && "border border-blue-500/40 bg-blue-500/10 text-blue-300",
                      goal.status === "BLOCKED" && "border border-red-500/40 bg-red-500/10 text-red-300",
                      "border border-ra-border text-ra-text-secondary",
                    )}>{goal.status}</span>
                  </div>
                  <p className="mt-2 flex items-center justify-between text-[11px] text-ra-text-tertiary">
                    <span className="line-clamp-1">{goal.objective}</span>
                    <span className="inline-flex shrink-0 items-center gap-1">{relativeTime(goal.updated_at)}</span>
                  </p>
                </button>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
