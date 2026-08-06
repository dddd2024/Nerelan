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
  { label: string; icon: typeof FilePlus; color: string }
> = {
  added: { label: "新增", icon: FilePlus, color: "text-emerald-600" },
  modified: { label: "修改", icon: FileEdit, color: "text-sky-600" },
  deleted: { label: "删除", icon: FileMinus, color: "text-rose-600" },
  renamed: { label: "重命名", icon: FileOutput, color: "text-violet-600" },
};

export function ChangesPanel({ changes }: ChangesPanelProps) {
  const [open, setOpen] = useState<Record<string, boolean>>({});

  if (changes.length === 0) {
    return (
      <p className="text-sm text-slate-500" data-testid="changes-empty">
        暂无文件变更。
      </p>
    );
  }

  const totalAdd = changes.reduce((s, c) => s + c.additions, 0);
  const totalDel = changes.reduce((s, c) => s + c.deletions, 0);

  return (
    <div data-testid="changes-panel" className="space-y-2">
      <div className="flex items-center gap-3 text-xs text-slate-500">
        <span>{changes.length} 个文件</span>
        <span className="text-emerald-600">+{totalAdd}</span>
        <span className="text-rose-600">-{totalDel}</span>
      </div>
      <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
        {changes.map((c) => {
          const meta = STATUS_META[c.status];
          const Icon = meta.icon;
          const isOpen = open[c.path] ?? false;
          return (
            <li key={c.path}>
              <button
                type="button"
                aria-expanded={isOpen}
                aria-controls={`diff-${c.path}`}
                onClick={() => setOpen((p) => ({ ...p, [c.path]: !p[c.path] }))}
                className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-inset"
                data-testid={`changes-file-${c.path}`}
              >
                <Icon aria-hidden="true" className={cn("h-4 w-4 shrink-0", meta.color)} />
                <span className="flex-1 truncate font-mono text-xs text-slate-800">
                  {c.path}
                </span>
                <span className="text-xs text-emerald-600">+{c.additions}</span>
                <span className="text-xs text-rose-600">-{c.deletions}</span>
                <ChevronDown
                  aria-hidden="true"
                  className={cn(
                    "h-4 w-4 text-slate-400 transition-transform",
                    isOpen && "rotate-180",
                  )}
                />
              </button>
              {isOpen ? (
                <div id={`diff-${c.path}`} className="border-t border-slate-100 p-3">
                  <DiffViewer diff={c.diff} />
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
