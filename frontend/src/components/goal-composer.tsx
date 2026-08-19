import { ArrowUp, Bot, GitBranch, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { StartGoalInput } from "@/lib/platform-client";
import { cn } from "@/lib/cn";

interface GoalComposerProps {
  busy: boolean;
  onSubmit: (input: StartGoalInput) => void;
}

export function GoalComposer({ busy, onSubmit }: GoalComposerProps) {
  const [objective, setObjective] = useState("");
  const [repository, setRepository] = useState("dddd2024/reverse-agent");
  const [executorKind, setExecutorKind] = useState<StartGoalInput["executorKind"]>("opencode");
  const [bindingRef, setBindingRef] = useState("coding-default");
  const [confirmed, setConfirmed] = useState(false);

  const ready = objective.trim().length >= 8 && repository.includes("/") && confirmed && !busy;

  return (
    <form
      className="rounded-2xl border border-ra-border bg-ra-light/90 shadow-[0_18px_70px_rgba(0,0,0,.22)]"
      onSubmit={(event) => {
        event.preventDefault();
        if (!ready) return;
        onSubmit({ objective: objective.trim(), repository: repository.trim(), executorKind, bindingRef, autonomyHours: 2 });
        setObjective("");
      }}
    >
      <label htmlFor="goal-objective" className="sr-only">描述最终目标</label>
      <textarea
        id="goal-objective"
        value={objective}
        onChange={(event) => setObjective(event.target.value)}
        placeholder="描述你希望平台完成的最终目标…"
        rows={4}
        className="min-h-32 w-full resize-none bg-transparent px-5 pt-5 text-[17px] leading-7 text-ra-text placeholder:text-ra-text-tertiary focus:outline-none"
      />

      <div className="border-t border-ra-border/70 px-4 py-3">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <label className="inline-flex items-center gap-2 rounded-lg border border-ra-border bg-ra-base/40 px-3 py-2 text-xs text-ra-text-secondary">
              <GitBranch className="h-3.5 w-3.5" />
              <input
                aria-label="仓库"
                value={repository}
                onChange={(event) => setRepository(event.target.value)}
                className="w-44 bg-transparent text-ra-text focus:outline-none"
              />
            </label>
            <label className="inline-flex items-center gap-2 rounded-lg border border-ra-border bg-ra-base/40 px-3 py-2 text-xs text-ra-text-secondary">
              <Bot className="h-3.5 w-3.5" />
              <select
                aria-label="执行模式"
                value={executorKind}
                onChange={(event) => setExecutorKind(event.target.value as StartGoalInput["executorKind"])}
                className="bg-transparent text-ra-text focus:outline-none"
              >
                <option value="opencode">OpenCode 多 Agent</option>
                <option value="deterministic_fixture">无模型验证</option>
              </select>
            </label>
            {executorKind === "opencode" && (
              <input
                aria-label="模型绑定"
                value={bindingRef}
                onChange={(event) => setBindingRef(event.target.value)}
                placeholder="模型绑定"
                className="w-36 rounded-lg border border-ra-border bg-ra-base/40 px-3 py-2 text-xs text-ra-text focus:outline-none focus:ring-1 focus:ring-ra-accent"
              />
            )}
          </div>
          <div className="flex items-center justify-between gap-3 xl:justify-end">
            <label className="inline-flex cursor-pointer items-center gap-2 text-xs text-ra-text-secondary">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(event) => setConfirmed(event.target.checked)}
                className="h-4 w-4 accent-blue-400"
              />
              <ShieldCheck className="h-3.5 w-3.5" />
              启用 2 小时自治窗口
            </label>
            <button
              type="submit"
              disabled={!ready}
              aria-label="规划并运行"
              className={cn(
                "inline-flex h-9 w-9 items-center justify-center rounded-full transition",
                ready ? "bg-ra-text text-ra-base hover:bg-blue-100" : "bg-ra-tertiary text-ra-text-tertiary",
              )}
            >
              <ArrowUp className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}
