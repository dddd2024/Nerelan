import { cn } from "@/lib/cn";

interface DiffViewerProps {
  diff: string;
  className?: string;
  defaultExpanded?: boolean;
}

/**
 * Display a unified file diff with simple added/removed line coloring.
 * No external syntax highlighter.
 */
export function DiffViewer({ diff, className, defaultExpanded = false }: DiffViewerProps) {
  const lines = diff.split("\n");

  return (
    <pre
      className={cn(
        "overflow-x-auto rounded-md border border-slate-200 bg-slate-50 p-3",
        "font-mono text-xs leading-5 text-slate-700",
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
              kind === "add" && "bg-emerald-50 text-emerald-800",
              kind === "del" && "bg-rose-50 text-rose-800",
              kind === "hunk" && "bg-sky-50 text-sky-800",
              kind === "meta" && "text-slate-400",
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
