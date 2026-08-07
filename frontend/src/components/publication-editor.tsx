import type { PublicationCapability, PublicationPolicy } from "@/types";
import { cn } from "@/lib/cn";

const ALL_PUB: PublicationCapability[] = [
  "create_tag",
  "create_github_release",
  "publish_package",
  "publish_container",
  "deploy_preview",
  "deploy_staging",
  "deploy_production",
  "rollback_deployment",
];

interface PublicationEditorProps {
  capabilities: PublicationCapability[];
  onCapabilitiesChange: (next: PublicationCapability[]) => void;
  policy: PublicationPolicy;
  onPolicyChange: (next: PublicationPolicy) => void;
}

function splitList(v: string): string[] {
  return v.split(",").map((s) => s.trim()).filter(Boolean);
}

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-xs text-ra-text-tertiary">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "mt-1 w-full rounded-md border border-ra-border bg-ra-input px-3 py-1.5 text-sm text-ra-text",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
        )}
      />
    </label>
  );
}

/**
 * OpenHands-style publication capabilities editor.
 * Source: OpenHands capabilities/tools checkbox pattern (tag 1.8.0).
 * License: MIT (inherited from OpenHands)
 */
export function PublicationEditor({
  capabilities,
  onCapabilitiesChange,
  policy,
  onPolicyChange,
}: PublicationEditorProps) {
  const toggle = (cap: PublicationCapability) => {
    if (capabilities.includes(cap)) {
      onCapabilitiesChange(capabilities.filter((c) => c !== cap));
    } else {
      onCapabilitiesChange([...capabilities, cap]);
    }
  };

  const update = (patch: Partial<PublicationPolicy>) =>
    onPolicyChange({ ...policy, ...patch });

  return (
    <div data-testid="publication-editor" className="space-y-3">
      <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {ALL_PUB.map((cap) => {
          const checked = capabilities.includes(cap);
          return (
            <li key={cap}>
              <label
                className={cn(
                  "flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm",
                  checked
                    ? "border-ra-accent/30 bg-ra-accent/10 text-ra-text"
                    : "border-ra-border text-ra-text-secondary",
                )}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggle(cap)}
                  aria-label={cap}
                  data-testid={`pub-${cap}`}
                  className="h-4 w-4 rounded border-ra-border text-ra-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
                />
                <span className="font-mono text-xs">{cap}</span>
              </label>
            </li>
          );
        })}
      </ul>
      <p className="text-xs text-ra-text-tertiary">
        发布与部署能力相互独立。网络写入权限不隐含部署能力。
      </p>
      <fieldset className="space-y-2 rounded-md border border-ra-border p-3">
        <legend className="px-1 text-xs font-medium text-ra-text-tertiary">
          发布策略
        </legend>
        <TextField
          label="制品/包（逗号分隔）"
          value={policy.allowedArtifactOrPackage.join(", ")}
          onChange={(v) => update({ allowedArtifactOrPackage: splitList(v) })}
        />
        <TextField
          label="注册表（逗号分隔）"
          value={policy.allowedRegistry.join(", ")}
          onChange={(v) => update({ allowedRegistry: splitList(v) })}
        />
        <TextField
          label="仓库（逗号分隔）"
          value={policy.allowedRepository.join(", ")}
          onChange={(v) => update({ allowedRepository: splitList(v) })}
        />
        <TextField
          label="环境（逗号分隔）"
          value={policy.allowedEnvironment.join(", ")}
          onChange={(v) => update({ allowedEnvironment: splitList(v) })}
        />
        <TextField
          label="回滚策略"
          value={policy.rollbackStrategy ?? ""}
          onChange={(v) =>
            update({ rollbackStrategy: v || undefined })
          }
        />
      </fieldset>
    </div>
  );
}
