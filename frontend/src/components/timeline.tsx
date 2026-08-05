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
 * Vertical timeline component for activity events.
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
                className="absolute left-[11px] top-6 h-full w-px bg-slate-200"
              />
            ) : null}
            <span
              aria-hidden="true"
              className={cn(
                "relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500",
                item.iconColor,
              )}
            >
              {item.icon}
            </span>
            <div className="min-w-0 flex-1 pt-0.5">
              <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                <div className="text-sm font-medium text-slate-800">
                  {item.title}
                </div>
                {item.meta ? (
                  <div className="text-xs text-slate-400">{item.meta}</div>
                ) : null}
              </div>
              {item.body ? (
                <div className="mt-1 text-sm text-slate-600">{item.body}</div>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
