import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { ChevronRight, Target } from "lucide-react";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { PageHeader, PageSurface } from "@/components/page-header";
import { HistoryPagination, useHistoryCursor } from "@/components/history-pagination";
import { goalIssueKey } from "@/components/sidebar";
import { fetchGoalsPage, type PlatformGoal } from "@/lib/platform-client";
import { formatRelativeTime } from "@/lib/format";
import { GOAL_TONE_DOT, GOAL_TONE_TEXT, goalState, goalTitle, issueRef, type GoalGroup } from "@/lib/goal-view";
import { cn } from "@/lib/cn";

const GROUPS: Array<{ id: GoalGroup; title: string; empty?: string; fold?: number }> = [
  { id: "needs_you", title: "需要你处理" },
  { id: "active", title: "进行中" },
  { id: "stopped", title: "已停下", fold: 5 },
  { id: "ended", title: "已结束", fold: 3 },
];

/** Goals that have not run yet continue on the approvals page. */
const BEFORE_RUN = new Set(["DRAFT", "PLANNED", "APPROVED"]);

function goalLink(goal: PlatformGoal): string {
  const id = encodeURIComponent(goal.id);
  return BEFORE_RUN.has(goal.status) ? `/approvals?goal=${id}` : `/?goal=${id}`;
}

interface Row {
  goal: PlatformGoal;
  /** Older goals for the same issue, newest first. */
  older: PlatformGoal[];
}

function time(value: string) {
  return new Date(value).getTime() || 0;
}

/** One row per issue: its newest goal, with the older ones folded under it. */
export function groupGoals(goals: PlatformGoal[]): Record<GoalGroup, Row[]> {
  const byIssue = new Map<string, PlatformGoal[]>();
  for (const goal of goals) {
    const key = goalIssueKey(goal);
    byIssue.set(key, [...(byIssue.get(key) ?? []), goal]);
  }
  const groups: Record<GoalGroup, Row[]> = { needs_you: [], active: [], stopped: [], ended: [] };
  for (const same of byIssue.values()) {
    const [goal, ...older] = [...same].sort((a, b) => time(b.updated_at) - time(a.updated_at));
    groups[goalState(goal).group].push({ goal, older });
  }
  for (const rows of Object.values(groups)) rows.sort((a, b) => time(b.goal.updated_at) - time(a.goal.updated_at));
  return groups;
}

function GoalRow({ goal, older }: Row) {
  const state = goalState(goal);
  const issue = issueRef(goal);
  return (
    <li data-testid={`goal-row-${goal.id}`}>
      <Link to={goalLink(goal)}
        className="flex items-start gap-3 px-4 py-3 transition-colors hover:bg-ra-light/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ra-accent">
        <span aria-hidden="true" className={cn("mt-[7px] h-2 w-2 shrink-0 rounded-full", GOAL_TONE_DOT[state.tone], state.key === "running" && "animate-pulse")} />
        <span className="min-w-0 flex-1">
          <span className="flex min-w-0 items-baseline gap-2">
            <span className="min-w-0 truncate text-sm font-medium text-ra-text" title={goalTitle(goal, 300)}>{goalTitle(goal)}</span>
            {issue && <span className="shrink-0 font-mono text-xs text-ra-text-tertiary">#{issue.number}</span>}
          </span>
          <span data-testid={`goal-progress-line-${goal.id}`} className={cn("mt-0.5 block truncate text-sm", GOAL_TONE_TEXT[state.tone])}>
            {state.label}{state.detail ? `：${state.detail}` : ""}
          </span>
        </span>
        <span className="shrink-0 pt-0.5 text-xs tabular-nums text-ra-text-tertiary">{formatRelativeTime(goal.updated_at)}</span>
      </Link>
      {older.length > 0 && (
        // Older goals for the same issue stay reachable here (the sidebar and Home show one per issue).
        <details className="group px-4 pb-2.5 pl-9" data-testid={`goal-older-${goal.id}`}>
          <summary className="w-fit cursor-pointer list-none text-xs text-ra-text-tertiary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent [&::-webkit-details-marker]:hidden">
            之前还有 {older.length} 个同一 Issue 的旧目标
            <ChevronRight className="ml-0.5 inline h-3 w-3 transition-transform group-open:rotate-90" aria-hidden="true" />
          </summary>
          <ul className="mt-1 space-y-0.5">
            {older.map((old) => {
              const oldState = goalState(old);
              return (
                <li key={old.id}>
                  <Link to={goalLink(old)} className="flex items-baseline gap-2 rounded text-xs hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
                    <span className={GOAL_TONE_TEXT[oldState.tone]}>{oldState.label}{oldState.detail ? `：${oldState.detail}` : ""}</span>
                    <span className="text-ra-text-tertiary">{formatRelativeTime(old.updated_at)}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </details>
      )}
    </li>
  );
}

function GoalGroupList({ title, rows, fold }: { title: string; rows: Row[]; fold?: number }) {
  const [open, setOpen] = useState(false);
  if (rows.length === 0) return null;
  const shown = fold && !open ? rows.slice(0, fold) : rows;
  return (
    <section aria-label={title} className="mb-6">
      <h2 className="mb-2 flex items-baseline gap-2 px-1 text-sm font-medium text-ra-text">
        {title}<span className="text-xs font-normal text-ra-text-tertiary">{rows.length}</span>
      </h2>
      <ul className="divide-y divide-ra-border/60 overflow-hidden rounded-xl border border-ra-border">
        {shown.map((row) => <GoalRow key={row.goal.id} {...row} />)}
      </ul>
      {shown.length < rows.length && (
        <button type="button" onClick={() => setOpen(true)}
          className="mt-2 inline-flex items-center gap-1 px-1 text-xs text-ra-text-secondary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
          显示其余 {rows.length - shown.length} 个<ChevronRight className="h-3 w-3" aria-hidden="true" />
        </button>
      )}
    </section>
  );
}

export function GoalsPage() {
  const navigation = useHistoryCursor();
  const query = useQuery({
    queryKey: ["goals", "history", navigation.cursor],
    queryFn: () => fetchGoalsPage({ cursor: navigation.cursor }),
    staleTime: 2_000, refetchInterval: 5_000,
  });
  const groups = useMemo(() => groupGoals(query.data?.items ?? []), [query.data]);
  const emptyPage = (query.data?.items.length ?? 0) === 0 && (query.data?.total ?? 0) > 0;
  const paged = navigation.hasPrevious || Boolean(query.data?.next_cursor) || emptyPage;

  return (
    <PageSurface data-testid="goals-page">
      <PageHeader title="目标" icon={Target} description="需要你处理的排在最前；同一个 Issue 的多次尝试只显示最新的一个。" />
      {paged && <HistoryPagination navigation={navigation} count={query.data?.items.length} total={query.data?.total} nextCursor={query.data?.next_cursor} loading={query.isFetching} />}
      {query.isPending && <LoadingState label="正在加载目标…" />}
      {query.isError && <ErrorState title={query.data ? "目标更新失败，显示上次内容" : "目标加载失败"} error={query.error} onRetry={() => void query.refetch()} />}
      {query.data && (
        <div aria-label="目标历史" className="mt-2">
          {GROUPS.map((group) => <GoalGroupList key={group.id} title={group.title} rows={groups[group.id]} fold={group.fold} />)}
          {query.data.items.length === 0 && (
            <p className="p-8 text-center text-sm text-ra-text-tertiary">{emptyPage ? "这一页没有目标。" : "还没有目标。"}</p>
          )}
        </div>
      )}
    </PageSurface>
  );
}
