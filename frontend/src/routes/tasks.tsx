import { Link, useSearchParams } from "react-router";
import { useEffect, useMemo } from "react";
import { ListChecks } from "lucide-react";
import { useTasks } from "@/hooks/use-tasks";
import { TaskInbox } from "@/components/task-inbox";
import { PageHeader } from "@/components/page-header";
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
    <main
      data-testid="tasks-page"
      className={cn(
        "flex h-full flex-col bg-ra-workspace px-4 py-6 sm:px-6 lg:px-7 lg:py-8",
        "custom-scrollbar-always",
      )}
    >
      {/*
       * The task collection previously rendered with no heading at all: this
       * was the only top-level surface without an `h1` or a page header.
       */}
      <PageHeader
        title="任务"
        icon={ListChecks}
        description="按状态分组的任务集合；打开任一任务查看执行流、变更与证据。"
      />
      {repository ? (
        <div
          data-testid="tasks-repository-filter"
          className="mb-3 flex items-center gap-2 text-xs text-ra-text-tertiary"
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
      <div className="flex flex-1 flex-col min-h-0">
        <TaskInbox
          tasks={filtered}
          isLoading={isLoading}
          isError={isError}
          error={error}
        />
      </div>
    </main>
  );
}
