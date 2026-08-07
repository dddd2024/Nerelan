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
 * OpenHands-style collapsible section.
 *
 * Upstream reference:
 *   frontend/src/components/features/chat/generic-event-message.tsx
 *     (tag 1.8.0) — expandable chevron pattern with border-l accent
 *   frontend/src/components/features/chat/model-messages.tsx
 *     — collapsible profile rows
 *
 * Styled to match OpenHands dark panel borders and text colors.
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
    <section className="rounded-lg border border-ra-border bg-ra-light">
      <button
        id={buttonId}
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "flex w-full items-center gap-2 px-4 py-3 text-left",
          "text-ra-text-secondary hover:text-ra-text",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent focus-visible:ring-inset",
        )}
      >
        <ChevronRight
          aria-hidden="true"
          className={cn(
            "h-4 w-4 shrink-0 text-ra-text-tertiary transition-transform",
            open && "rotate-90",
          )}
        />
        {icon ? <span className="shrink-0 text-ra-text-secondary">{icon}</span> : null}
        <span className="flex-1 text-sm font-medium text-ra-text-secondary">
          {title}
        </span>
        {summary ? <span className="text-xs text-ra-text-tertiary">{summary}</span> : null}
      </button>
      {open ? (
        <div
          id={panelId}
          role="region"
          aria-labelledby={buttonId}
          className="border-t border-ra-border px-4 py-3"
        >
          {children}
        </div>
      ) : null}
    </section>
  );
}
