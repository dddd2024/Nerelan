import { Link } from "react-router";
import type { Task } from "@/types";
import { cn } from "@/lib/cn";
import { displayTitle } from "@/lib/display-title";
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
 * in a border-b separator layout. The upstream hardcoded hover color is
 * replaced by the `ra-tertiary` surface token; status dot colors are
 * tokenised instead of carrying the upstream palette.
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

  /*
   * Row shape follows `#448` §7 (high-density / low-noise rows): identity and
   * the one exceptional fact stay on the left, bounded secondary metadata is
   * pushed to the right edge of the same line instead of being stacked into
   * three short lines. The previous version rendered four stacked rows, which
   * measured 76px per task and left the right half of every line empty.
   *
   * The card sits inside a bordered section container, so it carries only a
   * hairline separator: a second full-strength border read as a double frame.
   */
  return (
    <Link
      to={`/tasks/${task.id}`}
      data-testid={`task-card-${task.id}`}
      className={cn(
        "relative block w-full border-b border-ra-border/60 px-3.5 py-2.5 last:border-b-0",
        "text-left transition-colors hover:bg-ra-tertiary focus:outline-none",
        "focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ra-accent",
      )}
    >
      <div className="flex items-center gap-2">
        <span
          className={cn("h-1.5 w-1.5 shrink-0 rounded-full", state.dot)}
          aria-label={state.label}
          title={state.label}
        />
        <span
          className="min-w-0 flex-1 truncate text-[13px] font-medium leading-5 text-ra-text"
          title={displayTitle(task.title, 160)}
        >
          {task.issueNumber ? `#${task.issueNumber} — ` : ""}{displayTitle(task.title)}
        </span>
        <span className="shrink-0 text-[11px] tabular-nums text-ra-text-tertiary">
          {formatRelativeTime(task.updatedAt)}
        </span>
      </div>

      <div className="mt-1 flex items-center gap-2 pl-3.5 text-[11px] text-ra-text-tertiary">
        <span className="min-w-0 truncate font-mono text-ra-text-secondary">
          {task.branch}
        </span>
        {task.draftPr ? <span className="shrink-0 font-mono">#{task.draftPr.number}</span> : null}
        <span className="shrink-0">{permissionModeLabel(task.permissionProfile)}</span>
        {task.executor ? (
          /*
           * Executor identity is healthy context, so it stays quiet. It was
           * previously tinted accent/green, which made a normal fact compete
           * with the exceptional ones (`#448` §10).
           */
          <span
            className="shrink-0 truncate rounded-full bg-ra-light px-1.5 py-0.5 text-ra-text-secondary"
            data-testid="task-executor-badge"
            title={`executor=${task.executor}`}
          >
            {task.executor === "fixture/provider-free" ? "fixture / provider-free" : task.executor}
          </span>
        ) : null}
        {task.riskTier && task.riskTier !== "UNKNOWN" ? (
          <span className="ml-auto shrink-0">
            {/* Healthy/unknown tiers stay implicit on the list surface: the API
                currently returns no risk field, so rendering the neutral
                "风险未提供" chip here repeated the same zero-information pill on
                every row. Elevated tiers (R2/R3) are the only ones that carry
                signal, matching the intent recorded in riskTierStyle. */}
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[11px] font-medium",
                risk.badge,
              )}
            >
              <span className={cn("h-1 w-1 rounded-full", risk.dot)} />
              {risk.label}
            </span>
          </span>
        ) : null}
      </div>

      {note ? (
        <p className="mt-1 truncate pl-3.5 text-[11px] leading-4 text-ra-text-secondary" title={note}>
          {note}
        </p>
      ) : null}
    </Link>
  );
}
