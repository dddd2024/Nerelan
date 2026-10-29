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
  EXECUTOR_PROGRESS: { icon: PlayCircle, color: "text-ra-text-tertiary" },
  EXECUTOR_COMPLETED: { icon: CheckCircle2, color: "text-ra-status-success" },
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
export type ActivityDensity = "brief" | "standard" | "detail";
const DENSITY_PREF_KEY = "nerelan.activity-density.v1";
const SIGNIFICANT_TYPES = new Set<ActivityEventType>([
  "VALIDATED", "LOCAL_VALIDATED", "EXECUTOR_COMPLETED", "READY_FOR_HUMAN",
  "DRAFT_PR_OPEN",
]);

function briefEvents(events: ActivityEvent[]): ActivityEvent[] {
  const recent = events.slice(-2);
  const notable = [...events].reverse().find((event) =>
    SIGNIFICANT_TYPES.has(event.type) ||
    /失败|阻塞|拒绝|异常|failed|blocked|denied|error/i.test(
      `${event.title} ${event.description}`,
    ),
  );
  // Only select observed events, preserving their original chronology and IDs.
  const ids = new Set([...recent, ...(notable ? [notable] : [])].map((event) => event.id));
  return events.filter((event) => ids.has(event.id));
}

const DENSITIES: { value: ActivityDensity; label: string }[] = [
  { value: "brief", label: "简洁" },
  { value: "standard", label: "标准" },
  { value: "detail", label: "详细" },
];

function savedDensity(): ActivityDensity {
  try {
    const preference = window.localStorage.getItem(DENSITY_PREF_KEY);
    if (preference === "brief" || preference === "standard" || preference === "detail") {
      return preference;
    }
  } catch {
    // Storage may be unavailable in restricted browser contexts.
  }
  return "standard";
}

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
  const [density, setDensity] = useState<ActivityDensity>(savedDensity);
  const visibleEvents = density === "brief" ? briefEvents(events) : events;
  const changeDensity = (next: ActivityDensity) => {
    setDensity(next);
    try {
      window.localStorage.setItem(DENSITY_PREF_KEY, next);
    } catch {
      // UI mode is still usable when persistence is unavailable.
    }
  };

  return (
    <div data-testid="activity-stream" className="space-y-3">
      <div role="group" aria-label="执行记录显示方式" className="flex items-center gap-1" data-testid="activity-density-control">
        {DENSITIES.map((option) => (
          <button
            key={option.value}
            type="button"
            aria-pressed={density === option.value}
            data-testid={`activity-density-${option.value}`}
            onClick={() => changeDensity(option.value)}
            className={cn(
              "min-h-8 rounded-md px-3 text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
              density === option.value
                ? "bg-ra-tertiary text-ra-text font-medium"
                : "text-ra-text-tertiary hover:text-ra-text hover:bg-ra-tertiary/50",
            )}
          >
            {option.label}
          </button>
        ))}
        <span className="ml-auto text-xs text-ra-text-tertiary">
          {density === "brief" ? `最近 ${visibleEvents.length} / ${events.length} 条` : `${events.length} 条事件`}
        </span>
      </div>
      <Timeline
        items={visibleEvents.map((e) => {
          const { icon: Icon, color } = ICONS[e.type];
          const hasRaw = Boolean(e.rawLog);
          const hasRuntime = hasRuntimeWording(e);
          const expandable = hasRaw || hasRuntime;
          // Detailed mode does not silently reveal stored raw logs: they may
          // contain diagnostic data not intended for the default surface.
          const isOpen = expandedRaw[e.id] ?? false;
          // Executor-progress descriptions contain the executor's actual public
          // activity text. Preserve the original language, never invent a summary.
          const localizedDescription =
            e.description && (LOCALIZED_TEXT.test(e.description) ||
              e.type === "EXECUTOR_PROGRESS" || e.type === "EXECUTOR_COMPLETED")
              ? e.description : "";
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
                {density === "detail" ? (
                  <p className="font-mono text-xs text-ra-text-tertiary"
                     data-testid={`event-source-${e.id}`}>
                    {e.type} · {e.id} · {e.timestamp}
                  </p>
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

      {density === "detail" ? <CollapsibleSection title="完整事件日志" summary={`${events.length} 条事件`}>
        <ul className="space-y-1 text-xs text-ra-text-tertiary">
          {events.map((e) => (
            <li key={e.id} className="flex flex-wrap gap-x-2">
              <span className="tabular-nums">{formatRelativeTime(e.timestamp)}</span>
              <span className="font-mono">{e.type}</span>
              <span>{activityEventLabel(e.type)}</span>
            </li>
          ))}
        </ul>
      </CollapsibleSection> : null}
    </div>
  );
}
