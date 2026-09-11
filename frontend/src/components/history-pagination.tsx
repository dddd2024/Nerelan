import { useState } from "react";

export function useHistoryCursor() {
  const [cursors, setCursors] = useState<Array<string | undefined>>([undefined]);
  return {
    cursor: cursors.at(-1),
    page: cursors.length,
    hasPrevious: cursors.length > 1,
    previous: () => setCursors((values) => values.length > 1 ? values.slice(0, -1) : values),
    latest: () => setCursors([undefined]),
    next: (cursor: string | null | undefined) => {
      if (cursor) setCursors((values) => values.at(-1) === cursor ? values : [...values, cursor]);
    },
  };
}

export function HistoryPagination({ navigation, count, total, nextCursor, loading }: {
  navigation: ReturnType<typeof useHistoryCursor>;
  count?: number;
  total?: number | null;
  nextCursor?: string | null;
  loading: boolean;
}) {
  const buttonClass = "min-h-9 rounded-lg border border-ra-border px-3 text-xs hover:bg-ra-light disabled:cursor-not-allowed disabled:opacity-40 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent";
  return (
    <nav aria-label="历史分页" className="my-4 flex flex-wrap items-center justify-between gap-3 text-ra-text-secondary">
      <p aria-live="polite" className="text-xs">第 {navigation.page} 页{count !== undefined ? ` · 本页 ${count} 条` : ""}{total != null ? ` · 共 ${total} 条` : ""}</p>
      <div className="flex flex-wrap gap-2">
        <button type="button" className={buttonClass} onClick={navigation.latest} disabled={loading || !navigation.hasPrevious}>返回最新</button>
        <button type="button" className={buttonClass} onClick={navigation.previous} disabled={loading || !navigation.hasPrevious}>上一页</button>
        <button type="button" className={buttonClass} onClick={() => navigation.next(nextCursor)} disabled={loading || !nextCursor}>下一页</button>
      </div>
    </nav>
  );
}
