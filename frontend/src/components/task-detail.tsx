import { FunctionalValidationView } from "@/components/functional-validation";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import {
  BarChart2,
  ChevronRight,
  ExternalLink,
  FileText,
  GitBranch,
  GitPullRequest,
  ShieldCheck,
} from "lucide-react";
import { ActivityStream } from "@/components/activity-stream";
import { Badge } from "@/components/badge";
import { ChangesPanel } from "@/components/changes-panel";
import { CustomPolicyEditor } from "@/components/custom-policy-editor";
import { ErrorState } from "@/components/error-state";
import { EvidencePanel } from "@/components/evidence-panel";
import { LoadingState } from "@/components/loading-state";
import { PermissionsPanel } from "@/components/permissions-panel";
import { useBreakpoint } from "@/hooks/use-breakpoint";
import { usePlatformStatus } from "@/hooks/use-platform";
import { usePublishTask } from "@/hooks/use-task";
import { cn } from "@/lib/cn";
import { displayObjective, displayTitle } from "@/lib/display-title";
import {
  authorityStatusLabel,
  testStatusLabel,
  validationStatusLabel,
} from "@/lib/task-labels";
import {
  permissionModeLabel,
  riskTierStyle,
  runStateStyle,
} from "@/lib/format";
import { profileToPolicy } from "@/lib/profile-mapper";
import type { PolicyContract, Task } from "@/types";
import { AgentCanvasWorkbenchFrame } from "@/vendor/agent-canvas-v1.6.1/agent-canvas-workbench-frame";
import { ResizeHandle } from "@/vendor/agent-canvas-v1.6.1/resize-handle";

type WorkspacePane = "changes" | "evidence" | "authority";
type MobilePane = "activity" | WorkspacePane;

const RIGHT_TABS: {
  id: WorkspacePane;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}[] = [
  { id: "changes", label: "变更文件", icon: GitBranch },
  { id: "evidence", label: "证据", icon: BarChart2 },
  { id: "authority", label: "授权", icon: ShieldCheck },
];

interface RightPanelProps {
  rightTab: WorkspacePane;
  setRightTab: (tab: WorkspacePane) => void;
  displayTask: Task;
  policy: ReturnType<typeof profileToPolicy>;
}

function renderWorkspacePane(
  pane: MobilePane,
  task: Task,
  policy: ReturnType<typeof profileToPolicy>,
) {
  switch (pane) {
    case "activity":
      return <ActivityStream events={task.activity} />;
    case "changes":
      return <ChangesPanel changes={task.changes} />;
    case "evidence":
      return <EvidencePanel evidence={task.evidence} />;
    case "authority":
      return <PermissionsPanel policy={policy} />;
  }
}

