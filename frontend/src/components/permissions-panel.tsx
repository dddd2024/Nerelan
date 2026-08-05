import type { PolicyContract } from "@/types";
import { Badge } from "@/components/badge";
import { CollapsibleSection } from "@/components/collapsible-section";
import { summarizePolicy } from "@/lib/policy-summary";
import { permissionModeLabel } from "@/lib/format";

interface PermissionsPanelProps {
  policy: PolicyContract;
}

export function PermissionsPanel({ policy }: PermissionsPanelProps) {
  const summary = summarizePolicy(policy);
  return (
    <div data-testid="permissions-panel" className="space-y-3">
      <section className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex items-center gap-2">
          <Badge>{permissionModeLabel(policy.mode)}</Badge>
          <span className="font-mono text-xs text-slate-500">{policy.repository}</span>
        </div>
        <p className="mt-3 text-sm text-slate-700" data-testid="permissions-summary">
          {summary}
        </p>
      </section>

      <CollapsibleSection title="Resource access" defaultOpen>
        <dl className="space-y-3 text-sm">
          <Scope label="Filesystem (allowed)">
            {policy.resourceAccess.filesystem.allowedPaths.join(", ") || "—"}
          </Scope>
          <Scope label="Filesystem (writable)">
            {policy.resourceAccess.filesystem.writablePaths.join(", ") || "—"}
          </Scope>
          <Scope label="Network (domains)">
            {policy.resourceAccess.network.allowedDomains.join(", ") || "—"}
          </Scope>
          <Scope label="Network (write)">
            {policy.resourceAccess.network.allowWrite ? "allowed" : "denied"}
          </Scope>
          <Scope label="Shell (allowed)">
            {policy.resourceAccess.shell.allowedCommands.join(", ") || "—"}
          </Scope>
          <Scope label="Shell (denied)">
            {policy.resourceAccess.shell.deniedCommands.join(", ") || "—"}
          </Scope>
          <Scope label="Secrets">
            {policy.resourceAccess.secrets.access}
          </Scope>
          <Scope label="Worker approval">
            {policy.resourceAccess.workerApproval.required
              ? policy.resourceAccess.workerApproval.approvers.join(", ")
              : "not required"}
          </Scope>
        </dl>
      </CollapsibleSection>

      <CollapsibleSection title="GitHub capabilities" defaultOpen>
        <ul className="flex flex-wrap gap-2">
          {policy.githubCapabilities.map((c) => (
            <li key={c}>
              <Badge className="border-slate-200 bg-slate-50 text-slate-700">{c}</Badge>
            </li>
          ))}
          {policy.githubCapabilities.length === 0 ? (
            <li className="text-xs text-slate-400">None</li>
          ) : null}
        </ul>
        <p className="mt-2 text-xs text-slate-400">
          merge_pr and push_main are independent toggles.
        </p>
      </CollapsibleSection>

      <CollapsibleSection title="Publication & deployment capabilities" defaultOpen>
        <ul className="flex flex-wrap gap-2">
          {policy.publicationCapabilities.map((c) => (
            <li key={c}>
              <Badge className="border-slate-200 bg-slate-50 text-slate-700">{c}</Badge>
            </li>
          ))}
          {policy.publicationCapabilities.length === 0 ? (
            <li className="text-xs text-slate-400">None</li>
          ) : null}
        </ul>
        <dl className="mt-3 space-y-2 text-sm">
          <Scope label="Artifacts/packages">
            {policy.publicationPolicy.allowedArtifactOrPackage.join(", ") || "—"}
          </Scope>
          <Scope label="Registry">
            {policy.publicationPolicy.allowedRegistry.join(", ") || "—"}
          </Scope>
          <Scope label="Repository">
            {policy.publicationPolicy.allowedRepository.join(", ") || "—"}
          </Scope>
          <Scope label="Environments">
            {policy.publicationPolicy.allowedEnvironment.join(", ") || "—"}
          </Scope>
          <Scope label="Rollback strategy">
            {policy.publicationPolicy.rollbackStrategy ?? "—"}
          </Scope>
        </dl>
        <p className="mt-2 text-xs text-slate-400">
          Deployment is not implied by network write access.
        </p>
      </CollapsibleSection>

      <CollapsibleSection title="Autonomous window" defaultOpen>
        <dl className="space-y-2 text-sm">
          <Scope label="Enabled">
            {policy.autonomousWindow.enabled ? "yes" : "no"}
          </Scope>
          <Scope label="Starts at">{policy.autonomousWindow.startsAt}</Scope>
          <Scope label="Expires at">{policy.autonomousWindow.expiresAt}</Scope>
          <Scope label="Max PRs opened">
            {String(policy.autonomousWindow.maxPrsOpened)}
          </Scope>
          <Scope label="Max merges to main">
            {String(policy.autonomousWindow.maxMergesToMain)}
          </Scope>
          <Scope label="Max releases">
            {String(policy.autonomousWindow.maxReleasesCreated)}
          </Scope>
          <Scope label="Max deploys">
            {String(policy.autonomousWindow.maxDeploysToEnvironment)}
          </Scope>
          <Scope label="Stop conditions">
            {policy.autonomousWindow.stopConditions
              .map((s) => s.type)
              .join(", ") || "—"}
          </Scope>
        </dl>
      </CollapsibleSection>
    </div>
  );
}

function Scope({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="text-slate-700">{children}</dd>
    </div>
  );
}
