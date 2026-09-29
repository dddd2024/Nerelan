import { useState } from "react";
import type { ActivityEvent, ActivityEventType } from "@/types";
import { formatRelativeTime } from "@/lib/format";
import { activityEventLabel } from "@/lib/task-labels";
import { Timeline } from "@/components/timeline";
import { CollapsibleSection } from "@/components/collapsible-section";
import { cn } from "@/lib/cn";
import {
  Search,
  CheckCircle2,
  FolderTree,
  PlayCircle,
  StopCircle,
  ShieldCheck,
  GitCommit,
  Upload,
  GitPullRequest,
  Workflow,
  Flag,
} from "lucide-react";

interface ActivityStreamProps {
  events: ActivityEvent[];
}

const ICONS: Record<ActivityEventType, { icon: React.ComponentType<React.SVGProps<SVGSVGElement>>; color: string }> = {
  DISCOVERED: { icon: Search, color: "text-ra-text-tertiary" },
  VALIDATED: { icon: CheckCircle2, color: "text-ra-status-success" },
  WORKSPACE_READY: { icon: FolderTree, color: "text-ra-status-success" },
  EXECUTOR_RUNNING: { icon: PlayCircle, color: "text-ra-status-success" },
  EXECUTOR_FINISHED: { icon: StopCircle, color: "text-ra-text-tertiary" },
  LOCAL_VALIDATED: { icon: ShieldCheck, color: "text-ra-status-success" },
  COMMITTED: { icon: GitCommit, color: "text-ra-text-tertiary" },
  PUSHED: { icon: Upload, color: "text-ra-text-tertiary" },
  DRAFT_PR_OPEN: { icon: GitPullRequest, color: "text-ra-text-tertiary" },
  WORKFLOWS_OBSERVED: { icon: Workflow, color: "text-ra-status-success" },
  READY_FOR_HUMAN: { icon: Flag, color: "text-ra-text-tertiary" },
};

/** Any CJK range: the runtime title already speaks the user's language. */
const LOCALIZED_TEXT = /[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]/;

/**
 * The runtime sends machine labels such as `Workspace ready` or
 * `Executor action evidence`. `#448 §5` requires the stream to describe what
 * happened in product terms, so a non-localized runtime title is replaced by
 * the localized event-type label and kept verbatim behind disclosure. A title
 * that already reads as product language is never overridden.
 */
function rowTitle(event: ActivityEvent): string {
  return LOCALIZED_TEXT.test(event.title) ? event.title : activityEventLabel(event.type);
}

function hasRuntimeWording(event: ActivityEvent): boolean {
  return (
    !LOCALIZED_TEXT.test(event.title) ||
    (Boolean(event.description) && !LOCALIZED_TEXT.test(event.description))
  );
}

/**
 * Timeline of ActivityEvents — OpenHands GenericEventMessage adaptation.
 *
 * Upstream source:
 *   frontend/src/components/features/chat/generic-event-message.tsx
 *     (tag 1.8.0)
 *   - `border-l-2 pl-2 my-2 py-2 border-neutral-300 text-sm w-full`
 *   - expandable chevron pattern (angle-up/angle-down)
 *   frontend/src/components/features/chat/model-messages.tsx
 *   - collapsible sections with chevron
 *
 * Structurally ported: events render as collapsible timeline items with
 * icon, title, meta, and expandable raw log.
 *
 * Modifications: reverse-agent ActivityEvent types replace V1 observations;
 * Level 1 is product-language only, runtime wording moves to disclosure.
 * License: MIT (inherited from OpenHands)
 */
export function ActivityStream({ events }: ActivityStreamProps) {
  const [expandedRaw, setExpandedRaw] = useState<Record<string, boolean>>({});

  return (
    <div data-testid="activity-stream" className="space-y-3">
      <Timeline
        items={events.map((e) => {
          const { icon: Icon, color } = ICONS[e.type];
          const hasRaw = Boolean(e.rawLog);
          const hasRuntime = hasRuntimeWording(e);
          const expandable = hasRaw || hasRuntime;
          const isOpen = expandedRaw[e.id] ?? false;
          const localizedDescription =
            e.description && LOCALIZED_TEXT.test(e.description) ? e.description : "";
          return {
            id: e.id,
            icon: <Icon aria-hidden="true" className="h-3.5 w-3.5" />,
            iconColor: color,
            title: rowTitle(e),
            meta: formatRelativeTime(e.timestamp),
            body: (
              <div className="space-y-1">
                {localizedDescription ? (
                  <p className="text-ra-text-secondary">{localizedDescription}</p>
                ) : null}
                {expandable ? (
                  <button
                    type="button"
                    aria-expanded={isOpen}
                    aria-controls={`raw-${e.id}`}
                    onClick={() =>
                      setExpandedRaw((prev) => ({ ...prev, [e.id]: !prev[e.id] }))
                    }
                    className={cn(
                      // `inline-block py-1` lifts the hit area to the 24px
                      // minimum target without changing the 12px type size or
                      // the underline treatment; a bare inline link measured
                      // only 84x16.
                      "inline-block py-1 text-xs font-medium text-ra-text-tertiary underline-offset-2 hover:underline",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    )}
                    data-testid={`raw-toggle-${e.id}`}
                  >
                    {isOpen ? "隐藏运行时原文" : "显示运行时原文"}
                  </button>
                ) : null}
                {expandable && isOpen ? (
                  <div
                    id={`raw-${e.id}`}
                    data-testid={`raw-log-${e.id}`}
                    className={cn(
                      "mt-2 space-y-1 overflow-x-auto rounded-md border border-ra-border",
                      "bg-ra-input p-2 font-mono text-xs text-ra-text-secondary",
                    )}
                  >
                    <p>{e.title}</p>
                    {e.description ? <p>{e.description}</p> : null}
                    {hasRaw ? <pre className="whitespace-pre-wrap">{e.rawLog}</pre> : null}
                  </div>
                ) : null}
              </div>
            ),
          };
        })}
      />

      <CollapsibleSection title="完整事件日志" summary={`${events.length} 条事件`}>
        <ul className="space-y-1 text-xs text-ra-text-tertiary">
          {events.map((e) => (
            <li key={e.id} className="flex flex-wrap gap-x-2">
              <span className="tabular-nums">{formatRelativeTime(e.timestamp)}</span>
              <span className="font-mono">{e.type}</span>
              <span>{activityEventLabel(e.type)}</span>
            </li>
          ))}
        </ul>
      </CollapsibleSection>
    </div>
  );
}
