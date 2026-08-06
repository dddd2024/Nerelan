import { Link } from "react-router";
import { AlertCircle, ArrowRight } from "lucide-react";
import type { Task } from "@/types";
import { Badge } from "@/components/badge";
import { cn } from "@/lib/cn";
import {
  formatRelativeTime,
  permissionModeLabel,
  riskTierStyle,
  runStateStyle,
} from "@/lib/format";

interface TaskCardProps {
  task: Task;
}

export function TaskCard({ task }: TaskCardProps) {
  const state = runStateStyle(task.state);
  const risk = riskTierStyle(task.riskTier);
  const note = task.blocker ?? task.nextAction;

  return (
    <Link
      to={`/tasks/${task.id}`}
      data-testid={`task-card-${task.id}`}
      className={cn(
        "block rounded-lg border border-slate-200 bg-white p-4 transition-colors",
        "hover:border-slate-300 hover:bg-slate-50/60",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>#{task.issueNumber}</span>
            <span aria-hidden="true">·</span>
            <span className="font-mono">{task.branch}</span>
          </div>
          <h3 className="mt-1 truncate text-sm font-medium text-slate-800">
            {task.title}
          </h3>
        </div>
        <ArrowRight aria-hidden="true" className="mt-1 h-4 w-4 shrink-0 text-slate-300" />
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Badge className={state.badge} dot={state.dot}>
          {state.label}
        </Badge>
        <Badge className={risk.badge} dot={risk.dot}>
          {risk.label}
        </Badge>
        <Badge>{permissionModeLabel(task.permissionProfile)}</Badge>
        <span className="ml-auto text-xs text-slate-400">
          {formatRelativeTime(task.updatedAt)}
        </span>
      </div>
      {note ? (
        <div className="mt-3 flex items-start gap-2 border-t border-slate-100 pt-2 text-xs text-slate-600">
          <AlertCircle
            aria-hidden="true"
            className={cn(
              "mt-0.5 h-3.5 w-3.5 shrink-0",
              task.blocker ? "text-amber-500" : "text-slate-400",
            )}
          />
          <span>
            <span className="font-medium text-slate-700">
              {task.blocker ? "阻塞项：" : "下一步："}
            </span>
            {note}
          </span>
        </div>
      ) : null}
    </Link>
  );
}
