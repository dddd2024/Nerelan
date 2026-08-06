import { cn } from "@/lib/cn";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  dot?: string;
}

/**
 * OpenHands-style badge.
 * Source: OpenHands ConversationCard uses inline status dots and badges
 * with rounded-full, border-based styling. License: MIT (inherited).
 */
export function Badge({ children, className, dot }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        "border-ra-border text-ra-text-secondary",
        className,
      )}
    >
      {dot ? (
        <span
          aria-hidden="true"
          className={cn("h-1.5 w-1.5 rounded-full", dot)}
        />
      ) : null}
      {children}
    </span>
  );
}
