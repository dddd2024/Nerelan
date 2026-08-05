import { cn } from "@/lib/cn";

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  dot?: string;
}

/**
 * Reusable badge. Accepts pre-computed Tailwind classes via className and an
 * optional dot color class.
 */
export function Badge({ children, className, dot }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        "border-slate-200 bg-slate-50 text-slate-700",
        className,
      )}
    >
      {dot ? (
        <span aria-hidden="true" className={cn("h-1.5 w-1.5 rounded-full", dot)} />
      ) : null}
      {children}
    </span>
  );
}
