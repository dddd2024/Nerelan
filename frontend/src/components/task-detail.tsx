import { useState } from "react";
import { Link } from "react-router";
import { ArrowLeft, GitBranch, GitPullRequest } from "lucide-react";
import type { Task } from "@/types";
import type { PolicyContract } from "@/types";
import { Badge } from "@/components/badge";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { OverviewPanel } from "@/components/overview-panel";
import { ActivityStream } from "@/components/activity-stream";
import { ChangesPanel } from "@/components/changes-panel";
import { EvidencePanel } from "@/components/evidence-panel";
import { PermissionsPanel } from "@/components/permissions-panel";
import {
  riskTierStyle,
  runStateStyle,
  permissionModeLabel,
  formatClock,
} from "@/lib/format";
import { cn } from "@/lib/cn";
import { profileToPolicy } from "@/lib/profile-mapper";

type Tab = "overview" | "activity" | "changes" | "evidence" | "permissions";

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "概览" },
  { id: "activity", label: "活动" },
  { id: "changes", label: "变更" },
  { id: "evidence", label: "证据" },
  { id: "permissions", label: "权限" },
];

interface TaskDetailProps {
  task: Task | undefined;
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
}

export function TaskDetail({ task, isLoading, isError, error }: TaskDetailProps) {
  const [tab, setTab] = useState<Tab>("overview");

  if (isLoading) {
    return (
      <div data-testid="task-detail">
        <LoadingState label="加载任务中…" />
      </div>
    );
  }
  if (isError || !task) {
    return (
      <div data-testid="task-detail">
        <ErrorState title="未找到任务" error={error} />
        <div className="px-4">
          <Link
            to="/tasks"
            className="text-sm text-slate-500 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            ← 返回任务列表
          </Link>
        </div>
      </div>
    );
  }

  const state = runStateStyle(task.state);
  const risk = riskTierStyle(task.riskTier);
  const policy: PolicyContract = profileToPolicy(task.permissionProfile);
  const window = policy.autonomousWindow;

  return (
    <div data-testid="task-detail" className="space-y-4">
      <div>
        <Link
          to="/tasks"
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          任务
        </Link>
      </div>

      <header className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span>#{task.issueNumber}</span>
              <span aria-hidden="true">·</span>
              <span className="inline-flex items-center gap-1 font-mono">
                <GitBranch aria-hidden="true" className="h-3 w-3" />
                {task.branch}
              </span>
            </div>
            <h1 className="mt-1 text-lg font-semibold text-slate-900">
              {task.title}
            </h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge className={state.badge} dot={state.dot}>
              {state.label}
            </Badge>
            <Badge className={risk.badge} dot={risk.dot}>
              {risk.label}
            </Badge>
            <Badge>{permissionModeLabel(task.permissionProfile)}</Badge>
          </div>
        </div>

        <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Meta label="无人值守窗口">
            {window.enabled ? `截至 ${formatClock(window.expiresAt)}` : "未启用"}
          </Meta>
          <Meta label="Draft PR">
            {task.draftPr ? (
              <span className="inline-flex items-center gap-1">
                <GitPullRequest aria-hidden="true" className="h-3 w-3" />
                <a
                  href={task.draftPr.url}
                  className="text-sky-600 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                  target="_blank"
                  rel="noreferrer"
                >
                  #{task.draftPr.number}
                </a>
                <span className="font-mono text-xs text-slate-400">
                  @ {task.draftPr.headSha.slice(0, 7)}
                </span>
              </span>
            ) : (
              "—"
            )}
          </Meta>
          <Meta label="阻塞项">{task.blocker ?? "无"}</Meta>
          <Meta label="下一步">{task.nextAction ?? "—"}</Meta>
        </dl>
      </header>

      <div
        role="tablist"
        aria-label="任务分区"
        className="flex flex-wrap gap-1 rounded-lg border border-slate-200 bg-white p-1"
      >
        {TABS.map((t) => {
          const selected = t.id === tab;
          return (
            <button
              key={t.id}
              role="tab"
              id={`tab-${t.id}`}
              aria-selected={selected}
              aria-controls={`tabpanel-${t.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => setTab(t.id)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400",
                selected
                  ? "bg-slate-100 text-slate-900"
                  : "text-slate-500 hover:text-slate-700",
              )}
              data-testid={`tab-button-${t.id}`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      <div
        role="tabpanel"
        id={`tabpanel-${tab}`}
        aria-labelledby={`tab-${tab}`}
        data-testid={`tab-panel-${tab}`}
      >
        {tab === "overview" ? <OverviewPanel task={task} policy={policy} /> : null}
        {tab === "activity" ? <ActivityStream events={task.activity} /> : null}
        {tab === "changes" ? <ChangesPanel changes={task.changes} /> : null}
        {tab === "evidence" ? <EvidencePanel evidence={task.evidence} /> : null}
        {tab === "permissions" ? <PermissionsPanel policy={policy} /> : null}
      </div>
    </div>
  );
}

function Meta({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-700">{children}</dd>
    </div>
  );
}
