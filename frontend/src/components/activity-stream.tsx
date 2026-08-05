import { useState } from "react";
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
import type { ActivityEvent, ActivityEventType } from "@/types";
import { formatRelativeTime } from "@/lib/format";
import { Timeline } from "@/components/timeline";
import { CollapsibleSection } from "@/components/collapsible-section";

interface ActivityStreamProps {
  events: ActivityEvent[];
}

const ICONS: Record<ActivityEventType, { icon: typeof Search; color: string }> = {
  DISCOVERED: { icon: Search, color: "text-slate-500" },
  VALIDATED: { icon: CheckCircle2, color: "text-sky-500" },
  WORKSPACE_READY: { icon: FolderTree, color: "text-sky-500" },
  EXECUTOR_RUNNING: { icon: PlayCircle, color: "text-sky-500" },
  EXECUTOR_FINISHED: { icon: StopCircle, color: "text-slate-500" },
  LOCAL_VALIDATED: { icon: ShieldCheck, color: "text-emerald-500" },
  COMMITTED: { icon: GitCommit, color: "text-slate-500" },
  PUSHED: { icon: Upload, color: "text-slate-500" },
  DRAFT_PR_OPEN: { icon: GitPullRequest, color: "text-violet-500" },
  WORKFLOWS_OBSERVED: { icon: Workflow, color: "text-emerald-500" },
  READY_FOR_HUMAN: { icon: Flag, color: "text-emerald-500" },
};

/**
 * Timeline of ActivityEvents. Raw logs collapsed by default, expandable.
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
                <p className="text-slate-600">{e.description}</p>
                {hasRaw ? (
                  <button
                    type="button"
                    aria-expanded={isOpen}
                    aria-controls={`raw-${e.id}`}
                    onClick={() =>
                      setExpandedRaw((prev) => ({ ...prev, [e.id]: !prev[e.id] }))
                    }
                    className="text-xs font-medium text-slate-500 underline-offset-2 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                    data-testid={`raw-toggle-${e.id}`}
                  >
                    {isOpen ? "Hide raw log" : "Show raw log"}
                  </button>
                ) : null}
                {hasRaw && isOpen ? (
                  <pre
                    id={`raw-${e.id}`}
                    data-testid={`raw-log-${e.id}`}
                    className="overflow-x-auto rounded-md border border-slate-200 bg-slate-50 p-2 font-mono text-xs text-slate-700"
                  >
                    {e.rawLog}
                  </pre>
                ) : null}
              </div>
            ),
          };
        })}
      />
      <CollapsibleSection title="Full event log" summary={`${events.length} events`}>
        <ul className="space-y-1 text-xs text-slate-600">
          {events.map((e) => (
            <li key={e.id} className="flex gap-2">
              <span className="text-slate-400">{formatRelativeTime(e.timestamp)}</span>
              <span className="font-mono text-slate-500">{e.type}</span>
              <span>{e.title}</span>
            </li>
          ))}
        </ul>
      </CollapsibleSection>
    </div>
  );
}
