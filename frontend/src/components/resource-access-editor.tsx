import type { PolicyContract, ResourceAccess } from "@/types";
import { cn } from "@/lib/cn";

interface ResourceAccessEditorProps {
  value: ResourceAccess;
  onChange: (next: ResourceAccess) => void;
}

/**
 * Fields for filesystem, network, shell, secrets, worker_approval.
 */
export function ResourceAccessEditor({ value, onChange }: ResourceAccessEditorProps) {
  const update = (patch: Partial<ResourceAccess>) => onChange({ ...value, ...patch });

  return (
    <div data-testid="resource-access-editor" className="space-y-4">
      <Group label="Filesystem">
        <TextField
          label="Allowed paths (comma-separated)"
          value={value.filesystem.allowedPaths.join(", ")}
          onChange={(v) =>
            update({
              filesystem: { ...value.filesystem, allowedPaths: splitList(v) },
            })
          }
        />
        <TextField
          label="Writable paths (comma-separated)"
          value={value.filesystem.writablePaths.join(", ")}
          onChange={(v) =>
            update({
              filesystem: { ...value.filesystem, writablePaths: splitList(v) },
            })
          }
        />
      </Group>

      <Group label="Network">
        <TextField
          label="Allowed domains (comma-separated)"
          value={value.network.allowedDomains.join(", ")}
          onChange={(v) =>
            update({ network: { ...value.network, allowedDomains: splitList(v) } })
          }
        />
        <Toggle
          label="Allow network write"
          checked={value.network.allowWrite}
          onChange={(b) => update({ network: { ...value.network, allowWrite: b } })}
        />
      </Group>

      <Group label="Shell">
        <TextField
          label="Allowed commands (comma-separated)"
          value={value.shell.allowedCommands.join(", ")}
          onChange={(v) =>
            update({ shell: { ...value.shell, allowedCommands: splitList(v) } })
          }
        />
        <TextField
          label="Denied commands (comma-separated)"
          value={value.shell.deniedCommands.join(", ")}
          onChange={(v) =>
            update({ shell: { ...value.shell, deniedCommands: splitList(v) } })
          }
        />
      </Group>

      <Group label="Secrets">
        <label htmlFor="secrets-access" className="block text-xs text-slate-500">
          Secrets access
        </label>
        <select
          id="secrets-access"
          aria-label="Secrets access"
          value={value.secrets.access}
          onChange={(e) =>
            update({
              secrets: {
                ...value.secrets,
                access: e.target.value as PolicyContract["resourceAccess"]["secrets"]["access"],
              },
            })
          }
          className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        >
          <option value="none">none</option>
          <option value="masked">masked</option>
          <option value="raw_values">raw_values (rejected)</option>
        </select>
        <TextField
          label="Allowed keys (comma-separated)"
          value={value.secrets.allowedKeys.join(", ")}
          onChange={(v) =>
            update({ secrets: { ...value.secrets, allowedKeys: splitList(v) } })
          }
        />
      </Group>

      <Group label="Worker approval">
        <Toggle
          label="Approval required"
          checked={value.workerApproval.required}
          onChange={(b) =>
            update({ workerApproval: { ...value.workerApproval, required: b } })
          }
        />
        <TextField
          label="Approvers (comma-separated)"
          value={value.workerApproval.approvers.join(", ")}
          onChange={(v) =>
            update({
              workerApproval: { ...value.workerApproval, approvers: splitList(v) },
            })
          }
        />
      </Group>
    </div>
  );
}

function splitList(v: string): string[] {
  return v
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function Group({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <fieldset className="rounded-md border border-slate-100 p-3">
      <legend className="px-1 text-xs font-medium text-slate-500">{label}</legend>
      <div className="space-y-2">{children}</div>
    </fieldset>
  );
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
        className={cn(
          "mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400",
        )}
      />
    </label>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (b: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 rounded border-slate-300 text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
      />
      <span className="text-sm text-slate-700">{label}</span>
    </label>
  );
}
