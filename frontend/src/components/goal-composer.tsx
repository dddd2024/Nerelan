import {
  ArrowUp,
  Bot,
  GitBranch,
  Settings2,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useBindings } from "@/hooks/use-model-access";
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
    repository: "dddd2024/Nerelan",
    executorKind: "opencode",
    /*
     * Deliberately empty. A hardcoded binding name is a promise the frontend
     * cannot keep: if that binding is renamed, disabled, or routed to an
     * unavailable provider, the goal fails server-side with a bare KeyError.
     * The composer fills this from the bindings that actually exist.
     */
    bindingRef: "",
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
  const [bindingTouched, setBindingTouched] = useState(false);
  const draftRef = useRef(draft);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const bindingsQuery = useBindings();
  const usableBindings = useMemo(
    () =>
      (bindingsQuery.data ?? []).filter(
        (binding) => binding.enabled && binding.executorId === "opencode",
      ),
    [bindingsQuery.data],
  );

  /*
   * Default the binding to one that exists rather than to a remembered name.
   * Runs once, and never overwrites a binding the user typed themselves.
   */
  useEffect(() => {
    if (bindingTouched || bindingsQuery.data === undefined) return;
    const usable = usableBindings[0];
    if (!usable || draftRef.current.bindingRef) return;
    replaceDraft({ ...draftRef.current, bindingRef: usable.bindingId });
  }, [bindingTouched, bindingsQuery.data, usableBindings]);

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
  const needsBinding = draft.executorKind === "opencode";
  const bindingMissing = needsBinding && draft.bindingRef.trim().length === 0;
  const objectiveLength = draft.objective.trim().length;
  const repositoryReady = draft.repository.includes("/");
  const ready =
    objectiveLength >= 8 &&
    repositoryReady &&
    !bindingMissing &&
    !busy;

  /*
   * A disabled submit button with no stated reason is a dead end: the user
   * cannot tell whether the app is broken or waiting for something. Surface
   * the first unmet requirement, but only once the user has actually started
   * typing — an idle composer stays quiet (`#448` §9 state-aware actions,
   * §10 exception-driven UI).
   *
   * The missing-binding case is deliberately not repeated here: the options
   * row already states it next to the binding field itself.
   */
  const blockedReason = busy
    ? "正在创建目标…"
    : objectiveLength === 0
      ? null
      : objectiveLength < 8
        ? `目标描述至少需要 8 个字，当前 ${objectiveLength} 个。`
        : !repositoryReady
          ? "仓库需要写成 owner/name 的形式。"
          : null;

  return (
    <form
      className="rounded-2xl border border-ra-border bg-ra-workspace shadow-[0_2px_8px_-4px_var(--ra-border-strong)] transition-[border-color,box-shadow] focus-within:border-ra-accent focus-within:shadow-[0_0_0_3px_color-mix(in_srgb,var(--ra-accent)_12%,transparent)]"
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
      <div className="flex min-h-14 items-end gap-1.5 px-2 py-2.5">
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
          placeholder="让 Nerelan 做点什么…"
          rows={1}
          className="min-h-9 max-h-36 min-w-0 flex-1 resize-none overflow-y-auto bg-transparent px-2 py-2 text-[15px] leading-5 text-ra-text placeholder:text-ra-text-tertiary focus:outline-none"
        />

        <button
          type="submit"
          disabled={!ready}
          aria-label="创建并审阅目标"
          aria-describedby={blockedReason ? "goal-composer-blocked" : undefined}
          title={blockedReason ?? "创建并审阅目标"}
          className={cn(
            "inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition",
            ready
              ? "bg-ra-accent text-ra-base hover:bg-ra-accent-hover"
              : "bg-ra-tertiary/60 text-ra-text-tertiary",
          )}
        >
          <ArrowUp className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      {blockedReason ? (
        <p
          id="goal-composer-blocked"
          data-testid="goal-composer-blocked"
          className="px-3 pb-2 text-xs text-ra-text-tertiary"
        >
          {blockedReason}
        </p>
      ) : null}

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
                <>
                  <input
                    aria-label="模型绑定"
                    value={draft.bindingRef}
                    list="goal-composer-bindings"
                    onChange={(event) => {
                      setBindingTouched(true);
                      editDraft({ bindingRef: event.target.value });
                    }}
                    placeholder="模型绑定"
                    className={cn(
                      "w-36 rounded-lg border bg-ra-base/30 px-2.5 py-1.5 text-xs text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                      bindingMissing
                        ? "border-ra-status-warning/60"
                        : "border-ra-border/70",
                    )}
                  />
                  <datalist id="goal-composer-bindings">
                    {usableBindings.map((binding) => (
                      <option key={binding.bindingId} value={binding.bindingId}>
                        {binding.name}
                      </option>
                    ))}
                  </datalist>
                </>
              )}
            </div>

            <p className="text-xs text-ra-text-secondary">先保存草稿，审阅并批准后再启动。</p>
          </div>
          {bindingMissing ? (
            <p
              role="status"
              data-testid="goal-composer-binding-hint"
              className="mt-2 text-xs text-ra-status-warning"
            >
              {bindingsQuery.isLoading
                ? "正在获取可用的模型绑定…"
                : "没有可用的 OpenCode 绑定。请先在设置页创建连接与绑定，或直接填写绑定名称。"}
            </p>
          ) : null}
        </div>
      )}
    </form>
  );
}
