import { useState } from "react";
import { FilePlus, FileEdit, FileMinus, FileOutput, ChevronDown } from "lucide-react";
import type { ChangedFile } from "@/types";
import { cn } from "@/lib/cn";
import { DiffViewer } from "@/components/diff-viewer";

interface ChangesPanelProps {
  changes: ChangedFile[];
}

const STATUS_META: Record<
  ChangedFile["status"],
  { label: string; icon: React.ComponentType<React.SVGProps<SVGSVGElement>>; color: string }
> = {
  added: { label: "新增", icon: FilePlus, color: "text-[#BCFF8C]" },
  modified: { label: "修改", icon: FileEdit, color: "text-[#FFD43B]" },
  deleted: { label: "删除", icon: FileMinus, color: "text-ra-status-error" },
  renamed: { label: "重命名", icon: FileOutput, color: "text-[#A3A3A3]" },
};

/**
 * OpenHands ChangesTab / GitChanges adaptation.
 *
 * Upstream sources:
 *   frontend/src/routes/changes-tab.tsx (tag 1.8.0)
 *   — `flex flex-col items-center justify-center h-full
 *      text-tertiary-light` for status messages
 *   frontend/src/components/features/diff-viewer/file-diff-viewer.tsx
 *     (tag 1.8.0)
 *   — `border border-neutral-600 rounded-xl`, collapsible with chevron
 *   - status icon + path + expand/collapse chevron
 *   frontend/src/components/features/diff-viewer/empty-changes-message.tsx
 *   — icon + muted text center message
 *
 * Structurally ported: file list with border-b separators, status icon,
 * path, additions/deletions, and collapsible diff viewer. Dark panel
 * background (#1f2228 workspace bg) with border-ra-border.
 *
 * Modifications: reverse-agent ChangedFile type; simple pre-based diff
 * viewer instead of Monaco Editor (no external dependency).
 * License: MIT (inherited from OpenHands)
 */
export function ChangesPanel({ changes }: ChangesPanelProps) {
  const [open, setOpen] = useState<Record<string, boolean>>({});

  if (changes.length === 0) {
    return (
      <div
        className="flex flex-col items-center justify-center h-full p-6 gap-3 text-center"
        data-testid="changes-empty"
      >
        <FileOutput className="h-8 w-8 text-ra-text-tertiary" />
        <p className="text-sm text-ra-text-secondary">暂无文件变更。</p>
      </div>
    );
  }

  const totalAdd = changes.reduce((s, c) => s + c.additions, 0);
  const totalDel = changes.reduce((s, c) => s + c.deletions, 0);

  return (
    <div data-testid="changes-panel" className="space-y-2">
      <div className="flex items-center gap-3 text-xs text-ra-text-tertiary">
        <span>{changes.length} 个文件</span>
        <span className="text-[#BCFF8C]">+{totalAdd}</span>
        <span className="text-ra-status-error">-{totalDel}</span>
      </div>

      <div className="divide-y divide-ra-border rounded-xl border border-ra-border overflow-hidden">
        {changes.map((c) => {
          const meta = STATUS_META[c.status];
          const Icon = meta.icon;
          const isOpen = open[c.path] ?? false;
          return (
            <div key={c.path} className="flex flex-col">
              <button
                type="button"
                aria-expanded={isOpen}
                aria-controls={`diff-${c.path}`}
                onClick={() =>
                  setOpen((p) => ({ ...p, [c.path]: !p[c.path] }))
                }
                className={cn(
                  "flex w-full items-center gap-2 px-3 py-2 text-left",
                  "text-ra-text-secondary hover:bg-ra-tertiary",
                  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent focus-visible:ring-inset",
                )}
                data-testid={`changes-file-${c.path}`}
              >
                <Icon
                  aria-hidden="true"
                  className={cn("h-4 w-4 shrink-0", meta.color)}
                />
                <span className="flex-1 truncate font-mono text-xs text-ra-text-secondary">
                  {c.path}
                </span>
                <span className="text-xs text-[#BCFF8C]">+{c.additions}</span>
                <span className="text-xs text-ra-status-error">
                  -{c.deletions}
                </span>
                <ChevronDown
                  aria-hidden="true"
                  className={cn(
                    "h-4 w-4 text-ra-text-tertiary transition-transform",
                    isOpen && "rotate-180",
                  )}
                />
              </button>
              {isOpen ? (
                <div
                  id={`diff-${c.path}`}
                  className="border-t border-ra-border p-3"
                >
                  <DiffViewer diff={c.diff} />
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}
