import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { AlertTriangle, CheckCircle2, Loader2, Play } from "lucide-react";
import {
  activateOwnerWindow,
  fetchOwnerWindowCard,
  preflightOwnerWindow,
  PlatformClientError,
  type OwnerWindowCard,
  type OwnerWindowPreflightResult,
  type PlatformGoal,
} from "@/lib/platform-client";
import { cn } from "@/lib/cn";

const CHECK_LABELS: Record<string, string> = {
  request: "窗口参数",
  leftover_claims: "没有残留的执行占用",
  goals: "目标可以执行",
  model_pool: "有可用的模型",
  routing: "每一步都选得到模型",
};

const REASONS: Record<string, string> = {
  owner_window_old_active_claims_hold: "上一个窗口还留着执行占用：等它结束，或在终端里先清理。",
  owner_window_goal_not_admissible: "目标不在可执行状态：只有已生成计划、还没开始执行的目标能启动。",
  owner_window_pool_empty: "没有一个模型绑定可用：请在设置里启用至少一个。",
  owner_window_task_unroutable: "有一步找不到合适的模型：请启用更强的模型，或改计划。",
  owner_window_task_unbound: "有一步没有可用的模型绑定。",
  owner_window_pinned_binding_outside_pool: "目标指定的模型不在本窗口可用的模型里。",
  owner_window_max_tasks_below_planned_tasks: "任务上限小于计划的步数。",
  owner_window_requires_one_repository: "一次只能启动同一个仓库的目标。",
  owner_window_capability_missing: "计划里有一步需要的能力不在窗口里。",
  owner_window_scope_too_large: "一次启动的范围太大。",
};

function reasonText(reason: string): string {
  const code = reason.split(":", 1)[0];
  return REASONS[code] ?? reason;
}

function tokens(value: number) {
  return value >= 1_000_000 ? `${(value / 1_000_000).toFixed(value % 1_000_000 ? 1 : 0)}M` : value.toLocaleString("zh-CN");
}

function boundsText(card: OwnerWindowCard) {
  const r = card.request;
  const hours = r.hours >= 48 ? `${Math.round(r.hours / 24)} 天` : `${r.hours} 小时`;
  return [`时长 ${hours}`, `最多 ${r.max_tasks} 个任务`, `每步最多重试 ${r.max_retries} 次`, `同时 ${r.max_concurrent} 个`,
    r.max_token_units ? `Token 上限 ${tokens(r.max_token_units)}` : "Token 不设上限"].join(" · ");
}

/** "- goal T001: free (provider/model, reason)" → "T001 → provider/model（免费）". */
function previewLine(line: string): string {
  const match = /^-\s*\S+\s+(\S+):\s*(\w+)\s*\(([^,)]+)/.exec(line);
  if (!match) return line.replace(/^-\s*/, "");
  const [, task, cost, model] = match;
  const costLabel = cost === "free" ? "免费" : cost === "subscription" ? "订阅额度" : cost === "paid" ? "付费" : cost;
  return `${task} → ${model}（${costLabel}）`;
}

const COST_LABELS: Record<string, string> = { free: "免费", subscription: "订阅额度", paid: "付费" };

/** Start authorizes only the plan on screen: every checked goal must be at the revision shown. */
export function scopeMatchesGoal(report: OwnerWindowPreflightResult | undefined, goal: PlatformGoal): boolean {
  const goals = report?.scope?.goals ?? [];
  return goals.length > 0 && goals.every((entry) => entry.id !== goal.id || entry.revision === goal.revision)
    && goals.some((entry) => entry.id === goal.id);
}

function terminalCommand(card: OwnerWindowCard) {
  const r = card.request;
  return ["python -m reverse_agent.platform_v1.owner_window", ...r.goal_ids.map((id) => `--goal ${id}`),
    `--hours ${r.hours}`, `--max-tasks ${r.max_tasks}`, `--max-concurrent ${r.max_concurrent}`,
    `--max-retries ${r.max_retries}`, ...r.capabilities.map((capability) => `--capability ${capability}`),
    ...(r.max_token_units ? [`--max-token-units ${r.max_token_units}`] : [])].join(" ");
}

