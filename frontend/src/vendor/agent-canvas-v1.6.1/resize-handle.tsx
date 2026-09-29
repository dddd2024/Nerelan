import { useState, type KeyboardEvent, type MouseEvent } from "react";
import { cn } from "@/lib/cn";

interface ResizeHandleProps {
  onMouseDown: (event: MouseEvent<HTMLButtonElement>) => void;
  onKeyDown: (event: KeyboardEvent<HTMLDivElement>) => void;
  value: number;
  min: number;
  max: number;
  controls: string;
  className?: string;
  isDragging?: boolean;
}

/**
 * Direct source fork of Agent Canvas v1.6.1 ResizeHandle.
 *
 * Upstream: src/components/ui/resize-handle.tsx
 * Adaptations: local cn import plus the existing reverse-agent keyboard slider
 * semantics. The upstream zero-width frame, one-pixel line, hover state, and
 * drag-state highlight remain intact.
 *
 * Deliberate deviation from upstream: the drag target is widened from 12px to
 * 24px so it meets the 24px minimum target size. It is `position:absolute`,
 * centred on a `w-0` parent and fully transparent, so nothing moves and the
 * one-pixel line is unchanged - only the invisible grab area grows.
 *
 * Two further deviations, both recorded in the repo's own review findings:
 *
 * 1. The slider used to carry `focus:outline-none` while its only substitute
 *    was the one-pixel line itself. Because that utility outranks the global
 *    `:focus-visible` baseline in `index.css`, this control - the single
 *    keyboard-focusable element on the surface - opted out of the guaranteed
 *    2px accent outline and showed a 1px focus indicator instead. Dropping the
 *    utility lets it inherit the baseline, which is the documented contract.
 * 2. The active line was hard-coded `bg-white`, the same defect class the
 *    baseline commit fixed for `ring-white` call sites: white on the light
 *    workspace (near `#fffefa`) is invisible, so the hover/drag affordance
 *    simply did not exist in the light theme. `--ra-accent` is the token that
 *    holds at least 3:1 against every surface in both themes for all five
 *    accents, which is why the focus baseline uses it too.
 */
export function ResizeHandle({
  onMouseDown,
  onKeyDown,
  value,
  min,
  max,
  controls,
  className,
  isDragging = false,
}: ResizeHandleProps) {
  const [isHovering, setIsHovering] = useState(false);
  const lineActive = isDragging || isHovering;

  return (
    <div
      className={cn("relative z-10 w-0 shrink-0 self-stretch", className)}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <button
        type="button"
        tabIndex={-1}
        aria-label="拖动调整面板大小"
        data-testid="resize-handle-container"
        data-agent-canvas-source="v1.6.1"
        className="absolute inset-y-0 left-1/2 w-6 min-w-[24px] -translate-x-1/2 cursor-ew-resize border-0 bg-transparent p-0"
        onMouseDown={onMouseDown}
      />
      <div
        role="slider"
        aria-orientation="vertical"
        aria-label="调整面板大小"
        aria-controls={controls}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={Math.round(value)}
        tabIndex={0}
        onKeyDown={onKeyDown}
        className={cn(
          "absolute inset-y-0 left-1/2 w-px -translate-x-1/2 transition-colors focus-visible:bg-ra-accent",
          lineActive ? "bg-ra-accent" : "bg-transparent",
        )}
        data-testid="resize-handle"
      />
    </div>
  );
}
