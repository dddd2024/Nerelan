import type { PolicyContract } from "@/types";
import { Badge } from "@/components/badge";
import { CollapsibleSection } from "@/components/collapsible-section";
import { summarizePolicy } from "@/lib/policy-summary";
import { permissionModeLabel } from "@/lib/format";

interface PermissionsPanelProps {
  policy: PolicyContract;
}

function Scope({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-ra-text-tertiary">{label}</dt>
      <dd className="text-ra-text-secondary">{children}</dd>
    </div>
  );
}

/**
 * OpenHands-style permissions/policy panel.
 *
 * Upstream reference:
 *   frontend/src/components/features/conversation/conversation-name.tsx
 *     context menu — nested collapsible sections (tag 1.8.0)
 *   frontend/src/components/features/chat/generic-event-message.tsx
 *     — collapsible details pattern
 *
 * Styled to match OpenHands dark panels with border-ra-border,
 * bg-ra-light, text-ra-text/secondary/tertiary.
 *
 * Modifications: reverse-agent PolicyContract type instead of
 * conversation settings; policy summary instead of model details.
 */
export function PermissionsPanel({ policy }: PermissionsPanelProps) {
  const summary = summarizePolicy(policy);
  return (
    <div data-testid="permissions-panel" className="space-y-3">
      <section className="rounded-lg border border-ra-border bg-ra-light p-4">
        <div className="flex items-center gap-2">
          <Badge>{permissionModeLabel(policy.mode)}</Badge>
          <span className="font-mono text-xs text-ra-text-tertiary">{policy.repository}</span>
        </div>
        <p className="mt-3 text-sm text-ra-text-secondary" data-testid="permissions-summary">
          {summary}
        </p>
      </section>

      <CollapsibleSection title="文件系统" defaultOpen>
        <dl className="space-y-3 text-sm">
          <Scope label="文件系统（已批准路径）">
            {policy.resourceAccess.filesystem.allowedPaths.join(", ") || "—"}
          </Scope>
          <Scope label="文件系统（可写路径）">
            {policy.resourceAccess.filesystem.writablePaths.join(", ") || "—"}
          </Scope>
          <Scope label="网络（域名）">
            {policy.resourceAccess.network.allowedDomains.join(", ") || "—"}
          </Scope>
          <Scope label="网络（写入）">
            {policy.resourceAccess.network.allowWrite ? "允许" : "拒绝"}
          </Scope>
          <Scope label="Shell（允许）">
            {policy.resourceAccess.shell.allowedCommands.join(", ") || "—"}
          </Scope>
          <Scope label="Shell（拒绝）">
            {policy.resourceAccess.shell.deniedCommands.join(", ") || "—"}
          </Scope>
          <Scope label="密钥">
            {policy.resourceAccess.secrets.access}
          </Scope>
          <Scope label="Worker 审批">
            {policy.resourceAccess.workerApproval.required
              ? policy.resourceAccess.workerApproval.approvers.join(", ")
              : "不需要"}
          </Scope>
        </dl>
      </CollapsibleSection>

      <CollapsibleSection title="GitHub 能力" defaultOpen>
        <ul className="flex flex-wrap gap-2">
          {policy.githubCapabilities.map((c) => (
            <li key={c}>
              <Badge className="border-ra-border bg-ra-tertiary text-ra-text-secondary">
                {c}
              </Badge>
            </li>
          ))}
          {policy.githubCapabilities.length === 0 ? (
            <li className="text-xs text-ra-text-tertiary">无</li>
          ) : null}
        </ul>
        <p className="mt-2 text-xs text-ra-text-tertiary">
          merge_pr 与 push_main 为独立开关。
        </p>
      </CollapsibleSection>

      <CollapsibleSection title="发布与部署能力" defaultOpen>
        <ul className="flex flex-wrap gap-2">
          {policy.publicationCapabilities.map((c) => (
            <li key={c}>
              <Badge className="border-ra-border bg-ra-tertiary text-ra-text-secondary">
                {c}
              </Badge>
            </li>
          ))}
          {policy.publicationCapabilities.length === 0 ? (
            <li className="text-xs text-ra-text-tertiary">无</li>
          ) : null}
        </ul>
        <dl className="mt-3 space-y-2 text-sm">
          <Scope label="制品/包">
            {policy.publicationPolicy.allowedArtifactOrPackage.join(", ") || "—"}
          </Scope>
          <Scope label="仓库">
            {policy.publicationPolicy.allowedRepository.join(", ") || "—"}
          </Scope>
          <Scope label="注册表">
            {policy.publicationPolicy.allowedRegistry.join(", ") || "—"}
          </Scope>
          <Scope label="环境">
            {policy.publicationPolicy.allowedEnvironment.join(", ") || "—"}
          </Scope>
          <Scope label="回滚策略">
            {policy.publicationPolicy.rollbackStrategy ?? "—"}
          </Scope>
        </dl>
        <p className="mt-2 text-xs text-ra-text-tertiary">
          网络写入权限不隐含部署能力。
        </p>
      </CollapsibleSection>

      <CollapsibleSection title="无人值守窗口" defaultOpen>
        <dl className="space-y-2 text-sm">
          <Scope label="已启用">
            {policy.autonomousWindow.enabled ? "是" : "否"}
          </Scope>
          <Scope label="开始时间">{policy.autonomousWindow.startsAt}</Scope>
          <Scope label="过期时间">{policy.autonomousWindow.expiresAt}</Scope>
          <Scope label="最大 PR 数">
            {String(policy.autonomousWindow.maxPrsOpened)}
          </Scope>
          <Scope label="最大合并数">
            {String(policy.autonomousWindow.maxMergesToMain)}
          </Scope>
          <Scope label="最大发布数">
            {String(policy.autonomousWindow.maxReleasesCreated)}
          </Scope>
          <Scope label="最大部署数">
            {String(policy.autonomousWindow.maxDeploysToEnvironment)}
          </Scope>
          <Scope label="停止条件">
            {policy.autonomousWindow.stopConditions
              .map((s) => s.type)
              .join(", ") || "—"}
          </Scope>
        </dl>
      </CollapsibleSection>
    </div>
  );
}
