import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import {
  BarChart2,
  FileText,
  GitBranch,
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
import { cn } from "@/lib/cn";
import {
  permissionModeLabel,
  riskTierStyle,
  runStateStyle,
} from "@/lib/format";
import { profileToPolicy } from "@/lib/profile-mapper";
import type { PolicyContract, Task } from "@/types";

type WorkspacePane = "changes" | "evidence" | "authority";
type MobilePane = "activity" | WorkspacePane;

const RIGHT_TABS: {
  id: WorkspacePane;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}[] = [
  { id: "changes", label: "Changed Files", icon: GitBranch },
  { id: "evidence", label: "Evidence", icon: BarChart2 },
  { id: "authority", label: "Authority", icon: ShieldCheck },
];

interface RightPanelTabsProps {
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
function RightPanelTabs({
  rightTab,
  setRightTab,
  displayTask,
  policy,
}: RightPanelTabsProps) {
  return (
    <>
      <div
        role="tablist"
        aria-label="工作区分区"
        className="flex items-center gap-1 p-1 border-b border-ra-border"
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
                "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium",
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

      <div
        role="tabpanel"
        id={`tabpanel-${rightTab}`}
        aria-labelledby={`tab-${rightTab}`}
        className="h-[calc(100%-48px)] overflow-y-auto custom-scrollbar"
        data-testid="right-panel-content"
        data-active-pane={rightTab}
      >
        <div className="p-4">
          {renderWorkspacePane(rightTab, displayTask, policy)}
        </div>
      </div>
    </>
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

  const displayTask = task ?? null;

  if (isLoading) {
    return (
      <div data-testid="task-detail">
        <LoadingState label="加载任务中…" />
      </div>
    );
  }

  if (isError || !displayTask) {
    return (
      <div data-testid="task-detail">
        <ErrorState title="未找到任务" error={error} />
        <div className="px-4">
          <Link
            to="/tasks"
            className="text-sm text-ra-text-tertiary hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
          >
            ← 返回任务列表
          </Link>
        </div>
      </div>
    );
  }

  const state = runStateStyle(displayTask.state);
  const risk = riskTierStyle(displayTask.riskTier);
  const policy = profileToPolicy(displayTask.permissionProfile);

  const stateDotColor =
    {
      "bg-emerald-500": "bg-[#BCFF8C]",
      "bg-sky-500": "bg-[#FFD43B]",
      "bg-amber-500": "bg-[#FFD43B]",
      "bg-orange-500": "bg-[#FFD43B]",
      "bg-rose-500": "bg-ra-status-error",
      "bg-violet-500": "bg-[#A3A3A3]",
      "bg-slate-400": "bg-[#A3A3A3]",
    }[state.dot] ?? "bg-[#A3A3A3]";

  return (
    <div
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
              className="text-ra-text-tertiary hover:text-ra-text focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
            >
              ←
            </Link>
            <span className="text-xs text-ra-text-tertiary font-mono">
              #{displayTask.issueNumber}
            </span>
            <span aria-hidden="true" className="text-ra-text-tertiary">
              ·
            </span>
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
              "rounded-md px-2 py-1 text-xs text-ra-text-tertiary",
              "hover:text-ra-text hover:bg-ra-tertiary",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
            )}
            title="编辑权限策略"
          >
            <FileText className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>
      </div>

      <h1 className="text-lg font-semibold text-ra-text">
        {displayTask.title}
      </h1>

      <div
        className="flex items-center gap-2 mt-2"
        data-testid="task-executor-panel"
      >
        {displayTask.executor ? (
          <span
            className={cn(
              "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
              displayTask.executor === "fixture/provider-free"
                ? "bg-[#BCFF8C]/10 text-[#BCFF8C]"
                : "bg-ra-accent/10 text-ra-accent",
            )}
            title={`executor=${displayTask.executor}`}
          >
            <span className="w-1 h-1 rounded-full bg-current shrink-0" />
            executor: {displayTask.executor}
          </span>
        ) : null}
        {displayTask.validationCommandId ? (
          <span className="text-xs text-ra-text-tertiary">
            validation: {displayTask.validationCommandId}{" "}
            {displayTask.validationExitCode !== undefined
              ? `(exit ${displayTask.validationExitCode})`
              : ""}
          </span>
        ) : null}
        {displayTask.executionId ? (
          <span className="text-xs font-mono text-ra-text-tertiary">
            {displayTask.executionId}
          </span>
        ) : null}
      </div>

      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 text-xs">
        <Meta label="Executor" value={displayTask.executor ?? "—"} />
        <Meta label="下一步" value={displayTask.nextAction ?? "—"} />
        <Meta label="阻塞项" value={displayTask.blocker ?? "无"} />
        <Meta label="Authority" value={displayTask.authorityStatus} />
        <Meta label="测试" value={displayTask.testStatus} />
      </dl>

      {isDesktop ? (
        <div
          ref={splitContainerRef}
          data-testid="desktop-split-container"
          className="flex flex-row flex-1 overflow-hidden"
        >
          <div
            id="desktop-left-panel"
            data-testid="desktop-left-panel"
            className="flex flex-col bg-ra-workspace overflow-hidden flex-1 md:flex-none transition-all duration-300 ease-in-out"
            style={{
              width: `${leftWidth}%`,
              transitionProperty: isDragging ? "none" : "all",
            }}
          >
            <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
              <ActivityStream events={displayTask.activity} />
            </div>
          </div>

          <ResizeHandle
            leftWidth={leftWidth}
            onWidthChange={setLeftWidth}
            splitContainerRef={splitContainerRef}
            onDraggingChange={setIsDragging}
          />

          <div
            id="desktop-right-panel"
            data-testid="desktop-right-panel"
            className="flex flex-col overflow-hidden bg-ra-sidebar flex-1 md:flex-none transition-all duration-300 ease-in-out"
            style={{
              width: `calc(${100 - leftWidth}% - 4px)`,
              minWidth: "240px",
              transitionProperty: isDragging ? "none" : "all",
            }}
          >
            <RightPanelTabs
              rightTab={rightTab}
              setRightTab={setRightTab}
              displayTask={displayTask}
              policy={policy}
            />
          </div>
        </div>
      ) : (
        <div className="flex flex-col flex-1 overflow-hidden">
          <div
            role="tablist"
            aria-label="移动工作区"
            className="flex items-center gap-1 p-1 border-b border-ra-border overflow-x-auto"
          >
            <MobileTab
              id="activity"
              label="Activity"
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
    </div>
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

interface ResizeHandleProps {
  leftWidth: number;
  onWidthChange: (width: number) => void;
  splitContainerRef: React.RefObject<HTMLDivElement | null>;
  onDraggingChange: (dragging: boolean) => void;
}

function clampWidth(width: number) {
  return Math.max(30, Math.min(80, width));
}

/** Mouse- and keyboard-operable separator for the desktop workspace split. */
function ResizeHandle({
  leftWidth,
  onWidthChange,
  splitContainerRef,
  onDraggingChange,
}: ResizeHandleProps) {
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (event: MouseEvent) => {
      const splitContainer = splitContainerRef.current;
      if (!splitContainer) return;

      const rect = splitContainer.getBoundingClientRect();
      if (rect.width <= 0) return;

      const nextWidth = ((event.clientX - rect.left) / rect.width) * 100;
      onWidthChange(clampWidth(nextWidth));
    };

    const stopDragging = () => {
      setIsDragging(false);
      onDraggingChange(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", stopDragging);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", stopDragging);
      onDraggingChange(false);
    };
  }, [isDragging, onDraggingChange, onWidthChange, splitContainerRef]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    switch (event.key) {
      case "ArrowLeft":
        onWidthChange(clampWidth(leftWidth - 5));
        event.preventDefault();
        break;
      case "ArrowRight":
        onWidthChange(clampWidth(leftWidth + 5));
        event.preventDefault();
        break;
      case "Home":
        onWidthChange(30);
        event.preventDefault();
        break;
      case "End":
        onWidthChange(80);
        event.preventDefault();
        break;
    }
  };

  return (
    <div
      className="relative w-1 bg-transparent cursor-ew-resize shrink-0 group"
      onMouseDown={(event) => {
        event.preventDefault();
        setIsDragging(true);
        onDraggingChange(true);
      }}
      role="button"
      tabIndex={0}
      aria-label="开始拖动调整面板大小"
      data-testid="resize-handle-container"
    >
      <div
        role="slider"
        aria-orientation="vertical"
        aria-label="调整面板大小"
        aria-controls="desktop-left-panel desktop-right-panel"
        aria-valuemin={30}
        aria-valuemax={80}
        aria-valuenow={Math.round(leftWidth)}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        className="absolute inset-y-0 left-1/2 w-0.5 -translate-x-1/2 bg-ra-border group-hover:bg-ra-border-foreground focus:outline-none focus-visible:w-1 focus-visible:bg-ra-accent"
        data-testid="resize-handle"
      />
      <div className="absolute inset-y-0 -left-1 -right-1" aria-hidden="true" />
    </div>
  );
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
