import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { Target } from "lucide-react";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { PageHeader, PageSurface } from "@/components/page-header";
import { HistoryPagination, useHistoryCursor } from "@/components/history-pagination";
import { fetchGoalsPage } from "@/lib/platform-client";
import { goalStatusLabel } from "@/lib/goal-status-label";
import { displayTitle } from "@/lib/display-title";

export function GoalsPage() {
  const navigation = useHistoryCursor();
  const query = useQuery({
    queryKey: ["goals", "history", navigation.cursor],
    queryFn: () => fetchGoalsPage({ cursor: navigation.cursor }),
    staleTime: 2_000, refetchInterval: 5_000,
  });

  return (
    <PageSurface data-testid="goals-page">
      <PageHeader
        title="所有目标"
        icon={Target}
        description="浏览历史目标，打开目标继续查看进度与结果。"
      />
      <HistoryPagination navigation={navigation} count={query.data?.items.length} total={query.data?.total} nextCursor={query.data?.next_cursor} loading={query.isFetching} />
      {query.isPending && <LoadingState label="正在加载目标历史…" />}
      {query.isError && <ErrorState title={query.data ? "目标历史更新失败，显示上次内容" : "目标历史加载失败"} error={query.error} onRetry={() => void query.refetch()} />}
      {query.data && <ul className="divide-y divide-ra-border/60 overflow-hidden rounded-xl border border-ra-border" aria-label="目标历史">
        {query.data.items.map((goal) => <li key={goal.id}>
          <Link to={`/?goal=${encodeURIComponent(goal.id)}`} className="block p-4 transition-colors hover:bg-ra-light/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ra-accent">
            <div className="flex items-start justify-between gap-4">
              <span className="min-w-0 text-sm font-medium text-ra-text" title={displayTitle(goal.title, 160)}>{displayTitle(goal.title)}</span>
              <span className="shrink-0 text-xs text-ra-text-secondary">{goalStatusLabel(goal.status)}</span>
            </div>
            {goal.objective ? <p className="ra-measure mt-2 line-clamp-2 text-xs leading-5 text-ra-text-secondary" title={goal.objective}>{goal.objective}</p> : null}
            <p className="mt-2 text-xs text-ra-text-tertiary">{goal.repository}</p>
          </Link>
          {["DRAFT", "PLANNED", "APPROVED"].includes(goal.status) && <div className="px-4 pb-3">
            <Link
              to={`/approvals?goal=${encodeURIComponent(goal.id)}`}
              className="inline-flex items-center gap-1 text-xs text-ra-accent hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
            >
              审阅并继续此目标
            </Link>
          </div>}
        </li>)}
        {query.data.items.length === 0 && <li className="p-8 text-center text-sm text-ra-text-tertiary">这一页没有目标。</li>}
      </ul>}
    </PageSurface>
  );
}
