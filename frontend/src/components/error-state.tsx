import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/cn";

interface ErrorStateProps {
  title?: string;
  error?: unknown;
  onRetry?: () => void;
}

/**
 * OpenHands-style error state.
 * Upstream reference: OpenHands error handling patterns (tag 1.8.0)
 * using danger color (#FF684E) and AlertCircle icon.
 * License: MIT (inherited from OpenHands)
 */
export function ErrorState({
  title = "出现错误",
  error,
  onRetry,
}: ErrorStateProps) {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "string"
        ? error
        : undefined;

  return (
    <div
      role="alert"
      data-testid="error-state"
      className="flex flex-col gap-2 p-4 text-sm text-ra-text-secondary"
    >
      <div className="flex items-center gap-2">
        <AlertCircle className="h-4 w-4 text-ra-status-error" />
        <h3 className="font-medium text-ra-status-error">{title}</h3>
      </div>
      {message ? (
        <p className="text-xs text-ra-text-tertiary">{message}</p>
      ) : null}
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className={cn(
            "self-start rounded-md border border-ra-border bg-ra-input px-3 py-1",
            "text-xs font-medium text-ra-text-secondary hover:bg-ra-tertiary",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
          )}
        >
          重试
        </button>
      ) : null}
    </div>
  );
}
