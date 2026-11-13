/**
 * The goal page as an agent conversation (Claude / Codex conventions), built on
 * assistant-ui primitives over Nerelan's own goal timeline:
 * - a centred column: the Owner's request, then each agent attempt as an
 *   assistant turn with its words as prose and its tool calls folded into one
 *   row ("运行 3 条命令、读取 2 个文件") that expands;
 * - a docked composer that starts a new goal (a running agent cannot receive
 *   follow-up messages, so it does not pretend to);
 * - a side panel (Codex) with the steps, what changed and the checks.
 */
import { useMemo, useState, type PropsWithChildren, type ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useExternalStoreRuntime,
  type AppendMessage,
  type DataMessagePartProps,
  type TextMessagePartProps,
  type ThreadMessageLike,
  type ToolCallMessagePartProps,
} from "@assistant-ui/react";
import { ArrowDown, ArrowUp, Check, ChevronRight, CircleAlert, FileText, FolderSearch, LoaderCircle, PencilLine, Search, SquareTerminal, TestTube2 } from "lucide-react";
import { Link } from "react-router";
import type { PlatformGoal, PlatformGoalTimeline, PlatformRetryOptions, PlatformTimelineStep } from "@/lib/platform-client";
import { goalThread, type AttemptFiles, type AttemptHeader, type AttemptStop, type ToolArgs } from "@/lib/goal-thread";
import { stepTitle } from "@/lib/goal-view";
import { formatRelativeTime } from "@/lib/format";
import { functionalStatusLabel, normalizeFunctionalValidation } from "@/lib/functional-validation";
import { publicationText, statusFor } from "@/components/goal-progress";
import { StepRetry } from "@/components/step-retry";
import { livenessLabel } from "@/lib/run-vocabulary";
import { cn } from "@/lib/cn";

const TOOL_ICON: Record<string, typeof FileText> = {
  read: FileText, search: Search, edit: PencilLine, command: SquareTerminal, test: TestTube2,
};
const TOOL_VERB: Record<string, [string, string]> = {
  read: ["读取", "个文件"], search: ["搜索", "次"], edit: ["修改", "处"], command: ["运行", "条命令"], test: ["运行", "项检查"],
};

function UserMessage() {
  const [open, setOpen] = useState(false);
  return (
    <MessagePrimitive.Root className="mb-8 flex justify-end" data-testid="thread-user-message">
      <div className="max-w-[85%] rounded-3xl bg-ra-tertiary px-4 py-2.5">
        <div className={cn("whitespace-pre-line text-[15px] leading-7 text-ra-text", !open && "line-clamp-4")}>
          <MessagePrimitive.Parts />
        </div>
        <button type="button" onClick={() => setOpen((value) => !value)}
          className="mt-0.5 text-xs text-ra-text-tertiary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
          {open ? "收起" : "展开全文"}
        </button>
      </div>
    </MessagePrimitive.Root>
  );
}

function Prose({ text }: TextMessagePartProps) {
  return <p className="my-2 whitespace-pre-wrap text-[15px] leading-7 text-ra-text">{text}</p>;
}

function ToolRow(props: ToolCallMessagePartProps) {
  const args = props.args as ToolArgs;
  const Icon = TOOL_ICON[props.toolName] ?? FolderSearch;
  return (
    <li className="flex min-w-0 items-center gap-2 py-0.5 text-[13px] text-ra-text-secondary" data-testid={`thread-tool-${props.toolCallId}`}>
      <Icon className="h-3.5 w-3.5 shrink-0 text-ra-text-tertiary" aria-hidden="true" />
      <span className="min-w-0 flex-1 truncate font-mono text-xs" title={args?.detail}>{args?.detail}</span>
    </li>
  );
}

/** Consecutive tool calls fold into one row, the way agent chats show "Ran 3 commands". */
function ToolGroup({ children, startIndex, endIndex, parts }: PropsWithChildren<{ startIndex: number; endIndex: number; parts: readonly { type: string; toolName?: string }[] }>) {
  const counts = new Map<string, number>();
  for (const part of parts.slice(startIndex, endIndex + 1)) {
    if (part.type === "tool-call" && part.toolName) counts.set(part.toolName, (counts.get(part.toolName) ?? 0) + 1);
  }
  const summary = [...counts.entries()].map(([name, n]) => TOOL_VERB[name] ? `${TOOL_VERB[name][0]} ${n} ${TOOL_VERB[name][1]}` : `${n} 个动作`).join("、");
  return (
    <details className="group my-1.5" data-testid="thread-tool-group">
      <summary className="flex w-fit cursor-pointer list-none items-center gap-1 rounded-md py-0.5 text-[13px] text-ra-text-secondary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent [&::-webkit-details-marker]:hidden">
        {summary || "工具调用"}
        <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" aria-hidden="true" />
      </summary>
      <ul className="mt-1 max-h-72 overflow-y-auto border-l border-ra-border pl-3">{children}</ul>
    </details>
  );
}

