import { cn } from "@/lib/cn";

interface DiffViewerProps {
  diff: string;
  className?: string;
  defaultExpanded?: boolean;
}

/**
 * OpenHands FileDiffViewer structural port (simplified).
 *
 * Upstream source:
 *   frontend/src/components/features/diff-viewer/file-diff-viewer.tsx
 *     (tag 1.8.0)
 *   - `bg-neutral-900` for diff editor background
 *   - green (#014b01AA) for insertions, red (#750000AA) for deletions
 *   - monospace font-mono
 *   - hunk headers, meta lines, context lines
 *
 * Structurally ported: same line classification (add/del/hunk/meta/ctx)
 * with OpenHands diff color scheme (green additions, red deletions,
 * amber hunk headers). No Monaco dependency — uses plain pre/monospace.
 *
 * Modifications: simplified to text-based diff viewer; no view-mode
 * toggle or file status icon (handled by ChangesPanel parent).
 * License: MIT (inherited from OpenHands)
 */
export function DiffViewer({ diff, className, defaultExpanded = false }: DiffViewerProps) {
  const lines = diff.split("\n");

  return (
    <pre
      className={cn(
        "overflow-x-auto rounded-md border border-ra-border bg-ra-input",
        "font-mono text-xs leading-5 text-ra-text-secondary",
        className,
      )}
      data-testid="diff-viewer"
      data-expanded={defaultExpanded ? "true" : "false"}
    >
      {lines.map((line, i) => {
        const kind = lineKind(line);
        return (
          <span
            key={i}
            className={cn(
              "block whitespace-pre",
              kind === "add" && "bg-[#014b01AA]/20 text-[#BCFF8C]",
              kind === "del" && "bg-[#750000AA]/20 text-ra-status-error",
              kind === "hunk" && "bg-[#525252]/30 text-[#FFD43B]",
              kind === "meta" && "text-ra-text-tertiary",
            )}
          >
            {line || " "}
          </span>
        );
      })}
    </pre>
  );
}

type LineKind = "add" | "del" | "hunk" | "meta" | "ctx";

function lineKind(line: string): LineKind {
  if (line.startsWith("+++") || line.startsWith("---")) return "meta";
  if (line.startsWith("+")) return "add";
  if (line.startsWith("-")) return "del";
  if (line.startsWith("@@")) return "hunk";
  return "ctx";
}
