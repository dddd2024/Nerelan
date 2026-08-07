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
 * OpenHands-style capabilities checkboxes.
 * Source: OpenHands capabilities/tools checkbox pattern (tag 1.8.0).
 * License: MIT (inherited from OpenHands)
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
                    ? "border-ra-accent/30 bg-ra-accent/10 text-ra-text"
                    : "border-ra-border text-ra-text-secondary",
                )}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggle(cap)}
                  aria-label={cap}
                  data-testid={`cap-${cap}`}
                  className="h-4 w-4 rounded border-ra-border text-ra-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
                />
                <span className="font-mono text-xs">{cap}</span>
                {isMerge || isPushMain ? (
                  <span className="ml-auto text-[10px] text-ra-text-tertiary">
                    独立
                  </span>
                ) : null}
              </label>
            </li>
          );
        })}
      </ul>
      <p className="text-xs text-ra-text-tertiary">
        merge_pr 与 push_main 为独立开关。启用 merge_pr 不会启用 push_main。
      </p>
    </div>
  );
}
