interface ErrorStateProps {
  title?: string;
  error?: unknown;
  onRetry?: () => void;
}

export function ErrorState({ title = "Something went wrong", error, onRetry }: ErrorStateProps) {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "string"
        ? error
        : undefined;
  return (
    <div role="alert" data-testid="error-state" className="flex flex-col gap-2 p-4 text-sm">
      <h3 className="font-medium text-rose-700">{title}</h3>
      {message ? <p className="text-xs text-rose-600">{message}</p> : null}
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="self-start rounded-md border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}
