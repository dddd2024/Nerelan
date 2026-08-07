import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

interface TimelineItem {
  id: string;
  icon?: ReactNode;
  iconColor?: string;
  title: ReactNode;
  meta?: ReactNode;
  body?: ReactNode;
}

interface TimelineProps {
  items: TimelineItem[];
}

/**
 * OpenHands GenericEventMessage / Message structural port.
 *
 * Upstream sources:
 *   frontend/src/components/features/chat/generic-event-message.tsx
 *     (tag 1.8.0)
 *   - `border-l-2 pl-2 my-2 py-2 border-neutral-300 text-sm w-full`
 *   - title row: `flex items-center justify-between font-bold
 *     text-neutral-300`
 *   - expandable chevron: angle-down/angle-up SVGs
 *   frontend/src/components/features/chat/model-messages.tsx
 *   - collapsible event message pattern
 *
 * Structurally ported: vertical timeline with border-l accent,
 * title row, meta timestamp, and collapsible body. Icon dot uses
 * OpenHands neutral-300 color. Line styling matches OpenHands
 * event message borders.
 *
 * Modifications: activity events replace agent observations;
 * raw log expansion replaces markdown body.
 */
export function Timeline({ items }: TimelineProps) {
  return (
    <ol className="relative" data-testid="timeline">
      {items.map((item, i) => {
        const last = i === items.length - 1;
        return (
          <li key={item.id} className="relative flex gap-3 pb-5 last:pb-0">
            {!last ? (
              <span
                aria-hidden="true"
                className="absolute left-[11px] top-6 h-full w-px bg-ra-border"
              />
            ) : null}
            <span
              aria-hidden="true"
              className={cn(
                "relative z-10 flex h-6 w-6 shrink-0 items-center justify-center",
                "rounded-full border border-ra-border-strong bg-ra-light",
                item.iconColor,
              )}
            >
              {item.icon}
            </span>
            <div className="min-w-0 flex-1 pt-0.5">
              <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                <div className="text-sm font-medium text-ra-text-secondary">
                  {item.title}
                </div>
                {item.meta ? (
                  <div className="text-xs text-ra-text-tertiary">{item.meta}</div>
                ) : null}
              </div>
              {item.body ? (
                <div className="mt-1 text-sm text-ra-text-secondary">{item.body}</div>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
