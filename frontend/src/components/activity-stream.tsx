import { useState } from "react";
import type { ActivityEvent, ActivityEventType } from "@/types";
import { formatRelativeTime } from "@/lib/format";
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
  VALIDATED: { icon: CheckCircle2, color: "text-[#BCFF8C]" },
  WORKSPACE_READY: { icon: FolderTree, color: "text-[#BCFF8C]" },
  EXECUTOR_RUNNING: { icon: PlayCircle, color: "text-[#BCFF8C]" },
  EXECUTOR_FINISHED: { icon: StopCircle, color: "text-ra-text-tertiary" },
  LOCAL_VALIDATED: { icon: ShieldCheck, color: "text-[#BCFF8C]" },
  COMMITTED: { icon: GitCommit, color: "text-ra-text-tertiary" },
  PUSHED: { icon: Upload, color: "text-ra-text-tertiary" },
  DRAFT_PR_OPEN: { icon: GitPullRequest, color: "text-[#A3A3A3]" },
  WORKFLOWS_OBSERVED: { icon: Workflow, color: "text-[#BCFF8C]" },
  READY_FOR_HUMAN: { icon: Flag, color: "text-[#A3A3A3]" },
};

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
 * icon, title, meta, and expandable raw log. Border-l accent and dark
 * panel styling from OpenHands conversation theme.
 *
 * Modifications: reverse-agent ActivityEvent types replace V1 observations;
 * raw log rendering instead of markdown body.
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
          const isOpen = expandedRaw[e.id] ?? false;
          return {
            id: e.id,
            icon: <Icon aria-hidden="true" className="h-3.5 w-3.5" />,
            iconColor: color,
            title: e.title,
            meta: formatRelativeTime(e.timestamp),
            body: (
              <div className="space-y-1">
                <p className="text-ra-text-secondary">{e.description}</p>
                {hasRaw ? (
                  <button
                    type="button"
                    aria-expanded={isOpen}
                    aria-controls={`raw-${e.id}`}
                    onClick={() =>
                      setExpandedRaw((prev) => ({ ...prev, [e.id]: !prev[e.id] }))
                    }
                    className={cn(
                      "text-xs font-medium text-ra-text-tertiary underline-offset-2 hover:underline",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    )}
                    data-testid={`raw-toggle-${e.id}`}
                  >
                    {isOpen ? "隐藏原始日志" : "显示原始日志"}
                  </button>
                ) : null}
                {hasRaw && isOpen ? (
                  <pre
                    id={`raw-${e.id}`}
                    data-testid={`raw-log-${e.id}`}
                    className={cn(
                      "mt-2 overflow-x-auto rounded-md border border-ra-border",
                      "bg-ra-input p-2 font-mono text-xs text-ra-text-secondary",
                    )}
                  >
                    {e.rawLog}
                  </pre>
                ) : null}
              </div>
            ),
          };
        })}
      />

      <CollapsibleSection title="完整事件日志" summary={`${events.length} 条事件`}>
        <ul className="space-y-1 text-xs text-ra-text-tertiary">
          {events.map((e) => (
            <li key={e.id} className="flex gap-2">
              <span>{formatRelativeTime(e.timestamp)}</span>
              <span className="font-mono">{e.type}</span>
              <span>{e.title}</span>
            </li>
          ))}
        </ul>
      </CollapsibleSection>
    </div>
  );
}
