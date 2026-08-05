import type { GithubCapability } from "@/types";
import { cn } from "@/lib/cn";

const ALL_CAPS: GithubCapability[] = [
  "read_repository",
  "create_issue",
  "update_issue",
  "create_branch",
  "push_task_branch",
  "open_draft_pr",
  "mark_ready",
  "request_review",
  "merge_pr",
  "delete_merged_branch",
  "push_main",
];

interface GithubCapabilitiesEditorProps {
  value: GithubCapability[];
  onChange: (next: GithubCapability[]) => void;
}

/**
 * Checkboxes for 11 GitHub capabilities. merge_pr and push_main are
 * independent toggles.
 */
export function GithubCapabilitiesEditor({
  value,
  onChange,
}: GithubCapabilitiesEditorProps) {
  const toggle = (cap: GithubCapability) => {
    if (value.includes(cap)) {
      onChange(value.filter((c) => c !== cap));
    } else {
      onChange([...value, cap]);
    }
  };

  return (
    <div data-testid="github-capabilities-editor" className="space-y-2">
      <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {ALL_CAPS.map((cap) => {
          const checked = value.includes(cap);
          const isMerge = cap === "merge_pr";
          const isPushMain = cap === "push_main";
          return (
            <li key={cap}>
              <label
                className={cn(
                  "flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm",
                  checked
                    ? "border-slate-300 bg-slate-50 text-slate-800"
                    : "border-slate-100 text-slate-600",
                )}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggle(cap)}
                  aria-label={cap}
                  data-testid={`cap-${cap}`}
                  className="h-4 w-4 rounded border-slate-300 text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                />
                <span className="font-mono text-xs">{cap}</span>
                {isMerge || isPushMain ? (
                  <span className="ml-auto text-[10px] text-slate-400">
                    independent
                  </span>
                ) : null}
              </label>
            </li>
          );
        })}
      </ul>
      <p className="text-xs text-slate-400">
        merge_pr and push_main are independent toggles. Enabling merge_pr does
        not enable push_main.
      </p>
    </div>
  );
}
