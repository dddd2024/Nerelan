import { Inbox as InboxIcon, Sparkles, X } from "lucide-react";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  captureInboxItem,
  dismissInboxItem,
  fetchInbox,
  promoteInboxItem,
  type PlatformInboxItem,
} from "@/lib/platform-client";
import { cn } from "@/lib/cn";

const STATUS_LABELS: Record<PlatformInboxItem["status"], string> = {
  CAPTURED: "已捕获",
  PROMOTED: "已晋升为目标",
  DISMISSED: "已忽略",
};

export function InboxPage() {
  const queryClient = useQueryClient();
  const inboxQuery = useQuery({
    queryKey: ["inbox"],
    queryFn: fetchInbox,
    staleTime: 2_000,
    refetchInterval: 5_000,
  });
  const [objective, setObjective] = useState("");
  const [error, setError] = useState("");

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["inbox"] });
    void queryClient.invalidateQueries({ queryKey: ["goals"] });
  };

  const captureMutation = useMutation({
    mutationFn: captureInboxItem,
    onSuccess: () => {
      setObjective("");
      setError("");
      invalidate();
    },
    onError: (err: Error) => setError(err.message),
  });
  const promoteMutation = useMutation({
    mutationFn: promoteInboxItem,
    onSuccess: invalidate,
    onError: (err: Error) => setError(err.message),
  });
  const dismissMutation = useMutation({
    mutationFn: dismissInboxItem,
    onSuccess: invalidate,
    onError: (err: Error) => setError(err.message),
  });

  const items = inboxQuery.data ?? [];
  const captured = items.filter((item) => item.status === "CAPTURED");
  const settled = items.filter((item) => item.status !== "CAPTURED");

  return (
    <main data-testid="inbox-page" className="min-h-full bg-[var(--oh-surface)] px-4 py-7 sm:px-8 lg:px-12 lg:py-10">
      <div className="mx-auto w-full max-w-[900px]">
        <header className="mb-8">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-ra-text-tertiary">Human inbox</p>
          <h1 className="mt-2 flex items-center gap-2 text-3xl font-medium tracking-[-0.025em] text-ra-text sm:text-4xl">
            <InboxIcon className="h-7 w-7" aria-hidden="true" />想法收件箱
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-ra-text-secondary">
            先把想法记下来。捕获的内容只是展示状态，不具备执行权限；晋升会通过既有的目标审批链路创建普通 DRAFT 目标。
          </p>
        </header>

        <form
          data-testid="inbox-composer"
          className="rounded-2xl border border-ra-border bg-ra-light/40 p-4"
          onSubmit={(event) => {
            event.preventDefault();
            const trimmed = objective.trim();
            if (!trimmed) return;
            captureMutation.mutate({ objective: trimmed });
          }}
        >
          <label htmlFor="inbox-objective" className="block text-sm font-medium text-ra-text">
            记录一个想法
          </label>
          <textarea
            id="inbox-objective"
            aria-label="描述想法"
            data-testid="inbox-objective-input"
            rows={3}
            value={objective}
            onChange={(event) => setObjective(event.target.value)}
            placeholder="例如：让平台在夜间自动处理积压任务"
            className="mt-2 w-full resize-none rounded-xl border border-ra-border bg-ra-base px-3 py-2 text-sm text-ra-text placeholder:text-ra-text-tertiary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
          />
          <div className="mt-3 flex items-center justify-between">
            <p className="text-xs text-ra-text-tertiary">捕获仅保存展示状态，不会触发任何执行。</p>
            <button
              type="submit"
              aria-label="捕获想法"
              data-testid="inbox-capture-button"
              disabled={captureMutation.isPending || !objective.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-ra-accent px-3 py-2 text-sm font-medium text-ra-base disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
            >
              <Sparkles className="h-4 w-4" aria-hidden="true" />捕获
            </button>
          </div>
        </form>

        {error && (
          <p role="alert" data-testid="inbox-error" className="mt-3 text-sm text-red-300">{error}</p>
        )}

        <section aria-label="待处理想法" className="mt-10">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-medium text-ra-text">待处理</h2>
            <span className="text-xs text-ra-text-tertiary">{captured.length} 条</span>
          </div>
          <ul className="space-y-2" data-testid="inbox-captured-list">
            {captured.map((item) => (
              <li
                key={item.id}
                data-testid={`inbox-item-${item.id}`}
                className="rounded-xl border border-ra-border bg-ra-base p-4"
              >
                <p className="text-sm font-medium text-ra-text">{item.title}</p>
                <p className="mt-1 text-sm leading-6 text-ra-text-secondary">{item.objective}</p>
                <div className="mt-3 flex items-center gap-2">
                  <button
                    type="button"
                    aria-label={`晋升 ${item.title} 为目标`}
                    data-testid={`inbox-promote-${item.id}`}
                    disabled={promoteMutation.isPending}
                    onClick={() => promoteMutation.mutate(item.id)}
                    className="rounded-lg bg-ra-accent px-3 py-1.5 text-xs font-medium text-ra-base disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
                  >
                    晋升为目标
                  </button>
                  <button
                    type="button"
                    aria-label={`忽略 ${item.title}`}
                    data-testid={`inbox-dismiss-${item.id}`}
                    disabled={dismissMutation.isPending}
                    onClick={() => dismissMutation.mutate(item.id)}
                    className="inline-flex items-center gap-1 rounded-lg border border-ra-border px-3 py-1.5 text-xs text-ra-text-secondary hover:text-ra-text disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
                  >
                    <X className="h-3.5 w-3.5" aria-hidden="true" />忽略
                  </button>
                </div>
              </li>
            ))}
            {captured.length === 0 && (
              <li className="rounded-xl border border-dashed border-ra-border py-10 text-center text-sm text-ra-text-tertiary">
                没有待处理的想法。
              </li>
            )}
          </ul>
        </section>

        <section aria-label="历史记录" className="mt-10">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-medium text-ra-text">历史</h2>
            <span className="text-xs text-ra-text-tertiary">{settled.length} 条</span>
          </div>
          <ul className="space-y-1" data-testid="inbox-history-list">
            {settled.map((item) => (
              <li
                key={item.id}
                data-testid={`inbox-item-${item.id}`}
                className="flex items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm text-ra-text-secondary"
              >
                <span className="min-w-0 truncate">{item.title}</span>
                <span
                  className={cn(
                    "shrink-0 rounded-full px-2 py-0.5 text-[11px]",
                    item.status === "PROMOTED"
                      ? "bg-emerald-400/10 text-emerald-300"
                      : "bg-ra-light text-ra-text-tertiary",
                  )}
                >
                  {STATUS_LABELS[item.status]}
                </span>
              </li>
            ))}
            {settled.length === 0 && (
              <li className="py-6 text-center text-xs text-ra-text-tertiary">暂无历史。</li>
            )}
          </ul>
        </section>
      </div>
    </main>
  );
}
