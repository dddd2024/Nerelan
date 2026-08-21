import { Loader2, PlayCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { GoalComposer } from "@/components/goal-composer";
import { GoalProgress } from "@/components/goal-progress";
import { useGoals, usePlatformStatus, useStartGoal } from "@/hooks/use-platform";
import type { PlatformGoal } from "@/lib/platform-client";
import { cn } from "@/lib/cn";

function relativeTime(value: string) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return "刚刚";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  return `${Math.floor(seconds / 86400)} 天前`;
}

const TERMINAL_STATUSES = new Set(["COMPLETED", "BLOCKED", "INVALIDATED", "APPROVED", "PLANNED", "DRAFT"]);

export function HomePage() {
  const statusQuery = usePlatformStatus();
  const goalsQuery = useGoals();
  const startGoal = useStartGoal();
  const goals = useMemo(() => goalsQuery.data ?? [], [goalsQuery.data]);
  const [selectedId, setSelectedId] = useState<string | undefined>();

  useEffect(() => {
    if (!selectedId && goals[0]) setSelectedId(goals[0].id);
  }, [goals, selectedId]);

  const selected = useMemo(
    () => goals.find((goal) => goal.id === selectedId) ?? goals[0],
    [goals, selectedId],
  );
  const recent = useMemo(() => goals.slice(0, 3), [goals]);
  const platform = statusQuery.data;
  const activeWindow = platform?.autonomy.active_window;

  useEffect(() => {
    if (selected) return;
    const handler = () => {
      void goalsQuery.refetch();
      void statusQuery.refetch();
    };
    globalThis.addEventListener("visibilitychange", handler);
    globalThis.addEventListener("online", handler);
    return () => {
      globalThis.removeEventListener("visibilitychange", handler);
      globalThis.removeEventListener("online", handler);
    };
  }, [goalsQuery, statusQuery, selected]);

  useEffect(() => {
    if (!selected) return;
    const handler = () => {
      if (TERMINAL_STATUSES.has(selected.status)) return;
      void goalsQuery.refetch();
    };
    globalThis.addEventListener("visibilitychange", handler);
    globalThis.addEventListener("online", handler);
    return () => {
      globalThis.removeEventListener("visibilitychange", handler);
      globalThis.removeEventListener("online", handler);
    };
  }, [selected, goalsQuery]);

  function handleStarted(goal: PlatformGoal) {
    setSelectedId(goal.id);
  }

  return (
    <main data-testid="platform-home" className="min-h-full bg-[var(--oh-surface)] px-4 py-7 sm:px-8 lg:px-12 lg:py-10">
      <div className="mx-auto max-w-[1080px]">
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-ra-text-tertiary">Agent workspace</p>
            <h1 className="mt-2 text-3xl font-medium tracking-[-0.025em] text-ra-text sm:text-4xl">今天想完成什么？</h1>
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

        <section data-testid="goal-composer-section" className="mb-10">
          <GoalComposer
            busy={startGoal.isPending}
            onSubmit={(input) => startGoal.mutate(input, { onSuccess: handleStarted })}
          />
          {startGoal.isError && (
            <p role="alert" className="mt-3 text-sm text-red-300">{startGoal.error.message}</p>
          )}
        </section>

        <section data-testid="current-execution-section" aria-label="Current execution" className="mb-10">
          {selected ? (
            <GoalProgress goal={selected} />
          ) : (
            <div className="border-t border-ra-border/70 py-12 text-center text-sm text-ra-text-tertiary">
              第一个目标会在这里显示 Agent 的执行进度。
            </div>
          )}
        </section>

        <section data-testid="recent-goals-section" aria-label="Recent goals" className="border-t border-ra-border/70 pt-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-medium text-ra-text">最近目标</h2>
            <span className="text-xs text-ra-text-tertiary">{Math.min(goals.length, 3)} / {goals.length}</span>
          </div>
          <div className="space-y-2">
            {recent.map((goal) => (
              <button
                type="button"
                key={goal.id}
                onClick={() => setSelectedId(goal.id)}
                className={cn(
                  "w-full rounded-xl border border-ra-border/70 px-4 py-3 text-left transition hover:bg-ra-light/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                  selected?.id === goal.id && "border-ra-accent/60 bg-ra-light",
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
        </section>
      </div>
    </main>
  );
}
