import type { Task } from "@/types";
import { Badge } from "@/components/badge";
import { CollapsibleSection } from "@/components/collapsible-section";
import {
  riskTierStyle,
  runStateStyle,
  permissionModeLabel,
  formatClock,
} from "@/lib/format";
import type { PolicyContract } from "@/types";

interface OverviewPanelProps {
  task: Task;
  policy?: PolicyContract;
}

export function OverviewPanel({ task, policy }: OverviewPanelProps) {
  const state = runStateStyle(task.state);
  const risk = riskTierStyle(task.riskTier);
  const window = policy?.autonomousWindow;

  return (
    <div data-testid="overview-panel" className="space-y-3">
      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Conclusion
        </h2>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <Badge className={state.badge} dot={state.dot}>
            {state.label}
          </Badge>
          <Badge className={risk.badge} dot={risk.dot}>
            {risk.label}
          </Badge>
        </div>
        <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Next action" value={task.nextAction ?? "—"} />
          <Field label="Blocker" value={task.blocker ?? "None"} />
          <Field label="Authority" value={task.authorityStatus} />
          <Field label="Tests" value={task.testStatus} />
          <Field label="Workflows" value={task.workflowStatus} />
          <Field
            label="Draft PR"
            value={
              task.draftPr
                ? `#${task.draftPr.number} @ ${task.draftPr.headSha.slice(0, 7)}`
                : "—"
            }
          />
        </dl>
      </section>

      <CollapsibleSection title="Active permission summary" defaultOpen>
        <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Permission profile" value={permissionModeLabel(task.permissionProfile)} />
          <Field label="Repository" value={policy?.repository ?? "—"} />
          <Field
            label="Unattended window"
            value={
              window?.enabled
                ? `Enabled until ${formatClock(window.expiresAt)}`
                : "Not enabled"
            }
          />
          <Field
            label="Merge into main"
            value={
              policy?.githubCapabilities.includes("merge_pr") ? "Permitted" : "Not permitted"
            }
          />
        </dl>
      </CollapsibleSection>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-700">{value}</dd>
    </div>
  );
}
