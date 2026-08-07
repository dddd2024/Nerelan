import type { Task } from "@/types";
import type { PolicyContract } from "@/types";
import type { ReactNode } from "react";
import { Badge } from "@/components/badge";
import { CollapsibleSection } from "@/components/collapsible-section";
import {
  riskTierStyle,
  runStateStyle,
  permissionModeLabel,
  formatClock,
} from "@/lib/format";
import { cn } from "@/lib/cn";
import { GitPullRequest } from "lucide-react";

interface OverviewPanelProps {
  task: Task;
  policy?: PolicyContract;
}

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-ra-text-tertiary">{label}</dt>
      <dd className="mt-0.5 text-sm text-ra-text-secondary">{value}</dd>
    </div>
  );
}

/**
 * OpenHands ConversationNameWithStatus / ConversationMain structural port.
 *
 * Upstream sources:
 *   frontend/src/components/features/conversation/conversation-name-with-status.tsx
 *     (tag 1.8.0) — title + status dot + action buttons
 *   frontend/src/components/features/conversation/conversation-main/
 *     conversation-main.tsx — header with workspace info
 *
 * Styled to match OpenHands dark panel with border and rounded corners.
 */
export function OverviewPanel({ task, policy }: OverviewPanelProps) {
  const state = runStateStyle(task.state);
  const risk = riskTierStyle(task.riskTier);
  const window = policy?.autonomousWindow;

  return (
    <div data-testid="overview-panel" className="space-y-3">
      <section className="rounded-lg border border-ra-border bg-ra-light p-4">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-ra-text-tertiary">
          当前结论
        </h2>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <Badge className={cn(state.badge)} dot={state.dot}>
            {state.label}
          </Badge>
          <Badge className={cn(risk.badge)} dot={risk.dot}>
            {risk.label}
          </Badge>
        </div>
        <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="无人值守窗口" value={window?.enabled ? `截至 ${formatClock(window.expiresAt)}` : "未启用"} />
          <Field
            label="Draft PR"
            value={
              task.draftPr ? (
                <span className="inline-flex items-center gap-1">
                  <GitPullRequest aria-hidden="true" className="h-3 w-3 text-ra-text-tertiary" />
                  <a
                    href={task.draftPr.url}
                    className="text-ra-accent hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
                    target="_blank"
                    rel="noreferrer"
                  >
                    #{task.draftPr.number}
                  </a>
                  <span className="font-mono text-xs text-ra-text-tertiary">
                    @ {task.draftPr.headSha.slice(0, 7)}
                  </span>
                </span>
              ) : (
                "—"
              )
            }
          />
           <Field label="阻塞项" value={task.blocker ?? "无"} />
           <Field label="下一步" value={task.nextAction ?? "—"} />
        </dl>
      </section>

      <CollapsibleSection title="活跃权限摘要" defaultOpen>
        <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="权限配置" value={permissionModeLabel(task.permissionProfile)} />
          <Field label="仓库" value={policy?.repository ?? "—"} />
          <Field
            label="无人值守窗口"
            value={
              window?.enabled ? `启用至 ${formatClock(window.expiresAt)}` : "未启用"
            }
          />
          <Field
            label="合并至 main"
            value={policy?.githubCapabilities.includes("merge_pr") ? "允许" : "不允许"}
          />
        </dl>
      </CollapsibleSection>
    </div>
  );
}
