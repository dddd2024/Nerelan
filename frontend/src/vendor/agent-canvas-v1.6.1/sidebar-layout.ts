import { cn } from "@/lib/cn";

/**
 * Direct source fork of Agent Canvas v1.6.1 sidebar layout primitives.
 *
 * Upstream: src/components/features/sidebar/sidebar-layout.ts
 * Adaptations: local cn import and reverse-agent-compatible color tokens.
 */
export const navInteractiveTransitionClassName =
  "transition-none motion-reduce:transition-none";

export const SIDEBAR_ICON_SLOT_CLASS =
  "flex h-[30px] w-[18px] shrink-0 items-center justify-center";

export const SIDEBAR_COLLAPSED_ICON_SLOT_CLASS =
  "relative h-[30px] min-h-[30px] max-h-[30px] w-full shrink-0";

export const SIDEBAR_HEADER_ROW_CLASS =
  "flex h-10 min-h-10 shrink-0 items-center gap-2 pl-2.5 pr-2.5 w-full";

export function sidebarHeaderRowClassName(collapsed: boolean): string {
  return cn(
    "flex h-10 min-h-10 shrink-0 items-center w-full",
    collapsed ? "px-0" : "gap-2 pl-2.5 pr-2.5",
  );
}

export const SIDEBAR_ROW_INTERACTIVE_CLASS = {
  active: "bg-ra-tertiary text-ra-text font-normal",
  idle: "text-[var(--oh-muted)] hover:text-ra-text hover:bg-[var(--oh-surface-raised)]",
} as const;

export function sidebarNavListClassName(collapsed: boolean): string {
  return cn(
    "flex flex-col gap-0.5 w-full shrink-0 items-stretch",
    !collapsed && "pr-2.5",
  );
}

export function sidebarNavRowClassName(options?: {
  indent?: boolean;
  collapsed?: boolean;
}): string {
  const { indent = false, collapsed = false } = options ?? {};
  return cn(
    "flex h-[30px] min-h-[30px] min-w-0 items-center rounded-md",
    navInteractiveTransitionClassName,
    "text-[13px] leading-4 w-full",
    collapsed
      ? "group gap-0 px-0 overflow-visible bg-transparent hover:bg-transparent"
      : "gap-2 px-2.5 overflow-hidden",
    indent && !collapsed && "pl-7",
  );
}

export function sidebarCollapsedIconBgClassName(active: boolean): string {
  return cn(
    "pointer-events-none absolute inset-0 z-0 rounded-md",
    navInteractiveTransitionClassName,
    active
      ? "bg-ra-tertiary"
      : "bg-transparent group-hover:bg-[var(--oh-surface-raised)]",
  );
}

export function sidebarCollapsedIconGlyphClassName(active: boolean): string {
  return cn(
    "relative z-[1] flex h-full w-full items-center justify-start pl-2.5 [&_svg]:shrink-0",
    active
      ? "text-ra-text font-normal"
      : "text-[var(--oh-muted)] group-hover:text-ra-text",
  );
}

export function sidebarNavLabelClassName(collapsed: boolean): string {
  return collapsed ? "sr-only" : "min-w-0 truncate";
}

export const SIDEBAR_ICON_BUTTON_CLASS = cn(
  "inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md",
  navInteractiveTransitionClassName,
  "cursor-pointer",
);

export const SIDEBAR_COLLAPSED_LOGO_WRAPPER_CLASS = cn(
  "relative hidden md:block shrink-0 overflow-visible",
  SIDEBAR_COLLAPSED_ICON_SLOT_CLASS,
);

export const SIDEBAR_COLLAPSE_TOGGLE_OVERLAY_CLASS = cn(
  "absolute left-1/2 top-1/2 hidden h-7 w-7 -translate-x-1/2 -translate-y-1/2 md:inline-flex",
  "items-center justify-center rounded-md",
  navInteractiveTransitionClassName,
  "cursor-pointer",
  "text-[var(--oh-muted)] hover:text-ra-text hover:bg-[var(--oh-surface-raised)]",
);
