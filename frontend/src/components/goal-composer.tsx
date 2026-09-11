import {
  ArrowUp,
  Bot,
  GitBranch,
  Settings2,
} from "lucide-react";
import { useRef, useState } from "react";
import type { StartGoalInput } from "@/lib/goal-start-operation";
import { cn } from "@/lib/cn";

interface GoalComposerProps {
  busy: boolean;
  onSubmit: (input: StartGoalInput) => Promise<void>;
}

interface GoalComposerDraft extends StartGoalInput {
  confirmed: boolean;
}

const MAX_TEXTAREA_HEIGHT = 144;
const DRAFT_STORAGE_KEY = "nerelan.goal-composer.draft.v1";
const OPERATION_ID_PATTERN = /^[A-Za-z0-9._:-]{8,160}$/;

function createOperationId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `goal-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}

function freshDraft(): GoalComposerDraft {
  return {
    objective: "",
    repository: "dddd2024/reverse-agent",
    executorKind: "opencode",
    bindingRef: "coding-default",
    autonomyHours: 2,
    operationId: createOperationId(),
    confirmed: false,
  };
}

function readDraft(): GoalComposerDraft {
  const fallback = freshDraft();
  if (typeof window === "undefined") return fallback;
  let raw: string | null;
  try {
    raw = window.sessionStorage.getItem(DRAFT_STORAGE_KEY);
  } catch {
    return fallback;
  }
  if (!raw) return fallback;

  try {
    const parsed = JSON.parse(raw) as Partial<GoalComposerDraft>;
    if (
      typeof parsed.objective !== "string" ||
      typeof parsed.repository !== "string" ||
      !["opencode", "deterministic_fixture"].includes(parsed.executorKind ?? "") ||
      typeof parsed.bindingRef !== "string" ||
      parsed.autonomyHours !== 2 ||
      typeof parsed.operationId !== "string" ||
      !OPERATION_ID_PATTERN.test(parsed.operationId) ||
      typeof parsed.confirmed !== "boolean"
    ) {
      throw new Error("invalid_goal_composer_draft");
    }
    return {
      objective: parsed.objective.slice(0, 20_000),
      repository: parsed.repository.slice(0, 500),
      executorKind: parsed.executorKind as StartGoalInput["executorKind"],
      bindingRef: parsed.bindingRef.slice(0, 500),
      autonomyHours: 2,
      operationId: parsed.operationId,
      confirmed: parsed.confirmed,
    };
  } catch {
    try {
      window.sessionStorage.removeItem(DRAFT_STORAGE_KEY);
    } catch {
      // Session persistence is best-effort; the in-memory draft remains safe.
    }
    return fallback;
  }
}

function persistDraft(draft: GoalComposerDraft) {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draft));
  } catch {
    // Draft persistence must never block the user's in-memory editing.
  }
}

function clearPersistedDraft() {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(DRAFT_STORAGE_KEY);
  } catch {
    // A stale UI draft cannot mutate server Goal identity.
  }
}

function resizeObjectiveTextarea(element: HTMLTextAreaElement) {
  element.style.height = "auto";
  if (element.scrollHeight > 0) {
    element.style.height = `${Math.min(element.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`;
  }
}

export function GoalComposer({ busy, onSubmit }: GoalComposerProps) {
  const [draft, setDraft] = useState<GoalComposerDraft>(readDraft);
  const [optionsOpen, setOptionsOpen] = useState(
    () => draft.objective.trim().length > 0,
  );
  const draftRef = useRef(draft);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function replaceDraft(next: GoalComposerDraft, persist = true) {
    draftRef.current = next;
    setDraft(next);
    if (persist) persistDraft(next);
  }

  function editDraft(patch: Partial<GoalComposerDraft>) {
    replaceDraft({
      ...draftRef.current,
      ...patch,
      operationId: createOperationId(),
    });
  }

  const showOptions = optionsOpen || draft.objective.trim().length > 0;
  const ready =
    draft.objective.trim().length >= 8 &&
    draft.repository.includes("/") &&
    !busy;

  return (
    <form
      className="rounded-xl border border-ra-border/70 bg-ra-workspace transition-colors focus-within:border-ra-border-strong"
      onSubmit={async (event) => {
        event.preventDefault();
        if (!ready) return;
        const submitted: StartGoalInput = {
          objective: draftRef.current.objective.trim(),
          repository: draftRef.current.repository.trim(),
          executorKind: draftRef.current.executorKind,
          bindingRef: draftRef.current.bindingRef,
          autonomyHours: 2,
          operationId: draftRef.current.operationId,
        };

        try {
          await onSubmit(submitted);
        } catch {
          return;
        }

        if (draftRef.current.operationId !== submitted.operationId) return;
        const next = freshDraft();
        clearPersistedDraft();
        replaceDraft(next, false);
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
          value={draft.objective}
          onChange={(event) => {
            editDraft({ objective: event.target.value });
            resizeObjectiveTextarea(event.target);
          }}
          placeholder="Ask Nerelan to work on something…"
          rows={1}
          className="min-h-9 max-h-36 min-w-0 flex-1 resize-none overflow-y-auto bg-transparent px-2 py-2 text-[15px] leading-5 text-ra-text placeholder:text-ra-text-tertiary focus:outline-none"
        />

        <button
          type="submit"
          disabled={!ready}
          aria-label="创建并审阅目标"
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
                  value={draft.repository}
                  onChange={(event) => editDraft({ repository: event.target.value })}
                  className="w-44 bg-transparent text-ra-text focus:outline-none"
                />
              </label>
              <label className="inline-flex items-center gap-2 rounded-lg border border-ra-border/70 bg-ra-base/30 px-2.5 py-1.5 text-xs text-ra-text-secondary">
                <Bot className="h-3.5 w-3.5" aria-hidden="true" />
                <select
                  aria-label="执行模式"
                  value={draft.executorKind}
                  onChange={(event) =>
                    editDraft({
                      executorKind: event.target.value as StartGoalInput["executorKind"],
                    })
                  }
                  className="bg-transparent text-ra-text focus:outline-none"
                >
                  <option value="opencode">OpenCode 多 Agent</option>
                  <option value="deterministic_fixture">无模型验证</option>
                </select>
              </label>
              {draft.executorKind === "opencode" && (
                <input
                  aria-label="模型绑定"
                  value={draft.bindingRef}
                  onChange={(event) => editDraft({ bindingRef: event.target.value })}
                  placeholder="模型绑定"
                  className="w-36 rounded-lg border border-ra-border/70 bg-ra-base/30 px-2.5 py-1.5 text-xs text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
                />
              )}
            </div>

            <p className="text-xs text-ra-text-secondary">先保存草稿，审阅并批准后再启动。</p>
          </div>
        </div>
      )}
    </form>
  );
}
