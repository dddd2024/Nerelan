export function LoadingState({ label = "加载中…" }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="loading-state"
      className="flex items-center gap-2 p-4 text-sm text-slate-500"
    >
      <span aria-hidden="true" className="h-3 w-3 animate-pulse rounded-full bg-slate-300" />
      {label}
    </div>
  );
}
