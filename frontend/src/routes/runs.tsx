import { GitPullRequest, PlayCircle } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchRuns } from "@/lib/platform-client";
import { cn } from "@/lib/cn";

const STATE_STYLES: Record<string, string> = {
  READY_FOR_HUMAN: "bg-emerald-400/10 text-emerald-300",
  RUNNING: "bg-sky-400/10 text-sky-300",
  BLOCKED_EXTERNAL: "bg-amber-300/10 text-amber-200",
  FAILED_TERMINAL: "bg-red-400/10 text-red-300",
  WAITING_FOR_OWNER: "bg-ra-light text-ra-text-secondary",
};

const STATE_LABELS: Record<string, string> = {
  READY_FOR_HUMAN: "等待人工审查",
  RUNNING: "运行中",
  BLOCKED_EXTERNAL: "外部受阻",
  FAILED_TERMINAL: "终态失败",
  WAITING_FOR_OWNER: "等待派发",
};

function relativeTime(value: string) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return "刚刚";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  return `${Math.floor(seconds / 86400)} 天前`;
}

export function RunsPage() {
  const runsQuery = useQuery({
    queryKey: ["runs"],
    queryFn: fetchRuns,
    staleTime: 2_000,
    refetchInterval: 4_000,
  });
  const runs = runsQuery.data ?? [];

  return (
    <main data-testid="runs-page" className="min-h-full bg-[var(--oh-surface)] px-4 py-7 sm:px-8 lg:px-12 lg:py-10">
      <div className="mx-auto w-full max-w-[1000px]">
        <header className="mb-8">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-ra-text-tertiary">Agent runs</p>
          <h1 className="mt-2 flex items-center gap-2 text-3xl font-medium tracking-[-0.025em] text-ra-text sm:text-4xl">
            <PlayCircle className="h-7 w-7" aria-hidden="true" />Agent 运行
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-ra-text-secondary">
            由任务库、目标链接与发布记录派生的只读时间线；任务状态变化会直接反映在这里。
          </p>
        </header>

        <ul className="space-y-2" data-testid="runs-list">
          {runs.map((run) => (
            <li
              key={run.task_id}
              data-testid={`run-${run.task_id}`}
              className="rounded-2xl border border-ra-border bg-ra-base p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-ra-text">{run.title}</p>
                  <p className="mt-1 text-xs text-ra-text-tertiary">
                    {run.repository} · {run.executor_kind} · {relativeTime(run.updated_at)}
                  </p>
                </div>
                <span
                  data-testid={`run-state-${run.task_id}`}
                  className={cn(
                    "shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium",
                    STATE_STYLES[run.state] ?? STATE_STYLES.WAITING_FOR_OWNER,
                  )}
                >
                  {STATE_LABELS[run.state] ?? run.state}
                </span>
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">
                {run.goal_id ? (
                  <span data-testid={`run-goal-${run.task_id}`} className="text-ra-text-secondary">
                    目标：{run.goal_title}
                  </span>
                ) : (
                  <span className="text-ra-text-tertiary">未关联目标</span>
                )}
                {run.publication && run.publication.pr_number > 0 && (
                  <a
                    href={run.publication.pr_url}
                    target="_blank"
                    rel="noreferrer"
                    data-testid={`run-pr-${run.task_id}`}
                    className="inline-flex items-center gap-1 text-ra-accent hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
                  >
                    <GitPullRequest className="h-3.5 w-3.5" aria-hidden="true" />
                    PR #{run.publication.pr_number}
                  </a>
                )}
              </div>
            </li>
          ))}
          {runs.length === 0 && (
            <li className="rounded-2xl border border-dashed border-ra-border py-12 text-center text-sm text-ra-text-tertiary">
              还没有 Agent 运行记录。
            </li>
          )}
        </ul>
      </div>
    </main>
  );
}
