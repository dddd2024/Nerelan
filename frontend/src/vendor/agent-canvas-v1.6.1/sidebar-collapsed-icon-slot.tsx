import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import {
  SIDEBAR_COLLAPSED_ICON_SLOT_CLASS,
  sidebarCollapsedIconBgClassName,
  sidebarCollapsedIconGlyphClassName,
} from "./sidebar-layout";

interface SidebarCollapsedIconSlotProps {
  active: boolean;
  className?: string;
  children: ReactNode;
}

/**
 * Direct source fork of Agent Canvas v1.6.1 SidebarCollapsedIconSlot.
 * Upstream: src/components/features/sidebar/sidebar-collapsed-icon-slot.tsx
 */
export function SidebarCollapsedIconSlot({
  active,
  className,
  children,
}: SidebarCollapsedIconSlotProps) {
  return (
    <span className={cn(SIDEBAR_COLLAPSED_ICON_SLOT_CLASS, className)}>
      <span aria-hidden className={sidebarCollapsedIconBgClassName(active)} />
      <span className={sidebarCollapsedIconGlyphClassName(active)}>
        {children}
      </span>
    </span>
  );
}