const STATE_TEXT: Record<AttemptHeader["state"], [string, string]> = {
  running: ["进行中", "text-ra-accent"],
  done: ["完成", "text-ra-status-running"],
  stopped: ["停下", "text-ra-status-error"],
  queued: ["等待开始", "text-ra-text-tertiary"],
  retried: ["被中断，已自动重试", "text-ra-text-tertiary"],
};

function AttemptHeaderPart({ data }: DataMessagePartProps<AttemptHeader>) {
  const [label, tone] = STATE_TEXT[data.state];
  return (
    <div className="mb-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-ra-text-tertiary" data-testid="thread-attempt-header">
      <span className="font-medium text-ra-text">{data.step}</span>
      {data.attempts > 1 && <span>第 {data.attempt} 次</span>}
      {data.agent && <span>· {data.agent}</span>}
      {data.startedAt && data.state !== "queued" && <span>· {formatRelativeTime(data.startedAt)}</span>}
      <span className={cn("ml-auto inline-flex items-center gap-1", tone)}>
        {data.state === "running" && <LoaderCircle className="h-3 w-3 animate-spin" aria-hidden="true" />}
        {data.state === "running" && data.live ? livenessLabel(data.live) : label}
      </span>
    </div>
  );
}

function NotePart({ data }: DataMessagePartProps<{ text: string }>) {
  return <p className="my-1 text-xs text-ra-text-tertiary">{data.text}</p>;
}

function FilesPart({ data }: DataMessagePartProps<AttemptFiles>) {
  const add = data.files.reduce((sum, file) => sum + file.additions, 0);
  const del = data.files.reduce((sum, file) => sum + file.deletions, 0);
  return (
    <details className="group my-2 rounded-xl border border-ra-border" data-testid="thread-files">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-[13px] text-ra-text hover:bg-ra-light/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent [&::-webkit-details-marker]:hidden">
        改了 {data.files.length} 个文件
        <span className="font-mono text-xs text-ra-status-running">+{add}</span>
        <span className="font-mono text-xs text-ra-status-error">−{del}</span>
        <ChevronRight className="ml-auto h-3.5 w-3.5 text-ra-text-tertiary transition-transform group-open:rotate-90" aria-hidden="true" />
      </summary>
      <ul className="border-t border-ra-border px-3 py-1.5">
        {data.files.map((file) => (
          <li key={file.path} className="flex items-center gap-2 py-0.5 font-mono text-xs">
            <span className="min-w-0 flex-1 truncate text-ra-text-secondary" title={file.path}>{file.path}</span>
            <span className="text-ra-status-running">+{file.additions}</span>
            <span className="text-ra-status-error">−{file.deletions}</span>
          </li>
        ))}
      </ul>
    </details>
  );
}

function SummaryPart({ data }: DataMessagePartProps<{ text: string }>) {
  const [open, setOpen] = useState(false);
  const long = data.text.length > 400;
  return (
    <div className="my-2" data-testid="thread-summary">
      <p className={cn("whitespace-pre-wrap text-[15px] leading-7 text-ra-text", long && !open && "line-clamp-6")}>{data.text}</p>
      {long && (
        <button type="button" onClick={() => setOpen((value) => !value)}
          className="text-xs text-ra-text-tertiary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
          {open ? "收起" : "展开全部"}
        </button>
      )}
    </div>
  );
}

function StopPart({ data }: DataMessagePartProps<AttemptStop>) {
  if (data.superseded) {
    return <p className="my-2 text-xs text-ra-text-tertiary" data-testid="thread-stop">这次因“{data.label}”停下，之后已重试。</p>;
  }
  return (
    <div role="alert" className="my-2 flex items-start gap-2 rounded-xl bg-ra-status-error/5 px-3 py-2.5" data-testid="thread-stop">
      <CircleAlert className="mt-0.5 h-4 w-4 shrink-0 text-ra-status-error" aria-hidden="true" />
      <div className="min-w-0 text-sm">
        <p className="font-medium text-ra-text">停下了：{data.label}</p>
        {data.nextStep && <p className="mt-0.5 text-ra-text-secondary">{data.nextStep}</p>}
        {data.detail && (
          <details className="mt-1 text-xs text-ra-text-tertiary">
            <summary className="w-fit cursor-pointer hover:text-ra-text-secondary">技术细节</summary>
            <p className="mt-1 break-words font-mono">{data.detail}</p>
          </details>
        )}
      </div>
    </div>
  );
}

