import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Sparkles, Users } from "lucide-react";
import { AGENT_ROSTER_QUERY_KEY, useAgentRoster, usePutAgentRoster } from "@/hooks/use-model-access";
import { AGENT_ROLES, type AgentRole } from "@/lib/model-control-client";
import { applyAgentPolicy, fetchAgentPolicyJob, interpretAgentPolicy, type AgentPolicyJob } from "@/lib/platform-client";
import type { Binding } from "@/schemas/model-access";

const ROLE_COPY: Record<AgentRole, { label: string; hint: string }> = {
  planner: { label: "规划者", hint: "拆分目标、设计方案。建议用最强的模型。" },
  complex: { label: "复杂编码", hint: "架构级、跨多个文件的改动。" },
  coder: { label: "常规编码", hint: "一般功能与修复；未标注角色的任务默认交给它。" },
  simple: { label: "简单任务", hint: "文档、测试、小改动。适合免费或便宜的模型。" },
  reviewer: { label: "审查者", hint: "必须与常规编码使用不同的模型。" },
};
const POLL_MS = 2_000;
const EXAMPLE = "规划和难题用 Claude Opus，日常编码尽量用免费模型，审查交给 GPT，总限流的模型别用，整体越省越好。";

interface AgentTeamEditorProps {
  bindings: Binding[];
}

