import { Flag, Map } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchRoadmap, type PlatformRoadmapPhase } from "@/lib/platform-client";
import { cn } from "@/lib/cn";

const PHASE_STATUS_LABELS: Record<PlatformRoadmapPhase["derived_status"], string> = {
  PLANNED: "规划中",
  RUNNING: "进行中",
  BLOCKED: "受阻",
  COMPLETED: "已完成",
};

const PHASE_STATUS_STYLES: Record<PlatformRoadmapPhase["derived_status"], string> = {
  PLANNED: "bg-ra-light text-ra-text-secondary",
  RUNNING: "bg-sky-400/10 text-sky-300",
  BLOCKED: "bg-amber-300/10 text-amber-200",
  COMPLETED: "bg-emerald-400/10 text-emerald-300",
};

export function RoadmapPage() {
  const roadmapQuery = useQuery({
    queryKey: ["roadmap"],
    queryFn: fetchRoadmap,
    staleTime: 3_000,
    refetchInterval: 6_000,
  });
  const phases = roadmapQuery.data ?? [];

  return (
    <main data-testid="roadmap-page" className="min-h-full bg-[var(--oh-surface)] px-4 py-7 sm:px-8 lg:px-12 lg:py-10">
      <div className="mx-auto w-full max-w-[1000px]">
        <header className="mb-8">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-ra-text-tertiary">Roadmap</p>
          <h1 className="mt-2 flex items-center gap-2 text-3xl font-medium tracking-[-0.025em] text-ra-text sm:text-4xl">
            <Map className="h-7 w-7" aria-hidden="true" />路线图
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-ra-text-secondary">
            阶段状态始终由成员目标的状态推导，不独立维护；目标完成或受阻时阶段状态会自动更新。
          </p>
        </header>

        <ol className="space-y-4" data-testid="roadmap-phase-list">
          {phases.map((phase) => (
            <li
              key={phase.id}
              data-testid={`roadmap-phase-${phase.id}`}
              className="rounded-2xl border border-ra-border bg-ra-base p-5"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="flex items-center gap-2 text-base font-medium text-ra-text">
                    <Flag className="h-4 w-4 text-ra-text-tertiary" aria-hidden="true" />
                    {phase.title}
                  </h2>
                  {phase.description && (
                    <p className="mt-1 text-sm text-ra-text-secondary">{phase.description}</p>
                  )}
                </div>
                <span
                  data-testid={`roadmap-phase-status-${phase.id}`}
                  className={cn(
                    "rounded-full px-2.5 py-1 text-[11px] font-medium",
                    PHASE_STATUS_STYLES[phase.derived_status],
                  )}
                >
                  {PHASE_STATUS_LABELS[phase.derived_status]}
                </span>
              </div>

              <ul className="mt-4 space-y-1" data-testid={`roadmap-phase-goals-${phase.id}`}>
                {phase.goals.map((goal) => (
                  <li
                    key={goal.id}
                    data-testid={`roadmap-goal-${goal.id}`}
                    className="flex items-center justify-between gap-3 rounded-lg bg-ra-light/40 px-3 py-2"
                  >
                    <span className="min-w-0 truncate text-sm text-ra-text">{goal.title}</span>
                    <span className="shrink-0 text-[11px] text-ra-text-tertiary">{goal.status}</span>
                  </li>
                ))}
                {phase.goals.length === 0 && (
                  <li className="rounded-lg border border-dashed border-ra-border px-3 py-4 text-center text-xs text-ra-text-tertiary">
                    该阶段还没有挂载目标。
                  </li>
                )}
              </ul>
            </li>
          ))}
          {phases.length === 0 && (
            <li className="rounded-2xl border border-dashed border-ra-border py-12 text-center text-sm text-ra-text-tertiary">
              还没有路线图阶段。
            </li>
          )}
        </ol>
      </div>
    </main>
  );
}