function AssistantMessage({ messages }: { messages: ThreadMessageLike[] }) {
  return (
    <MessagePrimitive.Root className="mb-8" data-testid="thread-assistant-message">
      <MessagePrimitive.Parts
        components={{
          Text: Prose,
          tools: { Fallback: ToolRow },
          ToolGroup: ({ children, startIndex, endIndex }) => (
            <MessagePartsOf messages={messages}>
              {(parts) => <ToolGroup parts={parts} startIndex={startIndex} endIndex={endIndex}>{children}</ToolGroup>}
            </MessagePartsOf>
          ),
          data: { by_name: { attempt: AttemptHeaderPart, note: NotePart, files: FilesPart, summary: SummaryPart, stop: StopPart } },
        }}
      />
    </MessagePrimitive.Root>
  );
}

/** The current message's own parts (for the tool-group summary), read from the converted messages. */
function MessagePartsOf({ messages, children }: { messages: ThreadMessageLike[]; children: (parts: readonly { type: string; toolName?: string }[]) => ReactNode }) {
  const id = MessagePrimitive.useMessageId?.();
  const message = messages.find((item) => item.id === id);
  const parts = typeof message?.content === "string" ? [] : (message?.content ?? []);
  return <>{children(parts as readonly { type: string; toolName?: string }[])}</>;
}

function stepState(step: PlatformTimelineStep) {
  const current = step.attempts[step.attempts.length - 1];
  return statusFor(current?.status ?? step.status);
}

/** Codex-style side panel: the plan's steps, what changed, the checks, the PR. */
function GoalPanel({ goal, steps, retry, roles }: { goal: PlatformGoal; steps: PlatformTimelineStep[]; retry?: PlatformRetryOptions; roles: Map<string, string> }) {
  const files = new Map<string, { additions: number; deletions: number }>();
  for (const step of steps) {
    const latest = [...step.attempts].reverse().find((attempt) => (attempt.changed_files ?? []).length > 0);
    for (const file of latest?.changed_files ?? []) files.set(file.path, { additions: file.additions ?? 0, deletions: file.deletions ?? 0 });
  }
  return (
    <aside aria-label="目标概况" data-testid="goal-panel" className="hidden w-80 shrink-0 overflow-y-auto border-l border-ra-border px-5 py-5 text-sm lg:block custom-scrollbar">
      <h2 className="mb-2 text-xs font-medium text-ra-text-tertiary">步骤</h2>
      <ol className="space-y-3">
        {steps.map((step) => {
          const state = stepState(step);
          const current = step.attempts[step.attempts.length - 1];
          const proof = normalizeFunctionalValidation(step.functional_validation, current?.executor_kind);
          const Icon = state === "running" ? LoaderCircle : state === "review-ready" || state === "fixture-review-ready" ? Check : state === "blocked" || state === "interrupted" ? CircleAlert : null;
          return (
            <li key={step.plan_task_id} data-testid={`goal-panel-step-${step.plan_task_id}`}>
              <div className="flex items-center gap-2">
                <span className={cn("inline-flex h-4 w-4 items-center justify-center",
                  state === "running" ? "text-ra-accent" : state === "blocked" || state === "interrupted" ? "text-ra-status-error" : state === "queued" ? "text-ra-text-tertiary" : "text-ra-status-running")}>
                  {Icon ? <Icon className={cn("h-3.5 w-3.5", state === "running" && "animate-spin")} aria-hidden="true" /> : <span className="h-2 w-2 rounded-full border border-current" />}
                </span>
                <span className="min-w-0 flex-1 truncate font-medium text-ra-text">{stepTitle(step.title, roles.get(step.plan_task_id) ?? step.plan_task_id)}</span>
                {step.attempts.length > 1 && <span className="text-xs text-ra-text-tertiary">{step.attempts.length} 次</span>}
              </div>
              <p className="ml-6 mt-0.5 text-xs text-ra-text-tertiary">
                {functionalStatusLabel(proof.status)} · {publicationText(step.publication, step.publication_blocked)}
              </p>
              {step.publication?.pr_url && (
                <a href={step.publication.pr_url} target="_blank" rel="noreferrer" className="ml-6 text-xs text-ra-accent hover:underline">
                  打开 PR #{step.publication.pr_number}
                </a>
              )}
              {retry && ["FAILED", "BLOCKED"].includes(current?.status ?? "") && (
                <StepRetry goalId={goal.id} planTaskId={step.plan_task_id} options={retry} />
              )}
            </li>
          );
        })}
      </ol>
      {files.size > 0 && (
        <>
          <h2 className="mb-2 mt-6 text-xs font-medium text-ra-text-tertiary">改动（{files.size} 个文件）</h2>
          <ul className="space-y-1" data-testid="goal-panel-files">
            {[...files.entries()].map(([path, file]) => (
              <li key={path} className="flex items-center gap-2 font-mono text-xs">
                <span className="min-w-0 flex-1 truncate text-ra-text-secondary" title={path}>{path.split("/").pop()}</span>
                <span className="text-ra-status-running">+{file.additions}</span>
                <span className="text-ra-status-error">−{file.deletions}</span>
              </li>
            ))}
          </ul>
        </>
      )}
      <Link to={`/runs?goal=${encodeURIComponent(goal.id)}`}
        className="mt-6 inline-block text-xs text-ra-text-tertiary underline-offset-2 hover:text-ra-text hover:underline">
        查看完整运行记录
      </Link>
    </aside>
  );
}