/** Right-side navigation and content for the desktop two-pane workspace. */
function RightPanelTabList({
  rightTab,
  setRightTab,
}: Pick<RightPanelProps, "rightTab" | "setRightTab">) {
  return (
    <div
      role="tablist"
      aria-label="工作区分区"
      className="flex min-h-10 items-center gap-0.5 px-1.5"
    >
      {RIGHT_TABS.map((tab) => {
        const TabIcon = tab.icon;
        const selected = rightTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={selected}
            aria-controls={`tabpanel-${tab.id}`}
            tabIndex={selected ? 0 : -1}
            onClick={() => setRightTab(tab.id)}
            className={cn(
              "flex h-8 items-center gap-1.5 rounded-md px-2.5 text-sm font-medium",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
              selected
                ? "bg-ra-tertiary text-ra-text"
                : "text-ra-text-tertiary hover:text-ra-text hover:bg-ra-tertiary/50",
            )}
            data-testid={`right-tab-${tab.id}`}
          >
            <TabIcon className="h-4 w-4" aria-hidden="true" />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}

function RightPanelContent({
  rightTab,
  displayTask,
  policy,
}: Omit<RightPanelProps, "setRightTab">) {
  return (
    <div
      role="tabpanel"
      id={`tabpanel-${rightTab}`}
      aria-labelledby={`tab-${rightTab}`}
      className="h-full overflow-y-auto custom-scrollbar"
      data-testid="right-panel-content"
      data-active-pane={rightTab}
    >
      <div className="p-4">
        {renderWorkspacePane(rightTab, displayTask, policy)}
      </div>
    </div>
  );
}

/**
 * OpenHands ConversationMain + root-layout adaptation for task detail.
 *
 * Desktop (1024px+): resizable Activity / secondary-workspace split.
 * Mobile and tablet (<1024px): one reversible selector controlling exactly
 * one of Activity, Changed Files, Evidence and Authority.
 */
export function TaskDetail({ task, isLoading, isError, error }: TaskDetailProps) {
  const [rightTab, setRightTab] = useState<WorkspacePane>("changes");
  const [mobilePane, setMobilePane] = useState<MobilePane>("activity");
  const [customEditorOpen, setCustomEditorOpen] = useState(false);
  const [editorPolicy, setEditorPolicy] = useState<PolicyContract | null>(null);
  const [leftWidth, setLeftWidth] = useState(55);
  const [isDragging, setIsDragging] = useState(false);

  const breakpoint = useBreakpoint();
  const isDesktop = breakpoint === "desktop";
  const splitContainerRef = useRef<HTMLDivElement>(null);
  const platformStatus = usePlatformStatus();
  const publication = usePublishTask(task?.id ?? "");

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (event: MouseEvent) => {
      const splitContainer = splitContainerRef.current;
      if (!splitContainer) return;
      const rect = splitContainer.getBoundingClientRect();
      if (rect.width <= 0) return;
      setLeftWidth(clampWidth(((event.clientX - rect.left) / rect.width) * 100));
    };
    const stopDragging = () => setIsDragging(false);

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", stopDragging);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", stopDragging);
    };
  }, [isDragging]);

  const handleResizeKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    switch (event.key) {
      case "ArrowLeft":
        setLeftWidth((width) => clampWidth(width - 5));
        event.preventDefault();
        break;
      case "ArrowRight":
        setLeftWidth((width) => clampWidth(width + 5));
        event.preventDefault();
        break;
      case "Home":
        setLeftWidth(30);
        event.preventDefault();
        break;
      case "End":
        setLeftWidth(80);
        event.preventDefault();
        break;
    }
  };

  const displayTask = task ?? null;

  if (isLoading) {
    return (
      <main data-testid="task-detail">
        <LoadingState label="加载任务中…" />
      </main>
    );
  }

  if (isError || !displayTask) {
    return (
      <main data-testid="task-detail">
        <ErrorState title="未找到任务" error={error} />
        <div className="px-4">
          <Link
            to="/tasks"
            className="inline-flex min-h-6 items-center text-sm text-ra-text-tertiary hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
          >
            ← 返回任务列表
          </Link>
        </div>
      </main>
    );
  }

  const state = runStateStyle(displayTask.state);
  const risk = riskTierStyle(displayTask.riskTier);
  const policy = profileToPolicy(displayTask.permissionProfile);
  const activeWindow = platformStatus.data?.autonomy?.active_window ?? null;
  const changedPaths = Array.from(
    new Set(displayTask.changes.map((change) => change.path).filter(Boolean)),
  );
  const taskRepository = displayTask.repository ?? "";
  const publicationUsesHttp =
    import.meta.env.MODE !== "mock" &&
    !(import.meta.env.MODE === "test" && !import.meta.env.VITE_TASK_CLIENT_USE_HTTP);
  const windowCanPublish = Boolean(
    activeWindow &&
      activeWindow.status === "ACTIVE" &&
      activeWindow.capabilities.includes("open_draft_pr") &&
      activeWindow.repositories.includes(taskRepository),
  );
  const canPublish =
    publicationUsesHttp &&
    displayTask.state === "READY_FOR_HUMAN" &&
    changedPaths.length > 0 &&
    !displayTask.draftPr &&
    windowCanPublish;

  const stateDotColor = state.dot;
  const objective = displayObjective(displayTask.title);

  return (
    <main
      data-testid="task-detail"
      className="flex flex-col h-full gap-3 p-3 md:p-0"
    >
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4.5 pt-2 lg:pt-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="group relative flex-shrink-0">
            <div
              className={cn("w-4 h-4 rounded-full cursor-pointer", stateDotColor)}
              aria-label={state.label}
              title={state.label}
            />
          </div>
          <div className="flex items-center gap-2 min-w-0">
            <Link
              to="/tasks"
              aria-label="返回任务列表"
              className="inline-flex h-6 w-6 items-center justify-center rounded text-ra-text-tertiary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
            >
              ←
            </Link>
            {displayTask.issueNumber ? (
              <>
                <span className="text-xs text-ra-text-tertiary font-mono">
                  #{displayTask.issueNumber}
                </span>
                <span aria-hidden="true" className="text-ra-text-tertiary">
                  ·
                </span>
              </>
            ) : null}
            <span className="font-mono text-xs text-ra-text-tertiary truncate">
              {displayTask.branch}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Badge className={cn(state.badge)} dot={state.dot}>
            {state.label}
          </Badge>
          <Badge className={cn(risk.badge)} dot={risk.dot}>
            {risk.label}
          </Badge>
          <Badge className="border-ra-border bg-ra-tertiary text-ra-text-secondary">
            {permissionModeLabel(displayTask.permissionProfile)}
          </Badge>
          <button
            type="button"
            aria-label="编辑权限"
            onClick={() => {
              setEditorPolicy(profileToPolicy(displayTask.permissionProfile));
              setCustomEditorOpen(true);
            }}
            className={cn(
              // min-h-6 guarantees the 24px minimum target regardless of the
              // 14px icon vs 16px line box that made this button 22px tall.
              "inline-flex min-h-6 min-w-6 items-center justify-center rounded-md px-2 py-1 text-xs text-ra-text-tertiary",
              "hover:text-ra-text hover:bg-ra-tertiary",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
            )}
            title="编辑权限策略"
          >
            <FileText className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="min-w-0">
        <h1 className="text-lg font-semibold leading-6 text-ra-text">
          {displayTitle(displayTask.title)}
        </h1>

        {objective ? (
          <details className="group mt-1.5" data-testid="task-objective-disclosure">
            <summary
              className={cn(
                // min-h-6 holds the 24px minimum target: a bare `text-xs`
                // inline-flex summary computes to a 16px hit box, and both
                // disclosures in this panel measured 64x16.
                "inline-flex min-h-6 cursor-pointer list-none items-center gap-1 text-xs text-ra-text-tertiary",
                "hover:text-ra-text-secondary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                "[&::-webkit-details-marker]:hidden",
              )}
            >
              <ChevronRight
                className="h-3 w-3 transition-transform group-open:rotate-90"
                aria-hidden="true"
              />
              目标详情
            </summary>
            <p className="ra-measure mt-2 whitespace-pre-wrap text-sm leading-5 text-ra-text-secondary">
              {objective}
            </p>
          </details>
        ) : null}
      </div>

      <dl
        className="flex flex-wrap items-baseline gap-x-5 gap-y-1 text-xs"
        data-testid="task-level-one-meta"
      >
        <div className="flex items-baseline gap-1.5">
          <dt className="text-ra-text-tertiary">下一步：</dt>
          <dd className="text-ra-text-secondary">{displayTask.nextAction ?? "无待办动作"}</dd>
        </div>
        <div className="flex items-baseline gap-1.5">
          {/* The 6px dt/dd gap read as a fused "阻塞无" next to the 20px group
              gap, so each pair now carries the same `标签：值` colon the rest of
              the product uses (阶段：/ 目标：/ 活跃度：). */}
          <dt className="text-ra-text-tertiary">阻塞项：</dt>
          <dd className="text-ra-text-secondary">{displayTask.blocker ?? "无"}</dd>
        </div>
        <div className="flex items-baseline gap-1.5">
          <dt className="text-ra-text-tertiary">验证：</dt>
          <dd className="text-ra-text-secondary">{testStatusLabel(displayTask.testStatus)}</dd>
        </div>
      </dl>

      <details className="group text-xs" data-testid="task-diagnostics">
        <summary
          className={cn(
            // Same 24px minimum target as the objective disclosure above.
            "inline-flex min-h-6 cursor-pointer list-none items-center gap-1 text-ra-text-tertiary",
            "hover:text-ra-text-secondary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
            "[&::-webkit-details-marker]:hidden",
          )}
        >
          <ChevronRight
            className="h-3 w-3 transition-transform group-open:rotate-90"
            aria-hidden="true"
          />
          诊断信息
        </summary>
        <dl className="mt-2 grid grid-cols-1 gap-x-5 gap-y-2 sm:grid-cols-2 lg:grid-cols-4">
          <Meta label="执行器" value={displayTask.executor ?? "—"} />
          <Meta label="授权" value={authorityStatusLabel(displayTask.authorityStatus)} />
          <Meta
            label="校验命令"
            value={
              displayTask.validationCommandId
                ? `${displayTask.validationCommandId} · ${validationStatusLabel(displayTask.validationExitCode)}`
                : "未记录"
            }
          />
          <Meta label="执行 ID" value={displayTask.executionId ?? "—"} />
          <Meta label="任务 ID" value={displayTask.id} />
        </dl>
      </details>

      {displayTask.functionalValidation && <FunctionalValidationView evidence={displayTask.functionalValidation} executor={displayTask.executor} />}

      {displayTask.draftPr ? (
        <div
          data-testid="task-draft-pr"
          className="flex items-center gap-2 rounded-lg border border-ra-border bg-ra-tertiary/30 px-3 py-2 text-sm"
        >
          <GitPullRequest className="h-4 w-4 text-ra-text-tertiary" aria-hidden="true" />
          <a
            href={displayTask.draftPr.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-ra-accent hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
          >
            Draft PR #{displayTask.draftPr.number}
            <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
          </a>
          {displayTask.draftPr.headSha ? (
            <span className="font-mono text-xs text-ra-text-tertiary">
              {displayTask.draftPr.headSha.slice(0, 8)}
            </span>
          ) : null}
        </div>
      ) : canPublish ? (
        <div className="flex items-center gap-2" data-testid="task-publication-action">
          <button
            type="button"
            aria-label="发布草稿 PR"
            disabled={publication.isPending}
            onClick={() => {
              if (!activeWindow) return;
              publication.mutate({
                windowId: activeWindow.id,
                title: displayTask.title,
                allowedPaths: changedPaths,
              });
            }}
            className={cn(
              "inline-flex items-center gap-2 rounded-md border border-ra-border px-3 py-1.5 text-sm font-medium text-ra-text",
              "hover:bg-ra-tertiary disabled:cursor-not-allowed disabled:opacity-50",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
            )}
          >
            <GitPullRequest className="h-4 w-4" aria-hidden="true" />
            {publication.isPending ? "正在发布草稿 PR…" : "发布草稿 PR"}
          </button>
        </div>
      ) : null}

      {publication.isError ? (
        <p role="alert" className="text-sm text-ra-status-error">
          {publication.error instanceof Error
            ? `发布草稿 PR 失败：${publication.error.message}`
            : "发布草稿 PR 失败"}
        </p>
      ) : null}

      {isDesktop ? (
        <AgentCanvasWorkbenchFrame
          primaryLabel="执行活动"
          secondaryLabel="任务工作台"
          containerRef={splitContainerRef}
          leftWidth={leftWidth}
          isDragging={isDragging}
          primaryHeader={
            <div className="flex min-w-0 items-center gap-2">
              <span className="text-sm font-medium text-ra-text">执行活动</span>
              <span className="text-xs text-ra-text-secondary">
                {displayTask.activity.length} 条事件
              </span>
            </div>
          }
          primaryPane={<ActivityStream events={displayTask.activity} />}
          resizeHandle={
            <ResizeHandle
              onMouseDown={(event) => {
                event.preventDefault();
                setIsDragging(true);
              }}
              onKeyDown={handleResizeKeyDown}
              value={leftWidth}
              min={30}
              max={80}
              controls="desktop-left-panel desktop-right-panel"
              isDragging={isDragging}
            />
          }
          secondaryTabs={
            <RightPanelTabList
              rightTab={rightTab}
              setRightTab={setRightTab}
            />
          }
          secondaryPane={
            <RightPanelContent
              rightTab={rightTab}
              displayTask={displayTask}
              policy={policy}
            />
          }
        />
      ) : (
        <div className="flex flex-col flex-1 overflow-hidden">
          <div
            role="tablist"
            aria-label="移动工作区"
            className="flex items-center gap-1 p-1 border-b border-ra-border overflow-x-auto"
          >
            <MobileTab
              id="activity"
              label="执行活动"
              selected={mobilePane === "activity"}
              onSelect={() => setMobilePane("activity")}
              testId="mobile-pane-activity"
            />
            {RIGHT_TABS.map((tab) => (
              <MobileTab
                key={tab.id}
                id={tab.id}
                label={tab.label}
                icon={tab.icon}
                selected={mobilePane === tab.id}
                onSelect={() => setMobilePane(tab.id)}
                testId={`right-tab-${tab.id}`}
              />
            ))}
          </div>

          <div
            role="tabpanel"
            id={`mobile-panel-${mobilePane}`}
            aria-labelledby={`mobile-tab-${mobilePane}`}
            className="flex-1 overflow-y-auto custom-scrollbar p-4 bg-ra-workspace"
            data-testid="right-panel-content"
            data-active-pane={mobilePane}
          >
            {renderWorkspacePane(mobilePane, displayTask, policy)}
          </div>
        </div>
      )}

      {customEditorOpen ? (
        <CustomPolicyEditor
          open={customEditorOpen}
          policy={editorPolicy ?? profileToPolicy(displayTask.permissionProfile)}
          onChange={setEditorPolicy}
          onClose={() => setCustomEditorOpen(false)}
        />
      ) : null}
    </main>
  );
}

