import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center gap-2 p-8 text-center"
      role="status"
      data-testid="empty-state"
    >
      {icon ? <div className="text-slate-400">{icon}</div> : null}
      <h3 className="text-sm font-medium text-slate-700">{title}</h3>
      {description ? (
        <p className="max-w-sm text-xs text-slate-500">{description}</p>
      ) : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}
