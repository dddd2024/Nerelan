import { useState } from "react";
import { 
  ArrowLeft, 
  PlayCircle, 
  PauseCircle, 
  RotateCcw, 
  Trash2,
  Settings,
  Eye,
  Clock,
  CheckCircle,
  AlertCircle
} from "lucide-react";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";
import { LiveLogStream } from "@/components/live-log-stream";
import { AgentActivityMonitor } from "@/components/agent-activity-monitor";
import { useTaskSSE } from "@/hooks/use-sse";

interface TaskDetailViewProps {
  taskId: string;
  onBack?: () => void;
}

export function TaskDetailView({ taskId, onBack }: TaskDetailViewProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "logs" | "agents" | "settings">("overview");
  
  const { 
    taskUpdate, 
    agentStatus, 
    progress, 
    result,
    isConnected 
  } = useTaskSSE(taskId);

  const tabs = [
    { id: "overview", label: "概览", icon: Eye },
    { id: "logs", label: "日志", icon: Settings },
    { id: "agents", label: "Agent", icon: PlayCircle },
    { id: "settings", label: "设置", icon: Settings },
  ];

  return (
    <div className="min-h-full bg-[var(--oh-surface)]">
      {/* Header */}
      <div className="border-b border-ra-border bg-ra-light/50">
        <div className="max-w-[1400px] mx-auto px-4 py-4 sm:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {onBack && (
                <button
                  onClick={onBack}
                  className="p-2 rounded-lg hover:bg-ra-tertiary text-ra-text-secondary hover:text-ra-text"
                >
                  <ArrowLeft className="h-5 w-5" />
                </button>
              )}
              <div>
                <h1 className="text-xl font-semibold text-ra-text">任务详情</h1>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-sm text-ra-text-secondary">任务ID: {taskId}</span>
                  <span className={cn(
                    "px-2 py-0.5 rounded-full text-[10px] font-medium",
                    isConnected ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                  )}>
                    {isConnected ? "实时连接" : "离线"}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <PauseCircle className="h-4 w-4 mr-2" />
                暂停
              </Button>
              <Button variant="outline" size="sm">
                <RotateCcw className="h-4 w-4 mr-2" />
                重试
              </Button>
              <Button variant="destructive" size="sm">
                <Trash2 className="h-4 w-4 mr-2" />
                删除
              </Button>
            </div>
          </div>
          
          {/* Progress Bar */}
          {progress > 0 && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-ra-text-secondary mb-2">
                <span>执行进度</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="h-2 bg-ra-tertiary rounded-full overflow-hidden">
                <div
                  className="h-full bg-ra-accent rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-ra-border bg-ra-base">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-8">
          <nav className="flex gap-1 -mb-px">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                  activeTab === tab.id
                    ? "border-ra-accent text-ra-accent"
                    : "border-transparent text-ra-text-secondary hover:text-ra-text hover:border-ra-border"
                )}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-[1400px] mx-auto px-4 py-6 sm:px-8">
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Task Info */}
            <div className="rounded-xl border border-ra-border bg-ra-light p-6">
              <h2 className="text-lg font-medium text-ra-text mb-4">任务信息</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-ra-text-secondary">状态</label>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={cn(
                      "px-2 py-0.5 rounded-full text-[10px] font-medium",
                      taskUpdate?.status === "running" 
                        ? "bg-blue-500/20 text-blue-400"
                        : taskUpdate?.status === "completed"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-gray-500/20 text-gray-400"
                    )}>
                      {taskUpdate?.status || "pending"}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-ra-text-secondary">创建时间</label>
                  <p className="text-sm text-ra-text mt-1">
                    {taskUpdate?.created_at 
                      ? new Date(taskUpdate.created_at).toLocaleString("zh-CN")
                      : "—"}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-ra-text-secondary">最后更新</label>
                  <p className="text-sm text-ra-text mt-1">
                    {taskUpdate?.updated_at 
                      ? new Date(taskUpdate.updated_at).toLocaleString("zh-CN")
                      : "—"}
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="rounded-xl border border-ra-border bg-ra-light p-6">
              <h2 className="text-lg font-medium text-ra-text mb-4">快速统计</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-ra-tertiary/30">
                  <p className="text-2xl font-bold text-ra-accent">{progress}%</p>
                  <p className="text-xs text-ra-text-secondary">完成进度</p>
                </div>
                <div className="p-3 rounded-lg bg-ra-tertiary/30">
                  <p className="text-2xl font-bold text-emerald-400">
                    {agentStatus?.agents_active || 0}
                  </p>
                  <p className="text-xs text-ra-text-secondary">活跃Agent</p>
                </div>
                <div className="p-3 rounded-lg bg-ra-tertiary/30">
                  <p className="text-2xl font-bold text-blue-400">
                    {agentStatus?.tokens_used || 0}
                  </p>
                  <p className="text-xs text-ra-text-secondary">Token使用</p>
                </div>
                <div className="p-3 rounded-lg bg-ra-tertiary/30">
                  <p className="text-2xl font-bold text-purple-400">
                    {agentStatus?.cost || "$0.00"}
                  </p>
                  <p className="text-xs text-ra-text-secondary">预估成本</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "logs" && (
          <LiveLogStream taskId={taskId} />
        )}

        {activeTab === "agents" && (
          <AgentActivityMonitor taskId={taskId} />
        )}

        {activeTab === "settings" && (
          <div className="rounded-xl border border-ra-border bg-ra-light p-6">
            <h2 className="text-lg font-medium text-ra-text mb-4">任务设置</h2>
            <p className="text-sm text-ra-text-secondary">
              任务设置功能正在开发中...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
