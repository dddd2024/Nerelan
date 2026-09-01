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
 * Compact semantic activity rows.
 *
 * The previous permanent rail and bordered circular node track duplicated
 * ordering that is already present in the event list. Ordering and disclosure
 * semantics remain unchanged; only the presentation is quieter and denser.
 */
export function Timeline({ items }: TimelineProps) {
  return (
    <ol className="divide-y divide-ra-border/50" data-testid="timeline">
      {items.map((item) => (
        <li key={item.id} className="flex gap-3 py-2.5 first:pt-0 last:pb-0">
          <span
            aria-hidden="true"
            className={cn(
              "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center",
              item.iconColor,
            )}
          >
            {item.icon}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
              <div className="text-sm font-medium text-ra-text-secondary">
                {item.title}
              </div>
              {item.meta ? (
                <div className="shrink-0 text-xs tabular-nums text-ra-text-tertiary">
                  {item.meta}
                </div>
              ) : null}
            </div>
            {item.body ? (
              <div className="mt-0.5 text-sm leading-5 text-ra-text-secondary">
                {item.body}
              </div>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
