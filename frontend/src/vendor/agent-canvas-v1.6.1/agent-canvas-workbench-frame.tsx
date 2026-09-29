import type { ReactNode, RefObject } from "react";
import { cn } from "@/lib/cn";

interface AgentCanvasWorkbenchFrameProps {
  containerRef: RefObject<HTMLDivElement | null>;
  leftWidth: number;
  isDragging: boolean;
  primaryHeader: ReactNode;
  primaryPane: ReactNode;
  resizeHandle: ReactNode;
  secondaryTabs: ReactNode;
  secondaryPane: ReactNode;
  /*
   * Local addition. The upstream adapter hardcoded the two region labels in
   * English, which leaked English into an otherwise Chinese product surface
   * for screen-reader users. Callers can now supply localized labels; the
   * upstream defaults are preserved so the slot adapter stays reusable.
   */
  primaryLabel?: string;
  secondaryLabel?: string;
}

/**
 * Bounded slot adapter directly derived from Agent Canvas v1.6.1
 * ConversationMain. Chat/conversation/backend state is replaced by
 * reverse-agent-neutral header, primary-pane, tab, and secondary-pane slots.
 */
export function AgentCanvasWorkbenchFrame({
  containerRef,
  leftWidth,
  isDragging,
  primaryHeader,
  primaryPane,
  resizeHandle,
  secondaryTabs,
  secondaryPane,
  primaryLabel = "Activity",
  secondaryLabel = "Task workbench",
}: AgentCanvasWorkbenchFrameProps) {
  return (
    <div className="h-full min-h-0 flex flex-col overflow-hidden">
      <div
        ref={containerRef}
        data-testid="desktop-split-container"
        data-agent-canvas-source="v1.6.1"
        data-presentation-boundary="slot-adapter"
        className="flex flex-1 overflow-hidden transition-all duration-300 ease-in-out"
        style={{ transitionProperty: isDragging ? "none" : "all" }}
      >
        <section
          id="desktop-left-panel"
          data-testid="desktop-left-panel"
          aria-label={primaryLabel}
          className="flex flex-col bg-[var(--oh-surface)] overflow-hidden transition-all duration-300 ease-in-out"
          style={{
            width: `${leftWidth}%`,
            transitionProperty: isDragging ? "none" : "all",
          }}
        >
          <div className="flex h-10 min-h-10 shrink-0 items-center border-b border-[var(--oh-border)] px-3">
            {primaryHeader}
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-4">
            {primaryPane}
          </div>
        </section>

        {resizeHandle}

        <section
          id="desktop-right-panel"
          data-testid="desktop-right-panel"
          aria-label={secondaryLabel}
          className={cn(
            "flex flex-col overflow-hidden bg-[var(--oh-surface-raised)]",
            "border-l border-[var(--oh-border)] transition-all duration-300 ease-in-out",
          )}
          style={{
            width: `${100 - leftWidth}%`,
            minWidth: "240px",
            transitionProperty: isDragging ? "none" : "all",
          }}
        >
          <div className="flex shrink-0 flex-col border-b border-[var(--oh-border)]">
            {secondaryTabs}
          </div>
          <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
            {secondaryPane}
          </div>
        </section>
      </div>
    </div>
  );
}