/** Configures the Agent team from one natural-language sentence; manual role edits stay available. */
export function AgentTeamEditor({ bindings }: AgentTeamEditorProps) {
  const queryClient = useQueryClient();
  const rosterQuery = useAgentRoster();
  const putRoster = usePutAgentRoster();
  const [draft, setDraft] = useState<Partial<Record<AgentRole, string>>>({});
  const [text, setText] = useState("");
  const [job, setJob] = useState<AgentPolicyJob | null>(null);
  const [error, setError] = useState("");
  const usable = bindings.filter((binding) => binding.enabled);
  const nameOf = (bindingId: string) => {
    const binding = bindings.find((item) => item.bindingId === bindingId);
    return binding ? `${binding.name} · ${binding.modelId}` : bindingId;
  };

  useEffect(() => {
    if (!rosterQuery.data) return;
    const next: Partial<Record<AgentRole, string>> = {};
    for (const role of AGENT_ROLES) next[role] = rosterQuery.data[role].bindingId;
    setDraft(next);
    if (rosterQuery.data.policy?.text) setText((current) => current || rosterQuery.data!.policy!.text);
  }, [rosterQuery.data]);

  useEffect(() => {
    if (job?.status !== "RUNNING") return;
    const timer = window.setInterval(() => {
      void fetchAgentPolicyJob(job.id).then(setJob).catch(() => undefined);
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [job]);

  const changed = rosterQuery.data !== undefined
    && AGENT_ROLES.some((role) => (draft[role] ?? "") !== rosterQuery.data![role].bindingId);

  async function interpret() {
    setError("");
    try {
      setJob(await interpretAgentPolicy(text.trim()));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "理解偏好失败");
    }
  }

  async function apply() {
    if (!job) return;
    setError("");
    try {
      const result = await applyAgentPolicy(job.id);
      setJob(result.job);
      await queryClient.invalidateQueries({ queryKey: AGENT_ROSTER_QUERY_KEY });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "应用失败");
    }
  }

  async function saveManual() {
    setError("");
    try {
      await putRoster.mutateAsync(draft);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "保存失败");
    }
  }

  const proposal = job?.status === "PROPOSED" || job?.status === "APPLIED" ? job.proposal : null;

  return (
    <section aria-labelledby="agent-team-heading" className="mt-6 rounded-2xl border border-ra-border/70 bg-ra-workspace p-4 sm:p-5">
      <div className="flex items-start gap-3">
        <Users className="mt-0.5 h-4 w-4 shrink-0 text-ra-text-tertiary" aria-hidden="true" />
        <div className="min-w-0">
          <h2 id="agent-team-heading" className="text-sm font-medium text-ra-text">Agent 团队</h2>
          <p className="mt-1 text-xs leading-5 text-ra-text-secondary">
            用一句话描述你的偏好，系统会结合你已保存的模型和它们最近的表现，自动安排“多 Agent 分工”里每类工作交给谁。确认后才会生效。
          </p>
        </div>
      </div>

      <label htmlFor="agent-policy-text" className="mt-4 block text-sm font-medium text-ra-text">我的偏好</label>
      <textarea
        id="agent-policy-text"
        aria-label="Agent 团队偏好"
        className="mt-2 w-full rounded-lg border border-ra-border bg-ra-input px-3 py-2 text-sm text-ra-text"
        rows={3}
        maxLength={2000}
        placeholder={EXAMPLE}
        value={text}
        onChange={(event) => setText(event.target.value)}
      />
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <button type="button" onClick={() => void interpret()} disabled={!text.trim() || job?.status === "RUNNING"}
          className="inline-flex items-center gap-1.5 rounded-lg bg-ra-accent px-3 py-1.5 text-sm font-medium text-ra-base disabled:opacity-50">
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          {job?.status === "RUNNING" ? "正在理解…" : "让系统理解并给出安排"}
        </button>
        {job?.status === "FAILED" && <span role="alert" className="text-xs text-ra-status-error">没能理解：{job.error}</span>}
      </div>

      {proposal && (
        <div className="mt-4 rounded-xl border border-ra-border/60 bg-ra-light/40 p-3" data-testid="agent-policy-proposal">
          <p className="text-sm font-medium text-ra-text">我的理解是：</p>
          {proposal.explanation && <p className="mt-1 text-sm leading-6 text-ra-text-secondary">{proposal.explanation}</p>}
          <dl className="mt-3 grid gap-1.5 text-xs sm:grid-cols-2">
            {AGENT_ROLES.map((role) => (
              <div key={role} className="flex gap-2">
                <dt className="w-16 shrink-0 text-ra-text-tertiary">{ROLE_COPY[role].label}</dt>
                <dd className="min-w-0 truncate text-ra-text">{proposal.roles?.[role] ? nameOf(proposal.roles[role]) : "未分配"}</dd>
              </div>
            ))}
          </dl>
          {proposal.excluded && proposal.excluded.length > 0 && (
            <p className="mt-2 text-xs text-ra-text-secondary">不使用：{proposal.excluded.map(nameOf).join("、")}</p>
          )}
          <div className="mt-3 flex flex-wrap gap-2">
            {job?.status === "APPLIED"
              ? <span role="status" className="text-xs text-ra-status-running">已应用到 Agent 团队。</span>
              : <>
                  <button type="button" onClick={() => void apply()}
                    className="rounded-lg bg-ra-accent px-3 py-1.5 text-sm font-medium text-ra-base">确认应用</button>
                  <button type="button" onClick={() => setJob(null)}
                    className="rounded-lg border border-ra-border px-3 py-1.5 text-sm text-ra-text">放弃</button>
                </>}
          </div>
        </div>
      )}

      {rosterQuery.data?.policy?.explanation && !proposal && (
        <p className="mt-3 text-xs leading-5 text-ra-text-secondary">当前安排：{rosterQuery.data.policy.explanation}</p>
      )}

      <details className="mt-4">
        <summary className="cursor-pointer text-xs text-ra-text-secondary hover:text-ra-text">高级：手动指定每个角色</summary>
        {rosterQuery.isError ? (
          <p role="alert" className="mt-3 text-sm text-ra-status-error">Agent 团队读取失败。</p>
        ) : (
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
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
        <div className="mt-3 flex justify-end">
          <button type="button" onClick={() => void saveManual()} disabled={!changed || putRoster.isPending}
            className="rounded-lg border border-ra-border px-3 py-1.5 text-sm text-ra-text disabled:opacity-50">
            {putRoster.isPending ? "保存中…" : "保存 Agent 团队"}
          </button>
        </div>
      </details>

      {error && <p role="alert" className="mt-3 text-sm text-ra-status-error">{error}</p>}
    </section>
  );
}
