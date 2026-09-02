import { Link, useSearchParams } from "react-router";
import { useEffect, useMemo } from "react";
import { useTasks } from "@/hooks/use-tasks";
import { TaskInbox } from "@/components/task-inbox";
import { cn } from "@/lib/cn";

export const TASK_LIST_REFRESH_INTERVAL_MS = 2_500;

/**
 * Task collection surface. Repository filtering is presentation-only and uses
 * the same authoritative task list; it does not introduce a second project
 * store or backend query contract.
 */
export function TasksPage() {
  const { data, isLoading, isError, error, refetch } = useTasks();
  const [searchParams] = useSearchParams();
  const repository = searchParams.get("repository")?.trim() ?? "";
  const filtered = useMemo(
    () =>
      repository && data
        ? data.filter((task) => task.repository === repository)
        : data,
    [data, repository],
  );
  const hasRunningTask = filtered?.some((task) => task.state === "RUNNING") ?? false;

  useEffect(() => {
    if (!hasRunningTask) return;

    const intervalId = window.setInterval(() => {
      void refetch().catch(() => undefined);
    }, TASK_LIST_REFRESH_INTERVAL_MS);

    return () => window.clearInterval(intervalId);
  }, [hasRunningTask, refetch]);

  useEffect(() => {
    const reconcile = () => {
      void refetch().catch(() => undefined);
    };

    window.addEventListener("focus", reconcile);
    window.addEventListener("online", reconcile);
    document.addEventListener("visibilitychange", reconcile);
    return () => {
      window.removeEventListener("focus", reconcile);
      window.removeEventListener("online", reconcile);
      document.removeEventListener("visibilitychange", reconcile);
    };
  }, [refetch]);

  return (
    <div
      data-testid="tasks-page"
      className={cn(
        "px-0 pt-4 bg-transparent h-full flex flex-col",
        "rounded-xl lg:px-[42px] lg:pt-[42px] custom-scrollbar-always",
      )}
    >
      {repository ? (
        <div
          data-testid="tasks-repository-filter"
          className="mb-3 flex items-center gap-2 px-4 text-xs text-ra-text-tertiary lg:px-0"
        >
          <span className="min-w-0 truncate">项目 · {repository}</span>
          <Link
            to="/tasks"
            className="shrink-0 text-ra-text-secondary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
          >
            查看全部
          </Link>
        </div>
      ) : null}
      <div className="flex flex-col flex-1 min-h-0">
        <TaskInbox
          tasks={filtered}
          isLoading={isLoading}
          isError={isError}
          error={error}
        />
      </div>
    </div>
  );
}
