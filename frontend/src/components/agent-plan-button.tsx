import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { fetchAgentPlanStatus, startAgentPlan, type AgentPlanStatus, type PlatformGoal } from "@/lib/platform-client";

const POLL_MS = 3_000;

/** Asks the Agent team's planner to decompose an agent_team Goal into role-tagged tasks. */
export function AgentPlanButton({ goal, busy }: { goal: PlatformGoal; busy: boolean }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<AgentPlanStatus | null>(null);
  const [error, setError] = useState("");
  const running = status?.status === "RUNNING";

  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => {
      void fetchAgentPlanStatus(goal.id).then((next) => {
        setStatus(next);
        if (next.status === "PLANNED") {
          void queryClient.invalidateQueries({ queryKey: ["goals"] });
          void queryClient.invalidateQueries({ queryKey: ["goals", goal.id] });
        }
      }).catch(() => undefined);
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [running, goal.id, queryClient]);

  if (goal.orchestration_mode !== "agent_team" || !["DRAFT", "PLANNED"].includes(goal.status)) return null;

  async function start() {
    setError("");
    try {
      setStatus(await startAgentPlan(goal.id, goal.revision));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "规划启动失败");
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2" data-testid="agent-plan">
      <button type="button" onClick={() => void start()} disabled={busy || running}
        className="inline-flex items-center gap-1.5 rounded-lg border border-ra-border px-3 py-2 text-sm text-ra-text disabled:opacity-50">
        <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
        {running ? "规划者正在拆分任务…" : "让规划者拆分任务"}
      </button>
      {status?.status === "PLANNED" && <span role="status" className="text-xs text-ra-status-running">已生成按角色分工的计划，请审阅后批准。</span>}
      {status?.status === "FAILED" && <span role="alert" className="text-xs text-ra-status-error">规划失败：{status.error}</span>}
      {error && <span role="alert" className="text-xs text-ra-status-error">{error}</span>}
    </div>
  );
}
