import { useState, useRef, useEffect } from "react";
import { Link } from "react-router";
import type { Task } from "@/types";
import { Badge } from "@/components/badge";
import { ActivityStream } from "@/components/activity-stream";
import { ChangesPanel } from "@/components/changes-panel";
import { EvidencePanel } from "@/components/evidence-panel";
import { PermissionsPanel } from "@/components/permissions-panel";
import { CustomPolicyEditor } from "@/components/custom-policy-editor";
import { LoadingState } from "@/components/loading-state";
import { ErrorState } from "@/components/error-state";
import { profileToPolicy } from "@/lib/profile-mapper";
import {
  riskTierStyle,
  runStateStyle,
  permissionModeLabel,
} from "@/lib/format";
import { cn } from "@/lib/cn";
import { useBreakpoint } from "@/hooks/use-breakpoint";
import {
  ShieldCheck,
  FileText,
  BarChart2,
  GitBranch,
} from "lucide-react";
import type { PolicyContract } from "@/types";

type RightPanelTab = "activity" | "changes" | "evidence" | "authority";
type MobilePane = "activity" | "changes" | "evidence" | "authority";

interface RightPanelTabsProps {
  rightTab: RightPanelTab;
  setRightTab: (t: RightPanelTab) => void;
  displayTask: Task;
  policy: ReturnType<typeof profileToPolicy>;
}

