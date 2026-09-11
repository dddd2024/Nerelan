import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { HistoryPagination, useHistoryCursor } from "@/components/history-pagination";
import { fetchGoalsPage } from "@/lib/platform-client";

export function GoalsPage() {
  const navigation = useHistoryCursor();
  const query = useQuery({
    queryKey: ["goals", "history", navigation.cursor],
    queryFn: () => fetchGoalsPage({ cursor: navigation.cursor }),
    staleTime: 2_000, refetchInterval: 5_000,
  });
  return (
    <main className="min-h-full bg-ra-workspace px-4 py-7 sm:px-8 lg:px-12">
      <div className="mx-auto max-w-[1000px]">
        <Link to="/" className="text-sm text-ra-accent underline">返回工作区</Link>
        <h1 className="mt-4 text-3xl font-medium text-ra-text">所有目标</h1>
        <p className="mt-3 text-sm text-ra-text-secondary">浏览历史目标，打开目标继续查看进度与结果。</p>
        <HistoryPagination navigation={navigation} count={query.data?.items.length} total={query.data?.total} nextCursor={query.data?.next_cursor} loading={query.isFetching} />
        {query.isPending && <LoadingState label="正在加载目标历史…" />}
        {query.isError && <ErrorState title={query.data ? "目标历史更新失败，显示上次内容" : "目标历史加载失败"} error={query.error} onRetry={() => void query.refetch()} />}
        {query.data && <ul className="divide-y divide-ra-border rounded-xl border border-ra-border" aria-label="目标历史">
          {query.data.items.map((goal) => <li key={goal.id}>
            <Link to={`/?goal=${encodeURIComponent(goal.id)}`} className="block rounded-xl p-4 hover:bg-ra-light/30 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
              <div className="flex items-start justify-between gap-4"><span className="text-sm font-medium text-ra-text">{goal.title}</span><span className="text-xs text-ra-text-secondary">{goal.status}</span></div>
              <p className="mt-2 text-xs text-ra-text-secondary">{goal.objective}</p>
              <p className="mt-2 text-xs text-ra-text-tertiary">{goal.repository}</p>
            </Link>
          </li>)}
          {query.data.items.length === 0 && <li className="p-8 text-center text-sm text-ra-text-tertiary">这一页没有目标。</li>}
        </ul>}
      </div>
    </main>
  );
}
