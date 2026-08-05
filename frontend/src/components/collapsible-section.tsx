import { useId, useState, type ReactNode } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/cn";

interface CollapsibleSectionProps {
  title: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  summary?: ReactNode;
  icon?: ReactNode;
}

/**
 * Reusable collapsible panel with expand/collapse, keyboard accessible.
 */
export function CollapsibleSection({
  title,
  children,
  defaultOpen = false,
  summary,
  icon,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const reactId = useId();
  const buttonId = `cs-trigger-${reactId}`;
  const panelId = `cs-panel-${reactId}`;

  return (
    <section className="rounded-lg border border-slate-200 bg-white">
      <button
        id={buttonId}
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "flex w-full items-center gap-2 px-4 py-3 text-left",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-inset",
        )}
      >
        <ChevronRight
          aria-hidden="true"
          className={cn(
            "h-4 w-4 shrink-0 text-slate-400 transition-transform",
            open && "rotate-90",
          )}
        />
        {icon ? <span className="shrink-0 text-slate-500">{icon}</span> : null}
        <span className="flex-1 text-sm font-medium text-slate-800">{title}</span>
        {summary ? <span className="text-xs text-slate-500">{summary}</span> : null}
      </button>
      {open ? (
        <div
          id={panelId}
          role="region"
          aria-labelledby={buttonId}
          className="border-t border-slate-100 px-4 py-3"
        >
          {children}
        </div>
      ) : null}
    </section>
  );
}