export function GoalThread({ goal, timeline, onNewGoal, busy }: {
  goal: PlatformGoal;
  timeline?: PlatformGoalTimeline;
  onNewGoal: (text: string) => Promise<void>;
  busy?: boolean;
}) {
  const thread = useMemo(() => goalThread(goal, timeline), [goal, timeline]);
  const roles = useMemo(() => {
    const map = new Map((timeline?.plan ?? []).map((item) => [item.plan_task_id, item.role]));
    for (const task of goal.tasks) if (!map.has(task.id) && task.agent_role) map.set(task.id, task.agent_role);
    return map;
  }, [goal.tasks, timeline?.plan]);
  const runtime = useExternalStoreRuntime<ThreadMessageLike>({
    messages: thread.messages,
    convertMessage: (message) => message,
    isRunning: thread.running,
    isDisabled: busy,
    onNew: async (message: AppendMessage) => {
      const text = message.content.map((part) => (part.type === "text" ? part.text : "")).join("").trim();
      if (text) await onNewGoal(text);
    },
  });
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="flex min-h-0 flex-1" data-testid="goal-thread">
        <ThreadPrimitive.Root className="flex min-h-0 min-w-0 flex-1 flex-col">
          <ThreadPrimitive.Viewport className="relative min-h-0 flex-1 overflow-y-auto custom-scrollbar">
            <div className="mx-auto w-full max-w-[760px] px-4 pb-8 pt-6 sm:px-6">
              <ThreadPrimitive.Messages
                components={{ UserMessage, AssistantMessage: () => <AssistantMessage messages={thread.messages} /> }}
              />
            </div>
            <ThreadPrimitive.ScrollToBottom
              className="absolute bottom-3 left-1/2 inline-flex h-8 w-8 -translate-x-1/2 items-center justify-center rounded-full border border-ra-border bg-ra-base text-ra-text-secondary shadow-sm hover:text-ra-text disabled:invisible">
              <ArrowDown className="h-4 w-4" aria-hidden="true" />
              <span className="sr-only">回到最新</span>
            </ThreadPrimitive.ScrollToBottom>
          </ThreadPrimitive.Viewport>
          <div className="shrink-0 px-4 pb-4 sm:px-6">
            <ComposerPrimitive.Root className="mx-auto flex w-full max-w-[760px] items-end gap-2 rounded-3xl border border-ra-border bg-ra-base px-4 py-2.5 shadow-sm focus-within:border-ra-border-strong">
              <ComposerPrimitive.Input
                rows={1}
                placeholder="开始一个新目标…（正在运行的 Agent 不会收到这里的消息）"
                aria-label="开始一个新目标"
                className="max-h-40 min-h-6 flex-1 resize-none bg-transparent py-1 text-[15px] leading-6 text-ra-text outline-none placeholder:text-ra-text-tertiary"
              />
              <ComposerPrimitive.Send
                className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ra-text text-ra-base disabled:opacity-30">
                <ArrowUp className="h-4 w-4" aria-hidden="true" />
                <span className="sr-only">创建目标</span>
              </ComposerPrimitive.Send>
            </ComposerPrimitive.Root>
          </div>
        </ThreadPrimitive.Root>
        <GoalPanel goal={goal} steps={thread.steps} retry={timeline?.retry} roles={roles} />
      </div>
    </AssistantRuntimeProvider>
  );
}
