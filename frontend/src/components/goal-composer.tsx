import {
  ArrowUp,
  Bot,
  GitBranch,
  Settings2,
  ShieldCheck,
} from "lucide-react";
import { useRef, useState } from "react";
import type { StartGoalInput } from "@/lib/platform-client";
import { cn } from "@/lib/cn";

interface GoalComposerProps {
  busy: boolean;
  onSubmit: (input: StartGoalInput) => void;
}

const MAX_TEXTAREA_HEIGHT = 144;

function resizeObjectiveTextarea(element: HTMLTextAreaElement) {
  element.style.height = "auto";
  if (element.scrollHeight > 0) {
    element.style.height = `${Math.min(element.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`;
  }
}

export function GoalComposer({ busy, onSubmit }: GoalComposerProps) {
  const [objective, setObjective] = useState("");
  const [repository, setRepository] = useState("dddd2024/Nerelan");
  const [executorKind, setExecutorKind] =
    useState<StartGoalInput["executorKind"]>("opencode");
  const [bindingRef, setBindingRef] = useState("coding-default");
  const [confirmed, setConfirmed] = useState(false);
  const [optionsOpen, setOptionsOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const showOptions = optionsOpen || objective.trim().length > 0;
  const ready =
    objective.trim().length >= 8 &&
    repository.includes("/") &&
    confirmed &&
    !busy;

  return (
    <form
      className="rounded-xl border border-ra-border/70 bg-ra-workspace transition-colors focus-within:border-ra-border-strong"
      onSubmit={(event) => {
        event.preventDefault();
        if (!ready) return;
        onSubmit({
          objective: objective.trim(),
          repository: repository.trim(),
          executorKind,
          bindingRef,
          autonomyHours: 2,
        });
        setObjective("");
        setOptionsOpen(false);
        if (textareaRef.current) textareaRef.current.style.height = "auto";
      }}
    >
      <div className="flex min-h-12 items-end gap-1.5 px-2 py-1.5">
        <button
          type="button"
          aria-label="输入选项"
          aria-expanded={showOptions}
          onClick={() => setOptionsOpen((value) => !value)}
          className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-ra-text-tertiary transition hover:bg-ra-light/60 hover:text-ra-text-secondary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
        >
          <Settings2 className="h-4 w-4" aria-hidden="true" />
        </button>

        <label htmlFor="goal-objective" className="sr-only">
          描述最终目标
        </label>
        <textarea
          ref={textareaRef}
          id="goal-objective"
          value={objective}
          onChange={(event) => {
            setObjective(event.target.value);
            resizeObjectiveTextarea(event.target);
          }}
          placeholder="Ask Nerelan to work on something…"
          rows={1}
          className="min-h-9 max-h-36 min-w-0 flex-1 resize-none overflow-y-auto bg-transparent px-2 py-2 text-[15px] leading-5 text-ra-text placeholder:text-ra-text-tertiary focus:outline-none"
        />

        <button
          type="submit"
          disabled={!ready}
          aria-label="规划并运行"
          className={cn(
            "inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition",
            ready
              ? "bg-ra-text text-ra-base hover:opacity-90"
              : "bg-ra-light/70 text-ra-text-tertiary",
          )}
        >
          <ArrowUp className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      {showOptions && (
        <div
          data-testid="goal-composer-options"
          className="border-t border-ra-border/60 px-3 py-2.5"
        >
          <div className="flex flex-col gap-2.5 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-wrap items-center gap-2">
              <label className="inline-flex items-center gap-2 rounded-lg border border-ra-border/70 bg-ra-base/30 px-2.5 py-1.5 text-xs text-ra-text-secondary">
                <GitBranch className="h-3.5 w-3.5" aria-hidden="true" />
                <input
                  aria-label="仓库"
                  value={repository}
                  onChange={(event) => setRepository(event.target.value)}
                  className="w-44 bg-transparent text-ra-text focus:outline-none"
                />
              </label>
              <label className="inline-flex items-center gap-2 rounded-lg border border-ra-border/70 bg-ra-base/30 px-2.5 py-1.5 text-xs text-ra-text-secondary">
                <Bot className="h-3.5 w-3.5" aria-hidden="true" />
                <select
                  aria-label="执行模式"
                  value={executorKind}
                  onChange={(event) =>
                    setExecutorKind(
                      event.target.value as StartGoalInput["executorKind"],
                    )
                  }
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
                  className="w-36 rounded-lg border border-ra-border/70 bg-ra-base/30 px-2.5 py-1.5 text-xs text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
                />
              )}
            </div>

            <label className="inline-flex cursor-pointer items-center gap-2 text-xs text-ra-text-secondary">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(event) => setConfirmed(event.target.checked)}
                className="h-4 w-4 accent-blue-400"
              />
              <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
              启用 2 小时自治窗口
            </label>
          </div>
        </div>
      )}
    </form>
  );
}