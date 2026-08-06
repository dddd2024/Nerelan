import type { ReactNode } from "react";
import { Clock } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

/**
 * OpenHands-style empty state.
 * Upstream reference: EmptyChangesMessage, ConversationPanel empty state
 * (tag 1.8.0) — icon centered, muted text. License: MIT.
 */
export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center gap-2 p-8 text-center"
      role="status"
      data-testid="empty-state"
    >
      {icon ? (
        <div className="text-ra-text-tertiary">{icon}</div>
      ) : (
        <Clock className="h-8 w-8 text-ra-text-tertiary" />
      )}
      <h3 className="text-sm font-medium text-ra-text-secondary">{title}</h3>
      {description ? (
        <p className="max-w-sm text-xs text-ra-text-tertiary">{description}</p>
      ) : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}
