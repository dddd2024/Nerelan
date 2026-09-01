import type { MouseEvent, ReactNode } from "react";
import { cn } from "@/lib/cn";
import {
  sidebarHeaderRowClassName,
  sidebarNavListClassName,
} from "./sidebar-layout";

interface AgentCanvasSidebarFrameProps {
  collapsed: boolean;
  onExpand: () => void;
  logo: ReactNode;
  collapseToggle: ReactNode;
  primaryActions: ReactNode;
  navigation: ReactNode;
  footer?: ReactNode;
}

/**
 * Bounded slot adapter directly derived from Agent Canvas v1.6.1 Sidebar and
 * SidebarRailBody markup. OpenHands settings, navigation, backend registry,
 * health, modal, and conversation-store dependencies are replaced by slots.
 */
export function AgentCanvasSidebarFrame({
  collapsed,
  onExpand,
  logo,
  collapseToggle,
  primaryActions,
  navigation,
  footer,
}: AgentCanvasSidebarFrameProps) {
  const handleCollapsedRailClick = (event: MouseEvent<HTMLElement>) => {
    if (!collapsed) return;
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    if (target.closest("a,button,input,textarea,select,[role='button'],[role='link']")) {
      return;
    }
    onExpand();
  };

  return (
    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions, jsx-a11y/click-events-have-key-events -- matches the upstream empty-space collapsed-rail hit area; explicit controls retain keyboard behavior.
    <aside
      aria-label="导航"
      data-testid="sidebar"
      data-collapsed={String(collapsed)}
      data-agent-canvas-source="v1.6.1"
      data-presentation-boundary="slot-adapter"
      onClick={handleCollapsedRailClick}
      className={cn(
        "max-md:hidden flex bg-ra-base flex-col min-h-0 h-screen",
        "border-r border-[var(--oh-border)] transition-[width,min-width] duration-200",
        collapsed
          ? "w-[60px] min-w-[60px] px-2.5 sidebar-collapsed"
          : "w-[232px] min-w-[232px] pb-2 pl-2.5 pr-0 sidebar-expanded",
      )}
    >
      <div className="flex min-h-0 flex-1 flex-col items-stretch pt-2">
        <div className={sidebarHeaderRowClassName(collapsed)}>
          <div className="min-w-0 flex-1">{logo}</div>
          {collapseToggle}
        </div>

        <div className={cn(sidebarNavListClassName(collapsed), "mt-3")}>
          {primaryActions}
        </div>

        <nav
          aria-label="任务与项目"
          className={cn(
            sidebarNavListClassName(collapsed),
            "mt-3 min-h-0 flex-1 overflow-y-auto custom-scrollbar",
          )}
        >
          {navigation}
        </nav>

        {footer ? (
          <div
            className={cn(
              sidebarNavListClassName(collapsed),
              "mt-auto border-t border-[var(--oh-border)] pt-2 pb-2",
            )}
          >
            {footer}
          </div>
        ) : null}
      </div>
    </aside>
  );
}
