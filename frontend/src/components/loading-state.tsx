export function LoadingState({ label = "加载中…" }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="loading-state"
      className="flex items-center gap-2 p-4 text-sm text-ra-text-tertiary"
    >
      <span
        aria-hidden="true"
        className="h-3 w-3 animate-pulse rounded-full bg-ra-text-tertiary"
      />
      {label}
    </div>
  );
}