/**
 * The confirmation card (Owner decision 2026-11-09): pick a preset, read the
 * host's preflight, and Start activates the window. The host checks the card
 * digest against the scope it rereads; Start never sends anything the card did
 * not show. In the Owner's strict mode the card shows the terminal command.
 */
export function StartCard({ goal }: { goal: PlatformGoal }) {
  const [preset, setPreset] = useState("");
  const [notice, setNotice] = useState("");
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const cardQuery = useQuery({
    queryKey: ["owner-window-card", goal.id, goal.revision, preset],
    queryFn: () => fetchOwnerWindowCard([goal.id], preset),
    staleTime: 30_000, retry: false,
  });
  const card = cardQuery.data;
  const preflightQuery = useQuery<OwnerWindowPreflightResult>({
    queryKey: ["owner-window-preflight", goal.id, goal.revision, card?.preset, card?.request],
    queryFn: () => preflightOwnerWindow(card!.request),
    enabled: Boolean(card), staleTime: 15_000, retry: false,
  });
  const report = preflightQuery.data;
  const start = useMutation({
    mutationFn: () => activateOwnerWindow(card!.request, report!.card_digest!),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["goals"] });
      await queryClient.invalidateQueries({ queryKey: ["platform"] });
      navigate(`/?goal=${encodeURIComponent(goal.id)}`);
    },
    onError: (error) => {
      if (error instanceof PlatformClientError && error.code === "owner_window_scope_changed") {
        setNotice("你确认之后范围变了（计划、模型或参数），已重新检查，请再看一遍再开始。");
        // Reload the goal itself, not only the check: Start must never authorize a plan not on screen.
        void queryClient.invalidateQueries({ queryKey: ["goals", goal.id] });
        void queryClient.invalidateQueries({ queryKey: ["owner-window-card", goal.id] });
        void preflightQuery.refetch();
      }
    },
  });

  const failed = report?.checks.filter((check) => !check.ok) ?? [];
  const terminal = card?.confirmation === "terminal" || report?.confirmation === "terminal";
  const stale = Boolean(report?.scope) && !scopeMatchesGoal(report, goal);
  const canStart = Boolean(card && report?.ok && report.card_digest && scopeMatchesGoal(report, goal)
    && !terminal && !start.isPending);
  useEffect(() => {
    // The host checked a newer plan than the one shown: bring the shown plan up to date.
    if (stale) void queryClient.invalidateQueries({ queryKey: ["goals", goal.id] });
  }, [stale, queryClient, goal.id, report?.card_digest]);

  return (
    <section data-testid="start-card" aria-label="开始执行" className="mt-6 rounded-2xl border border-ra-border bg-ra-light/30 p-4">
      <h3 className="text-sm font-medium text-ra-text">开始执行</h3>
      <p className="mt-1 text-xs text-ra-text-secondary">
        选好执行窗口后点「开始」。窗口到期、任务数或 Token 用完就会停下；只开 Draft PR，不用付费 API。
      </p>

      {cardQuery.isError ? (
        <p role="alert" className="mt-3 text-sm text-ra-status-error">{(cardQuery.error as Error).message}</p>
      ) : null}

      {card ? (
        <>
          <div role="radiogroup" aria-label="执行窗口" className="mt-3 flex flex-wrap gap-2">
            {Object.entries(card.presets).map(([name, values]) => (
              <button key={name} type="button" role="radio" aria-checked={card.preset === name}
                data-testid={`start-preset-${name}`}
                onClick={() => { setNotice(""); setPreset(name); }}
                className={cn("rounded-lg border px-3 py-1.5 text-sm",
                  card.preset === name ? "border-ra-accent bg-ra-accent/10 text-ra-text" : "border-ra-border text-ra-text-secondary hover:bg-ra-tertiary")}>
                {values.label ?? name}
              </button>
            ))}
          </div>
          <p data-testid="start-bounds" className="mt-2 text-xs text-ra-text-secondary">{boundsText(card)}</p>
        </>
      ) : cardQuery.isPending ? (
        <p className="mt-3 flex items-center gap-2 text-xs text-ra-text-tertiary"><Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />正在读取执行窗口选项…</p>
      ) : null}

      {preflightQuery.isFetching && !report ? (
        <p className="mt-3 flex items-center gap-2 text-xs text-ra-text-tertiary"><Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />主机正在检查能不能启动…</p>
      ) : null}
      {preflightQuery.isError ? (
        <p role="alert" className="mt-3 text-sm text-ra-status-error">{(preflightQuery.error as Error).message}</p>
      ) : null}

      {report ? (
        <div data-testid="start-preflight" className="mt-3 space-y-2">
          {failed.length === 0 ? (
            <p className="flex items-center gap-2 text-sm text-ra-status-running">
              <CheckCircle2 className="h-4 w-4" aria-hidden="true" />检查通过，可以开始。
            </p>
          ) : (
            <ul className="space-y-1">
              {failed.map((check) => (
                <li key={check.check} data-testid={`start-check-${check.check}`} className="flex items-start gap-2 text-sm text-ra-status-error" title={check.reason}>
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                  <span>{CHECK_LABELS[check.check] ?? check.check}：{reasonText(check.reason)}</span>
                </li>
              ))}
            </ul>
          )}
          {report.warnings?.map((warning) => (
            <p key={`${warning.warning}-${warning.goal_id ?? ""}`} className="text-xs text-ra-status-warning">
              {warning.warning === "goal_unpublishable"
                ? "注意：计划里没有把检查过的结果交给审查的步骤，完成后不会自动开 Draft PR。"
                : warning.detail ?? warning.warning}
            </p>
          ))}
          {stale ? (
            <p role="status" data-testid="start-stale" className="text-xs text-ra-status-warning">
              计划刚被修改过，页面上的计划还不是主机检查的那一版：正在刷新，刷新后再开始。
            </p>
          ) : null}
          {report.scope?.pool?.length ? (
            <div data-testid="start-pool" className="text-xs text-ra-text-secondary">
              <p>本窗口可以用这些模型（{report.scope.pool.length} 个），执行时会在其中挑选：</p>
              <ul className="mt-1 space-y-0.5">
                {report.scope.pool.map((entry) => (
                  <li key={entry.binding}>
                    {entry.model || entry.binding} · {entry.executor}（{COST_LABELS[entry.cost] ?? entry.cost}{entry.weekly_paced ? "，按周配额节奏" : ""}）
                  </li>
                ))}
              </ul>
              {report.scope.pool_skipped?.length ? (
                <p data-testid="start-pool-skipped" className="mt-1 text-ra-text-tertiary">
                  不会使用：{report.scope.pool_skipped.join("、")}
                </p>
              ) : null}
            </div>
          ) : null}
          {report.preview.length > 0 ? (
            <details className="text-xs text-ra-text-tertiary">
              <summary className="cursor-pointer select-none hover:text-ra-text-secondary">每一步预计用的模型（{report.preview.length}）</summary>
              <ul className="mt-1 space-y-0.5" data-testid="start-preview">
                {report.preview.map((line) => <li key={line}>{previewLine(line)}</li>)}
              </ul>
            </details>
          ) : null}
        </div>
      ) : null}

      {notice ? <p role="status" className="mt-3 text-sm text-ra-status-warning">{notice}</p> : null}
      {start.isError && !(start.error instanceof PlatformClientError && start.error.code === "owner_window_scope_changed") ? (
        <p role="alert" data-testid="start-error" className="mt-3 text-sm text-ra-status-error">{(start.error as Error).message}</p>
      ) : null}

      {terminal && card ? (
        <div data-testid="start-terminal" className="mt-3 text-xs text-ra-text-secondary">
          <p>设置里打开了严格确认：请在主机终端运行下面的命令，并输入它显示的确认码。</p>
          <code className="mt-1 block break-all rounded-lg border border-ra-border bg-ra-base p-2 font-mono">{terminalCommand(card)}</code>
        </div>
      ) : (
        <button type="button" data-testid="start-button" disabled={!canStart} onClick={() => { setNotice(""); start.mutate(); }}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-ra-accent px-4 py-2 text-sm font-medium text-ra-base disabled:opacity-50">
          {start.isPending ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Play className="h-4 w-4" aria-hidden="true" />}
          开始
        </button>
      )}
    </section>
  );
}
