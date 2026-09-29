import { Flag, Map } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchRoadmap, type PlatformRoadmapPhase } from "@/lib/platform-client";
import { goalStatusLabel } from "@/lib/goal-status-label";
import { displayTitle } from "@/lib/display-title";
import { cn } from "@/lib/cn";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { PageHeader, PageSurface } from "@/components/page-header";
import {
  TONE_ACTIVE_FLAT,
  TONE_NEUTRAL_FLAT,
  TONE_SUCCESS_FLAT,
  TONE_WARNING_FLAT,
} from "@/lib/format";

const PHASE_STATUS_LABELS: Record<PlatformRoadmapPhase["derived_status"], string> = {
  PLANNED: "规划中",
  RUNNING: "进行中",
  BLOCKED: "受阻",
  COMPLETED: "执行完成，待审查",
};

const PHASE_STATUS_STYLES: Record<PlatformRoadmapPhase["derived_status"], string> = {
  PLANNED: TONE_NEUTRAL_FLAT,
  RUNNING: TONE_ACTIVE_FLAT,
  BLOCKED: TONE_WARNING_FLAT,
  COMPLETED: TONE_SUCCESS_FLAT,
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
    <PageSurface data-testid="roadmap-page">
      <PageHeader
        title="路线图"
        icon={Map}
        description="阶段状态始终由成员目标的状态推导，不独立维护；成员目标执行完成后，功能验证、审查与交付仍需分别确认。"
      />

      {roadmapQuery.isPending && <LoadingState label="正在加载路线图…" />}
      {roadmapQuery.isError && (
        <ErrorState
          title={roadmapQuery.data === undefined ? "路线图加载失败" : "路线图更新失败，显示上次内容"}
          error={roadmapQuery.error}
          onRetry={() => void roadmapQuery.refetch()}
        />
      )}
      {roadmapQuery.data !== undefined && <ol className="space-y-3" data-testid="roadmap-phase-list">
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
                  "shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium",
                  PHASE_STATUS_STYLES[phase.derived_status],
                )}
              >
                {PHASE_STATUS_LABELS[phase.derived_status]}
              </span>
            </div>

            {/*
             * Member goals are ordinary rows, not a second layer of cards:
             * a hairline divider carries the same grouping for less noise
             * (`#448` §2 / §12).
             */}
            <ul className="mt-3 divide-y divide-ra-border/60 border-t border-ra-border/60" data-testid={`roadmap-phase-goals-${phase.id}`}>
              {phase.goals.map((goal) => (
                <li
                  key={goal.id}
                  data-testid={`roadmap-goal-${goal.id}`}
                  className="flex items-center justify-between gap-3 py-2"
                >
                  <span className="min-w-0 truncate text-sm text-ra-text" title={displayTitle(goal.title, 160)}>{displayTitle(goal.title)}</span>
                  <span className="shrink-0 text-[11px] text-ra-text-tertiary">{goalStatusLabel(goal.status)}</span>
                </li>
              ))}
              {phase.goals.length === 0 && (
                <li className="py-4 text-center text-xs text-ra-text-tertiary">
                  该阶段还没有挂载目标。
                </li>
              )}
            </ul>
          </li>
        ))}
        {/* Was `rounded-2xl` + `py-12`, i.e. a 16px radius and a 93px dashed box
            for a single line, while every other empty state in the product is a
            `rounded-xl` box of roughly half that height. */}
        {phases.length === 0 && (
          <li className="rounded-xl border border-dashed border-ra-border py-8 text-center text-sm text-ra-text-tertiary">
            还没有路线图阶段。
          </li>
        )}
      </ol>}
    </PageSurface>
  );
}
