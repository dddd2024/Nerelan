import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import { useAgentRoster, usePutAgentRoster } from "@/hooks/use-model-access";
import { AGENT_ROLES, type AgentRole } from "@/lib/model-control-client";
import type { Binding } from "@/schemas/model-access";

const ROLE_COPY: Record<AgentRole, { label: string; hint: string }> = {
  planner: { label: "规划者", hint: "拆分目标、设计方案。建议用最强的模型。" },
  complex: { label: "复杂编码", hint: "架构级、跨多个文件的改动。" },
  coder: { label: "常规编码", hint: "一般功能与修复；未标注角色的任务默认交给它。" },
  simple: { label: "简单任务", hint: "文档、测试、小改动。适合免费或便宜的模型。" },
  reviewer: { label: "审查者", hint: "必须与常规编码使用不同的模型。" },
};

interface AgentTeamEditorProps {
  bindings: Binding[];
}

/** Maps each team role to a saved Binding so each kind of work goes to a matching agent. */
export function AgentTeamEditor({ bindings }: AgentTeamEditorProps) {
  const rosterQuery = useAgentRoster();
  const putRoster = usePutAgentRoster();
  const [draft, setDraft] = useState<Partial<Record<AgentRole, string>>>({});
  const [error, setError] = useState("");
  const usable = bindings.filter((binding) => binding.enabled);

  useEffect(() => {
    if (!rosterQuery.data) return;
    const next: Partial<Record<AgentRole, string>> = {};
    for (const role of AGENT_ROLES) next[role] = rosterQuery.data[role].bindingId;
    setDraft(next);
  }, [rosterQuery.data]);

  const changed = rosterQuery.data !== undefined
    && AGENT_ROLES.some((role) => (draft[role] ?? "") !== rosterQuery.data![role].bindingId);

  async function save() {
    setError("");
    try {
      await putRoster.mutateAsync(draft);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "保存失败");
    }
  }

  return (
    <section aria-labelledby="agent-team-heading" className="mt-6 rounded-2xl border border-ra-border/70 bg-ra-workspace p-4 sm:p-5">
      <div className="flex items-start gap-3">
        <Users className="mt-0.5 h-4 w-4 shrink-0 text-ra-text-tertiary" aria-hidden="true" />
        <div className="min-w-0">
          <h2 id="agent-team-heading" className="text-sm font-medium text-ra-text">Agent 团队</h2>
          <p className="mt-1 text-xs leading-5 text-ra-text-secondary">
            “多 Agent 分工”模式下，每个子任务按角色交给对应的模型：强模型负责规划和难点，便宜模型负责简单工作，以降低整体成本。
          </p>
        </div>
      </div>
      {rosterQuery.isError ? (
        <p role="alert" className="mt-3 text-sm text-ra-status-error">Agent 团队读取失败。</p>
      ) : (
        <dl className="mt-4 grid gap-3 sm:grid-cols-2">
          {AGENT_ROLES.map((role) => {
            const entry = rosterQuery.data?.[role];
            const unavailable = entry && entry.bindingId && !entry.available;
            return (
              <div key={role} className="rounded-xl border border-ra-border/60 px-3 py-2.5">
                <dt className="flex items-center justify-between gap-2">
                  <label htmlFor={`agent-role-${role}`} className="text-sm font-medium text-ra-text">{ROLE_COPY[role].label}</label>
                  {unavailable && <span className="text-[11px] text-ra-status-warning">绑定不可用</span>}
                </dt>
                <dd className="mt-1">
                  <p className="text-[11px] leading-4 text-ra-text-tertiary">{ROLE_COPY[role].hint}</p>
                  <select
                    id={`agent-role-${role}`}
                    aria-label={`${ROLE_COPY[role].label}的模型绑定`}
                    className="mt-2 w-full rounded-lg border border-ra-border bg-ra-input px-2.5 py-1.5 text-sm text-ra-text"
                    value={draft[role] ?? ""}
                    disabled={putRoster.isPending || rosterQuery.isPending}
                    onChange={(event) => setDraft((current) => ({ ...current, [role]: event.target.value }))}
                  >
                    <option value="">未分配</option>
                    {usable.map((binding) => (
                      <option key={binding.bindingId} value={binding.bindingId}>
                        {binding.name} · {binding.executorId} · {binding.modelId}
                      </option>
                    ))}
                  </select>
                </dd>
              </div>
            );
          })}
        </dl>
      )}
      {error && <p role="alert" className="mt-3 text-sm text-ra-status-error">{error}</p>}
      <div className="mt-4 flex justify-end">
        <button
          type="button"
          onClick={() => void save()}
          disabled={!changed || putRoster.isPending}
          className="rounded-lg bg-ra-accent px-3 py-1.5 text-sm font-medium text-ra-base disabled:opacity-50"
        >
          {putRoster.isPending ? "保存中…" : "保存 Agent 团队"}
        </button>
      </div>
    </section>
  );
}
