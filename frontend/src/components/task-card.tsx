import { Link } from "react-router";
import type { Task } from "@/types";
import { cn } from "@/lib/cn";
import {
  formatRelativeTime,
  permissionModeLabel,
  riskTierStyle,
  runStateStyle,
} from "@/lib/format";

interface TaskCardProps {
  task: Task;
  compact?: boolean;
}

/**
 * OpenHands ConversationCard structural port.
 *
 * Upstream sources:
 *   frontend/src/components/features/conversation-panel/conversation-card/
 *     conversation-card.tsx (tag 1.8.0)
 *   - `relative h-auto w-full p-3.5 border-b border-neutral-600 cursor-pointer
 *     hover:bg-[#454545]`
 *   - ConversationCardHeader: status dot + title
 *   - ConversationCardFooter: repo/branch + timestamp
 *
 * Structurally ported: same card structure — status indicator dot,
 * compact title row, repository/branch info, and relative timestamp
 * in a border-b separator layout. Hover state uses OpenHands hover
 * color (#454545). Status dot colors adapted from reverse-agent RunState.
 *
 * Modifications: tasks replace conversations; permission profile badge
 * replaces LLM model; reverse-agent repo/branch fields instead of
 * git_provider/selected_repository.
 * License: MIT (inherited from OpenHands)
 */
export function TaskCard({ task }: TaskCardProps) {
  const state = runStateStyle(task.state);
  const risk = riskTierStyle(task.riskTier);
  const note = task.blocker ?? task.nextAction;

  const statusDotColor = {
    "bg-emerald-500": "bg-ra-accent",
    "bg-sky-500": "bg-[#FFD43B]",
    "bg-amber-500": "bg-[#FFD43B]",
    "bg-orange-500": "bg-[#FFD43B]",
    "bg-rose-500": "bg-ra-status-error",
    "bg-violet-500": "bg-[#A3A3A3]",
    "bg-slate-400": "bg-[#A3A3A3]",
  }[state.dot] ?? "bg-[#A3A3A3]";

  return (
    <Link
      to={`/tasks/${task.id}`}
      data-testid={`task-card-${task.id}`}
      className={cn(
        "relative w-full p-3.5 border-b border-ra-border-strong cursor-pointer",
        "text-left transition-colors",
        "hover:bg-[#454545]",
      )}
    >
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-2 flex-1 min-w-0 overflow-hidden">
          <span
            className={cn("w-1.5 h-1.5 rounded-full shrink-0", statusDotColor)}
            aria-label={state.label}
            title={state.label}
          />
          <span
            className="text-xs leading-6 font-semibold bg-transparent truncate overflow-hidden"
            title={task.title}
          >
            #{task.issueNumber} — {task.title}
          </span>
        </div>
        <span className="text-xs text-ra-text-tertiary ml-2">
          {formatRelativeTime(task.updatedAt)}
        </span>
      </div>

      <div className="mt-1 flex flex-col gap-1">
        <div className="flex items-center gap-3 text-xs text-ra-text-secondary">
          <span className="font-mono">{task.branch}</span>
          {task.draftPr ? (
            <span className="inline-flex items-center gap-1">
              <span className="font-mono">#{task.draftPr.number}</span>
            </span>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs font-medium",
              risk.dot === "bg-rose-400"
                ? "bg-ra-status-error/10 text-ra-status-error"
                : "bg-ra-accent/10 text-ra-text",
            )}
          >
            <span
              className={cn("w-1.5 h-1.5 rounded-full", risk.dot.replace("bg-", "bg-"))}
            />
            {risk.label}
          </span>
          <span className="text-xs text-ra-text-tertiary">
            {permissionModeLabel(task.permissionProfile)}
          </span>
          {task.executor ? (
            <span
              className={cn(
                "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs font-medium",
                task.executor === "fixture/provider-free"
                  ? "bg-[#BCFF8C]/10 text-[#BCFF8C]"
                  : "bg-ra-accent/10 text-ra-accent",
              )}
              data-testid="task-executor-badge"
              title={`executor=${task.executor}`}
            >
              <span className="w-1 h-1 rounded-full bg-current shrink-0" />
              {task.executor === "fixture/provider-free"
                ? "fixture / provider-free"
                : task.executor}
            </span>
          ) : null}
        </div>
      </div>

      {note ? (
        <div className="mt-1 flex items-start gap-2 text-xs text-ra-text-secondary">
          <span className="truncate">{note}</span>
        </div>
      ) : null}
    </Link>
  );
}
