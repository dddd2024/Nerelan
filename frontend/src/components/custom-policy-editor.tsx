import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import type { MergeMethod, PolicyContract } from "@/types";
import { ResourceAccessEditor } from "@/components/resource-access-editor";
import { GithubCapabilitiesEditor } from "@/components/github-capabilities-editor";
import { PublicationEditor } from "@/components/publication-editor";
import { AutonomousWindowEditor } from "@/components/autonomous-window-editor";
import { AuthorizationSummary } from "@/components/authorization-summary";
import { CollapsibleSection } from "@/components/collapsible-section";
import { cn } from "@/lib/cn";

const MERGE_METHODS: MergeMethod[] = ["merge", "squash", "rebase"];

interface CustomPolicyEditorProps {
  open: boolean;
  policy: PolicyContract;
  onChange: (next: PolicyContract) => void;
  onClose: () => void;
}

/**
 * Modal/drawer with sections for resource access, GitHub capabilities,
 * publication/deployment capabilities, autonomous window, merge policy.
 * All fields independently configurable. Focus is trapped while open.
 */
export function CustomPolicyEditor({
  open,
  policy,
  onChange,
  onClose,
}: CustomPolicyEditorProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  const update = (patch: Partial<PolicyContract>) => onChange({ ...policy, ...patch });

  useEffect(() => {
    if (!open) return;
    previouslyFocused.current = document.activeElement as HTMLElement | null;
    const node = dialogRef.current;
    // Focus first focusable element.
    const focusable = node?.querySelector<HTMLElement>(
      "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])",
    );
    focusable?.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Tab" || !node) return;
      const items = Array.from(
        node.querySelectorAll<HTMLElement>(
          "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])",
        ),
      ).filter((el) => !el.hasAttribute("disabled"));
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      previouslyFocused.current?.focus?.();
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex"
      role="dialog"
      aria-modal="true"
      aria-label="自定义策略编辑器"
      data-testid="custom-policy-editor"
    >
      <button
        type="button"
        aria-label="关闭编辑器"
        tabIndex={-1}
        onClick={onClose}
        className="absolute inset-0 bg-slate-900/30"
      />
      <div
        ref={dialogRef}
        className={cn(
          "relative ml-auto h-full w-full max-w-2xl overflow-auto bg-white shadow-xl",
        )}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-100 bg-white px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-800">自定义策略</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="关闭"
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            <X aria-hidden="true" className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-3 p-4">
          <AuthorizationSummary policy={policy} />

          <CollapsibleSection title="合并策略" defaultOpen>
            <div className="space-y-2">
              <TextField
                label="允许的仓库（逗号分隔）"
                value={policy.mergePolicy.allowedRepositories.join(", ")}
                onChange={(v) =>
                  update({
                    mergePolicy: {
                      ...policy.mergePolicy,
                      allowedRepositories: splitList(v),
                    },
                  })
                }
              />
              <TextField
                label="允许的目标分支（逗号分隔）"
                value={policy.mergePolicy.allowedBaseBranches.join(", ")}
                onChange={(v) =>
                  update({
                    mergePolicy: {
                      ...policy.mergePolicy,
                      allowedBaseBranches: splitList(v),
                    },
                  })
                }
              />
              <TextField
                label="必需检查（逗号分隔）"
                value={policy.mergePolicy.requiredChecks.join(", ")}
                onChange={(v) =>
                  update({
                    mergePolicy: {
                      ...policy.mergePolicy,
                      requiredChecks: splitList(v),
                    },
                  })
                }
              />
              <fieldset>
                <legend className="text-xs text-slate-500">允许的合并方式</legend>
                <div className="mt-1 flex flex-wrap gap-3">
                  {MERGE_METHODS.map((m) => {
                    const checked = policy.mergePolicy.allowedMergeMethods.includes(m);
                    return (
                      <label key={m} className="flex items-center gap-1 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleMergeMethod(policy, update, m)}
                          aria-label={m}
                          className="h-4 w-4 rounded border-slate-300 text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                        />
                        <span className="font-mono text-xs">{m}</span>
                      </label>
                    );
                  })}
                </div>
              </fieldset>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={policy.mergePolicy.requireExactHead}
                  onChange={(e) =>
                    update({
                      mergePolicy: {
                        ...policy.mergePolicy,
                        requireExactHead: e.target.checked,
                      },
                    })
                  }
                  className="h-4 w-4 rounded border-slate-300 text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                />
                要求精确 Head
              </label>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="文件系统" defaultOpen>
            <ResourceAccessEditor
              value={policy.resourceAccess}
              onChange={(next) => update({ resourceAccess: next })}
            />
          </CollapsibleSection>

          <CollapsibleSection title="GitHub 能力" defaultOpen>
            <GithubCapabilitiesEditor
              value={policy.githubCapabilities}
              onChange={(next) => update({ githubCapabilities: next })}
            />
          </CollapsibleSection>

          <CollapsibleSection title="发布与部署" defaultOpen>
            <PublicationEditor
              capabilities={policy.publicationCapabilities}
              onCapabilitiesChange={(next) => update({ publicationCapabilities: next })}
              policy={policy.publicationPolicy}
              onPolicyChange={(next) => update({ publicationPolicy: next })}
            />
          </CollapsibleSection>

          <CollapsibleSection title="无人值守窗口" defaultOpen>
            <AutonomousWindowEditor
              value={policy.autonomousWindow}
              onChange={(next) => update({ autonomousWindow: next })}
            />
          </CollapsibleSection>
        </div>
      </div>
    </div>
  );
}

function splitList(v: string): string[] {
  return v.split(",").map((s) => s.trim()).filter(Boolean);
}

function toggleMergeMethod(
  policy: PolicyContract,
  update: (patch: Partial<PolicyContract>) => void,
  m: MergeMethod,
) {
  const list = policy.mergePolicy.allowedMergeMethods;
  const next = list.includes(m)
    ? list.filter((x) => x !== m)
    : [...list, m];
  update({ mergePolicy: { ...policy.mergePolicy, allowedMergeMethods: next } });
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
      <span className="text-xs text-slate-500">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
      />
    </label>
  );
}
