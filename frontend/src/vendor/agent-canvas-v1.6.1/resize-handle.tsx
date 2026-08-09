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
 * semantics. The upstream zero-width frame, 12px drag target, one-pixel line,
 * hover state, and drag-state highlight remain intact.
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
        className="absolute inset-y-0 left-1/2 w-3 min-w-[12px] -translate-x-1/2 cursor-ew-resize border-0 bg-transparent p-0"
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
          "absolute inset-y-0 left-1/2 w-px -translate-x-1/2 transition-colors focus:outline-none focus-visible:bg-ra-accent",
          lineActive ? "bg-white" : "bg-transparent",
        )}
        data-testid="resize-handle"
      />
    </div>
  );
}
