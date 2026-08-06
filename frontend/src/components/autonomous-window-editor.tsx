import type { AutonomousWindow, StopCondition, StopConditionRule } from "@/types";
import { cn } from "@/lib/cn";

const ALL_STOP: StopCondition[] = [
  "max_prs_opened",
  "max_merges_to_main",
  "max_releases_created",
  "max_deploys_to_environment",
  "budget_exhausted",
  "window_expired",
  "manual_stop",
  "blocking_review_thread",
  "ci_failure_on_head",
  "main_drift_detected",
  "authority_revoked",
];

interface AutonomousWindowEditorProps {
  value: AutonomousWindow;
  onChange: (next: AutonomousWindow) => void;
}

export function AutonomousWindowEditor({ value, onChange }: AutonomousWindowEditorProps) {
  const update = (patch: Partial<AutonomousWindow>) => onChange({ ...value, ...patch });

  const toggleStop = (sc: StopCondition) => {
    const exists = value.stopConditions.some((s) => s.type === sc);
    const next: StopConditionRule[] = exists
      ? value.stopConditions.filter((s) => s.type !== sc)
      : [...value.stopConditions, { type: sc, scope: "window" }];
    update({ stopConditions: next });
  };

  return (
    <div data-testid="autonomous-window-editor" className="space-y-3">
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={value.enabled}
          onChange={(e) => update({ enabled: e.target.checked })}
          aria-label="启用无人值守窗口"
          data-testid="aw-enabled"
          className="h-4 w-4 rounded border-slate-300 text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        />
        <span className="text-sm text-slate-700">启用无人值守窗口</span>
      </label>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <TextField
          label="开始时间（ISO）"
          value={value.startsAt}
          onChange={(v) => update({ startsAt: v })}
          testId="aw-startsAt"
        />
        <TextField
          label="过期时间（ISO）"
          value={value.expiresAt}
          onChange={(v) => update({ expiresAt: v })}
          testId="aw-expiresAt"
        />
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <NumberField label="最大 PR 数" value={value.maxPrsOpened} onChange={(n) => update({ maxPrsOpened: n })} />
        <NumberField label="最大合并数" value={value.maxMergesToMain} onChange={(n) => update({ maxMergesToMain: n })} />
        <NumberField label="最大发布数" value={value.maxReleasesCreated} onChange={(n) => update({ maxReleasesCreated: n })} />
        <NumberField label="最大部署数" value={value.maxDeploysToEnvironment} onChange={(n) => update({ maxDeploysToEnvironment: n })} />
      </div>
      <fieldset className="space-y-2 rounded-md border border-slate-100 p-3">
        <legend className="px-1 text-xs font-medium text-slate-500">
          停止条件
        </legend>
        <ul className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
          {ALL_STOP.map((sc) => {
            const checked = value.stopConditions.some((s) => s.type === sc);
            return (
              <li key={sc}>
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleStop(sc)}
                    aria-label={sc}
                    className="h-4 w-4 rounded border-slate-300 text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                  />
                  <span className="font-mono text-xs">{sc}</span>
                </label>
              </li>
            );
          })}
        </ul>
      </fieldset>
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
  testId,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  testId?: string;
}) {
  return (
    <label className="block">
      <span className="text-xs text-slate-500">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        data-testid={testId}
        className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
      />
    </label>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (n: number) => void;
}) {
  return (
    <label className="block">
      <span className="text-xs text-slate-500">{label}</span>
      <input
        type="number"
        min={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className={cn(
          "mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-sm",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400",
        )}
      />
    </label>
  );
}