/** Right-panel tab navigation and content panel (desktop two-pane). */
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
        {RIGHT_TABS.map((t) => {
          const TabIcon = t.icon;
          const selected = rightTab === t.id;
          return (
            <button
              key={t.id}
              role="tab"
              id={`tab-${t.id}`}
              aria-selected={selected}
              aria-controls={`tabpanel-${t.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => setRightTab(t.id)}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                selected
                  ? "bg-ra-tertiary text-ra-text"
                  : "text-ra-text-tertiary hover:text-ra-text hover:bg-ra-tertiary/50",
              )}
              data-testid={`right-tab-${t.id}`}
            >
              <TabIcon className="h-4 w-4" />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      <div
        className="h-[calc(100%-48px)] overflow-y-auto custom-scrollbar"
        data-testid="right-panel-content"
      >
        <div className="p-4">
          {rightTab === "changes" && <ChangesPanel changes={displayTask.changes} />}
          {rightTab === "evidence" && <EvidencePanel evidence={displayTask.evidence} />}
          {rightTab === "authority" && <PermissionsPanel policy={policy} />}
        </div>
      </div>
    </>
  );
}

const RIGHT_TABS: { id: RightPanelTab; label: string; icon: React.ComponentType<React.SVGProps<SVGSVGElement>> }[] = [
  { id: "changes", label: "Changed Files", icon: GitBranch },
  { id: "evidence", label: "Evidence", icon: BarChart2 },
  { id: "authority", label: "Authority", icon: ShieldCheck },
];

/**
 * OpenHands ConversationMain + root-layout adaptation for task detail.
 *
 * Desktop (tag 1.8.0): 1024px breakpoint, two-pane resizable horizontal split
 *   (left Activity / right tabs), resize separator between them.
 * Mobile (<1024px): one-pane selector — Activity, Changed Files, Evidence,
 *   Authority — exactly one visible at a time, reversible.
 *
 * Upstream sources:
 *   frontend/src/routes/conversation.tsx (tag 1.8.0)
 *   — `p-3 md:p-0 flex flex-col h-full gap-3`
 *   frontend/src/components/features/conversation/conversation-main/
 *     conversation-main.tsx (tag 1.8.0)
 *   — horizontal resizable split: chat panel (left) + tab panel (right)
 *   — `useResizablePanels` with resize handle between
 *   frontend/src/components/features/conversation/conversation-tabs/
 *     conversation-tabs.tsx (tag 1.8.0)
 *   — dark tab nav with icons
 *
 * Modifications: mobile single-pane selector added; desktop resize uses
 *   accessible separator semantics; permission selector as compact badge.
 *   No agent runtime, sandbox, or websocket.
 * License: MIT (inherited from OpenHands)
 */
export function TaskDetail({ task, isLoading, isError, error }: TaskDetailProps) {
  const [rightTab, setRightTab] = useState<RightPanelTab>("changes");
  const [customEditorOpen, setCustomEditorOpen] = useState(false);
  const [editorPolicy, setEditorPolicy] = useState<PolicyContract | null>(null);

  const bp = useBreakpoint();
  const isDesktop = bp === "desktop";
  const [mobilePane, setMobilePane] = useState<MobilePane>("activity");

  const containerRef = useRef<HTMLDivElement>(null);
  const leftResizeHandleRef = useRef<HTMLDivElement>(null);
  const [leftWidth, setLeftWidth] = useState(55);
  const [isDragging, setIsDragging] = useState(false);

  const displayTask = task ?? null;

  useEffect(() => {
    if (!isDragging) return;
    const onMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const newLeftPercent = ((e.clientX - rect.left) / rect.width) * 100;
      setLeftWidth(Math.max(30, Math.min(80, newLeftPercent)));
    };
    const onMouseUp = () => setIsDragging(false);
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [isDragging]);

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

  const stateDotColor = {
    "bg-emerald-500": "bg-[#BCFF8C]",
    "bg-sky-500": "bg-[#FFD43B]",
    "bg-amber-500": "bg-[#FFD43B]",
    "bg-orange-500": "bg-[#FFD43B]",
    "bg-rose-500": "bg-ra-status-error",
    "bg-violet-500": "bg-[#A3A3A3]",
    "bg-slate-400": "bg-[#A3A3A3]",
  }[state.dot] ?? "bg-[#A3A3A3]";

  function renderPaneContent(pane: MobilePane) {
    if (!displayTask) return null;
    switch (pane) {
      case "activity":
        return <ActivityStream events={displayTask.activity} />;
      case "changes":
        return <ChangesPanel changes={displayTask.changes} />;
      case "evidence":
        return <EvidencePanel evidence={displayTask.evidence} />;
      case "authority":
        return <PermissionsPanel policy={policy} />;
    }
  }

  return (
    <div
      data-testid="task-detail"
      className="flex flex-col h-full gap-3 p-3 md:p-0"
    >
      {/* Header — ConversationNameWithStatus adaptation */}
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
            <span className="font-mono text-xs text-ra-text-tertiary">
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
            <FileText className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Title */}
      <h1 className="text-lg font-semibold text-ra-text">
        {displayTask.title}
      </h1>

      {/* Meta info — ConversationName adaptation */}
      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 text-xs">
        <Meta label="下一步" value={displayTask.nextAction ?? "—"} />
        <Meta label="阻塞项" value={displayTask.blocker ?? "无"} />
        <Meta label="Authority" value={displayTask.authorityStatus} />
        <Meta label="测试" value={displayTask.testStatus} />
      </dl>

      {isDesktop ? (
        <div
          ref={containerRef}
          className="flex flex-row flex-1 overflow-hidden"
          style={{
            transitionProperty: isDragging ? "none" : "all",
          }}
        >
          <div
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
            handleRef={leftResizeHandleRef}
          />

          <div
            data-testid="desktop-right-panel"
            className="flex flex-col overflow-hidden bg-ra-sidebar flex-1 md:flex-none transition-all duration-300 ease-in-out"
            style={{
              width: `calc(${100 - leftWidth}% - 4px)`,
              minWidth: "240px",
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
            className="flex flex-col gap-1 p-1 border-b border-ra-border overflow-x-auto"
          >
            <button
              role="tab"
              id="mobile-tab-activity"
              aria-selected={mobilePane === "activity"}
              aria-controls="mobile-pane-activity"
              tabIndex={mobilePane === "activity" ? 0 : -1}
               onClick={() => setRightTab("activity")}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium w-full text-left",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                mobilePane === "activity"
                  ? "bg-ra-tertiary text-ra-text"
                  : "text-ra-text-tertiary hover:text-ra-text hover:bg-ra-tertiary/50",
              )}
              data-testid="mobile-pane-activity"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                className="h-4 w-4">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
              <span>Activity</span>
            </button>
            {RIGHT_TABS.map((t) => {
              const TabIcon = t.icon;
              const selected = mobilePane === t.id;
              return (
                <button
                  key={t.id}
                  role="tab"
                  id={`mobile-tab-${t.id}`}
                  aria-selected={selected}
                  aria-controls={`mobile-pane-${t.id}`}
                  tabIndex={selected ? 0 : -1}
                   onClick={() => {
                     setRightTab(t.id);
                   }}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium w-full text-left",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    selected
                      ? "bg-ra-tertiary text-ra-text"
                      : "text-ra-text-tertiary hover:text-ra-text hover:bg-ra-tertiary/50",
                  )}
                  data-testid={`mobile-pane-${t.id}`}
                >
                  <TabIcon className="h-4 w-4" />
                  <span>{t.label}</span>
                </button>
              );
            })}
          </div>

          <div
            className="flex-1 overflow-y-auto custom-scrollbar p-4 bg-ra-workspace"
            data-testid="mobile-pane-content"
          >
            {renderPaneContent(mobilePane)}
          </div>

          <div
            className="flex items-center gap-1 p-1 border-b border-ra-border"
          >
            {RIGHT_TABS.map((t) => {
              const TabIcon = t.icon;
              const selected = rightTab === t.id;
              return (
                <button
                  key={t.id}
                  role="tab"
                  id={`tab-${t.id}`}
                  aria-selected={selected}
                  aria-controls={`tabpanel-${t.id}`}
                  tabIndex={selected ? 0 : -1}
                  onClick={() => {
                    setRightTab(t.id);
                    setMobilePane(t.id);
                  }}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                    selected
                      ? "bg-ra-tertiary text-ra-text"
                      : "text-ra-text-tertiary hover:text-ra-text hover:bg-ra-tertiary/50",
                  )}
                  data-testid={`right-tab-${t.id}`}
                >
                  <TabIcon className="h-4 w-4" />
                  <span>{t.label}</span>
                </button>
              );
            })}
          </div>

          <div
            className="h-0 overflow-hidden"
            data-testid="right-panel-content"
          >
            <div className="p-4">
              {rightTab !== mobilePane && rightTab === "changes" && (
                <ChangesPanel changes={displayTask.changes} />
              )}
              {rightTab !== mobilePane && rightTab === "evidence" && (
                <EvidencePanel evidence={displayTask.evidence} />
              )}
              {rightTab !== mobilePane && rightTab === "authority" && (
                <PermissionsPanel policy={policy} />
              )}
            </div>
          </div>
        </div>
      )}

      {customEditorOpen ? (
        <CustomPolicyEditor
          open={customEditorOpen}
          policy={editorPolicy || profileToPolicy(displayTask.permissionProfile)}
          onChange={(updated) => setEditorPolicy(updated)}
          onClose={() => setCustomEditorOpen(false)}
        />
      ) : null}
    </div>
  );
}

interface ResizeHandleProps {
  leftWidth: number;
  onWidthChange: (w: number) => void;
  handleRef: React.RefObject<HTMLDivElement | null>;
}

/**
 * Accessible separator-style resize handle between the left (Activity) and
 * right (tabs) panels.  Draggable by mouse and keyboard-operable via
 * ArrowLeft / ArrowRight / Home / End.
 */
function ResizeHandle({ leftWidth, onWidthChange, handleRef }: ResizeHandleProps) {
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isDragging) return;
    const onMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const newLeftPercent = ((e.clientX - rect.left) / rect.width) * 100;
      onWidthChange(Math.max(30, Math.min(80, newLeftPercent)));
    };
    const onMouseUp = () => setIsDragging(false);
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [isDragging, onWidthChange]);

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "ArrowLeft") {
      onWidthChange(Math.max(30, leftWidth - 5));
      e.preventDefault();
    } else if (e.key === "ArrowRight") {
      onWidthChange(Math.min(80, leftWidth + 5));
      e.preventDefault();
    } else if (e.key === "Home") {
      onWidthChange(30);
      e.preventDefault();
    } else if (e.key === "End") {
      onWidthChange(80);
      e.preventDefault();
    }
  }

  return (
    <div
      ref={containerRef}
      className="relative w-1 bg-transparent cursor-ew-resize shrink-0 group"
      onMouseDown={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      data-testid="resize-handle-container"
    >
      <div
        ref={handleRef}
        role="separator"
        aria-orientation="vertical"
        aria-label="调整面板大小"
        aria-valuemin={30}
        aria-valuemax={80}
        aria-valuenow={leftWidth}
        tabIndex={0}
        onKeyDown={handleKey}
        className="absolute inset-y-0 left-1/2 w-0.5 -translate-x-1/2 bg-ra-border group-hover:bg-ra-border-foreground"
        data-testid="resize-handle"
      />
      <div className="absolute inset-y-0 -left-1 -right-1" />
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
