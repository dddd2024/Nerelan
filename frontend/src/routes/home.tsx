import { Activity, Clock3, Layers3, ShieldCheck } from "lucide-react";
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
  const platform = statusQuery.data;
  const window = platform?.autonomy.active_window;

  function handleStarted(goal: PlatformGoal) {
    setSelectedId(goal.id);
  }

  return (
    <main data-testid="platform-home" className="min-h-full bg-[var(--oh-surface)] px-4 py-7 sm:px-8 lg:px-12 lg:py-10">
      <div className="mx-auto grid w-full max-w-[1180px] gap-10 xl:grid-cols-[minmax(0,1fr)_280px]">
        <div className="min-w-0">
          <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-ra-text-tertiary">Multi-agent workspace</p>
              <h1 className="mt-2 text-3xl font-medium tracking-[-0.025em] text-ra-text sm:text-4xl">今天想完成什么？</h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-ra-text-secondary">
                给出最终目标。平台会生成规格与任务，协调 Agent，保存检查点，并把结果留给你审查。
              </p>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-ra-border bg-ra-light/70 px-3 py-1.5 text-xs text-ra-text-secondary">
              <span className={cn("h-2 w-2 rounded-full", platform?.coordinator.enabled ? "bg-emerald-400" : "bg-amber-300")} />
              {platform?.coordinator.enabled ? "协调器在线" : "手动模式"}
            </div>
          </header>

          <GoalComposer
            busy={startGoal.isPending}
            onSubmit={(input) => startGoal.mutate(input, { onSuccess: handleStarted })}
          />
          {startGoal.isError && (
            <p role="alert" className="mt-3 text-sm text-red-300">{startGoal.error.message}</p>
          )}
          <p className="mt-3 flex items-center gap-2 text-xs text-ra-text-tertiary">
            <ShieldCheck className="h-3.5 w-3.5" />
            策略在服务端执行；浏览器不持有 shell、文件系统或模型凭据。
          </p>

          <div className="mt-10">
            {selected ? (
              <GoalProgress goal={selected} />
            ) : (
              <div className="border-t border-ra-border/70 py-12 text-center text-sm text-ra-text-tertiary">
                第一个目标会在这里显示 Agent 的执行进度。
              </div>
            )}
          </div>
        </div>

        <aside className="border-t border-ra-border/70 pt-6 xl:border-l xl:border-t-0 xl:pl-7 xl:pt-1">
          <div className="grid grid-cols-2 gap-4 border-b border-ra-border/70 pb-6 xl:grid-cols-1">
            <div>
              <p className="flex items-center gap-2 text-xs text-ra-text-tertiary"><Activity className="h-3.5 w-3.5" />自治窗口</p>
              <p className="mt-2 text-sm text-ra-text">{window ? "运行中" : "未启用"}</p>
              <p className="mt-1 text-xs text-ra-text-tertiary">
                {window ? `${window.tasks_completed}/${window.max_tasks} 个任务完成` : "提交目标时可启用"}
              </p>
            </div>
            <div>
              <p className="flex items-center gap-2 text-xs text-ra-text-tertiary"><Layers3 className="h-3.5 w-3.5" />能力</p>
              <p className="mt-2 text-sm text-ra-text">{platform?.capability_count ?? "—"} 个已就绪</p>
              <p className="mt-1 text-xs text-ra-text-tertiary">规划 · 执行 · 验证 · Draft PR</p>
            </div>
          </div>

          <div className="pt-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium text-ra-text">最近目标</h2>
              <span className="text-xs text-ra-text-tertiary">{goals.length}</span>
            </div>
            <div className="space-y-1">
              {goals.slice(0, 8).map((goal) => (
                <button
                  type="button"
                  key={goal.id}
                  onClick={() => setSelectedId(goal.id)}
                  className={cn(
                    "w-full rounded-xl px-3 py-3 text-left transition focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    selected?.id === goal.id ? "bg-ra-light text-ra-text" : "text-ra-text-secondary hover:bg-ra-light/50 hover:text-ra-text",
                  )}
                >
                  <p className="line-clamp-2 text-sm leading-5">{goal.title}</p>
                  <p className="mt-2 flex items-center justify-between text-[11px] text-ra-text-tertiary">
                    <span>{goal.status}</span>
                    <span className="inline-flex items-center gap-1"><Clock3 className="h-3 w-3" />{relativeTime(goal.updated_at)}</span>
                  </p>
                </button>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}
