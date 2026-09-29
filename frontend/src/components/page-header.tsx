import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

interface PageHeaderProps {
  /** Page title. This is the single primary heading of the surface. */
  title: string;
  icon?: LucideIcon;
  /** One or two lines of orientation. Kept short on purpose. */
  description?: ReactNode;
  /** Optional contextual controls, aligned to the title baseline. */
  actions?: ReactNode;
  className?: string;
}

/**
 * Canonical page header for the primary workspace.
 *
 * Contract notes (`#448` §12 — visual-system rules):
 *
 * - **No kicker / eyebrow.** An earlier revision carried a small uppercase
 *   Latin label (`Roadmap`, `Human inbox`, …) above the title. It duplicated
 *   the title without adding information, it was applied to only four of the
 *   eight surfaces, and it mixed English into an otherwise Chinese product
 *   surface. Removing it satisfies "retain high information density while
 *   removing visual elements that do not add information".
 * - **One shared type scale.** Titles previously ranged from `text-3xl` to
 *   `text-3xl sm:text-4xl` with inconsistent letter-spacing. They now use the
 *   size already established by the Home detail title.
 * - The icon is supporting context, so it stays in the muted tone instead of
 *   competing with the title for weight.
 */
export function PageHeader({
  title,
  icon: Icon,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <header className={cn("mb-7 flex flex-wrap items-start justify-between gap-x-6 gap-y-3", className)}>
      <div className="min-w-0">
        <h1 className="flex items-center gap-2 text-[28px] font-medium leading-tight tracking-[-0.03em] text-ra-text sm:text-[32px]">
          {Icon ? <Icon className="h-6 w-6 shrink-0 text-ra-text-tertiary" aria-hidden="true" /> : null}
          <span className="min-w-0">{title}</span>
        </h1>
        {description ? (
          <p className="ra-measure mt-2.5 text-sm leading-6 text-ra-text-secondary">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

/**
 * Canonical shell for a top-level workspace surface: consistent background
 * token, horizontal padding and content measure.
 *
 * `#448` §13 targets a main horizontal padding of roughly 24–28px. The earlier
 * surfaces used 42–48px, which pushed content toward the middle and made the
 * workspace read as sparse rather than dense.
 */
export function PageSurface({
  children,
  className,
  measureClassName = "max-w-[1000px]",
  ...rest
}: {
  children: ReactNode;
  className?: string;
  measureClassName?: string;
} & React.HTMLAttributes<HTMLElement>) {
  return (
    <main
      className={cn("min-h-full bg-ra-workspace px-4 py-6 sm:px-6 lg:px-7 lg:py-8", className)}
      {...rest}
    >
      <div className={cn("mx-auto w-full", measureClassName)}>{children}</div>
    </main>
  );
}