interface MobileTabProps {
  id: MobilePane;
  label: string;
  selected: boolean;
  onSelect: () => void;
  testId: string;
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

function MobileTab({
  id,
  label,
  selected,
  onSelect,
  testId,
  icon: Icon,
}: MobileTabProps) {
  return (
    <button
      type="button"
      role="tab"
      id={`mobile-tab-${id}`}
      aria-selected={selected}
      aria-controls={`mobile-panel-${id}`}
      tabIndex={selected ? 0 : -1}
      onClick={onSelect}
      className={cn(
        "flex shrink-0 items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
        selected
          ? "bg-ra-tertiary text-ra-text"
          : "text-ra-text-tertiary hover:text-ra-text hover:bg-ra-tertiary/50",
      )}
      data-testid={testId}
    >
      {Icon ? (
        <Icon className="h-4 w-4" aria-hidden="true" />
      ) : (
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-4 w-4"
          aria-hidden="true"
        >
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
      )}
      <span>{label}</span>
    </button>
  );
}

function clampWidth(width: number) {
  return Math.max(30, Math.min(80, width));
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-ra-text-tertiary">{label}</dt>
      <dd className="mt-0.5 text-sm text-ra-text-secondary">{value}</dd>
    </div>
  );
}

interface TaskDetailProps {
  task: Task | undefined;
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
}
