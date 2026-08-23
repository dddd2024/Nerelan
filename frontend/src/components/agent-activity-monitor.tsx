import { useState, useEffect } from "react";
import { 
  Activity, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  PlayCircle,
  PauseCircle,
  MoreVertical,
  Eye,
  RotateCcw,
  XCircle
} from "lucide-react";
import { cn } from "@/lib/cn";

interface AgentActivity {
  agentId: string;
  agentName: string;
  role: string;
  status: "idle" | "running" | "completed" | "failed" | "paused";
  currentTask?: string;
  progress?: number;
  startedAt?: string;
  lastUpdate: string;
  tokensUsed?: number;
  cost?: string;
}

interface AgentActivityMonitorProps {
  taskId: string;
  className?: string;
}

const mockAgents: AgentActivity[] = [
  {
    agentId: "planner-001",
    agentName: "规划师",
    role: "Planner",
    status: "completed",
    currentTask: "分析需求并制定执行计划",
    progress: 100,
    startedAt: "2026-08-23T10:00:00Z",
    lastUpdate: "2026-08-23T10:02:30Z",
    tokensUsed: 1250,
    cost: "$0.02",
  },
  {
    agentId: "coder-001",
    agentName: "编码师",
    role: "Coder",
    status: "running",
    currentTask: "实现用户认证模块",
    progress: 65,
    startedAt: "2026-08-23T10:03:00Z",
    lastUpdate: "2026-08-23T10:15:45Z",
    tokensUsed: 3420,
    cost: "$0.08",
  },
  {
    agentId: "reviewer-001",
    agentName: "审查员",
    role: "Reviewer",
    status: "idle",
    lastUpdate: "2026-08-23T10:00:00Z",
  },
  {
    agentId: "validator-001",
    agentName: "验证器",
    role: "Validator",
    status: "idle",
    lastUpdate: "2026-08-23T10:00:00Z",
  },
];

export function AgentActivityMonitor({ taskId, className }: AgentActivityMonitorProps) {
  const [agents, setAgents] = useState<AgentActivity[]>(mockAgents);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // 模拟实时更新
  useEffect(() => {
    const interval = setInterval(() => {
      setAgents((prev) =>
        prev.map((agent) => {
          if (agent.status === "running" && agent.progress !== undefined) {
            const newProgress = Math.min(100, agent.progress + Math.random() * 5);
            return {
              ...agent,
              progress: newProgress,
              lastUpdate: new Date().toISOString(),
              tokensUsed: (agent.tokensUsed || 0) + Math.floor(Math.random() * 100),
            };
          }
          return agent;
        })
      );
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <PlayCircle className="h-4 w-4 text-blue-400" />;
      case "completed":
        return <CheckCircle className="h-4 w-4 text-emerald-400" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-400" />;
      case "paused":
        return <PauseCircle className="h-4 w-4 text-amber-300" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "border-blue-500/30 bg-blue-500/10";
      case "completed":
        return "border-emerald-500/30 bg-emerald-500/10";
      case "failed":
        return "border-red-500/30 bg-red-500/10";
      case "paused":
        return "border-amber-500/30 bg-amber-500/10";
      default:
        return "border-gray-500/30 bg-gray-500/10";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "running":
        return "运行中";
      case "completed":
        return "已完成";
      case "failed":
        return "失败";
      case "paused":
        return "已暂停";
      default:
        return "空闲";
    }
  };

  const activeAgents = agents.filter((a) => a.status === "running");
  const completedAgents = agents.filter((a) => a.status === "completed");
  const totalTokens = agents.reduce((sum, a) => sum + (a.tokensUsed || 0), 0);

  return (
    <div className={cn("rounded-xl border border-ra-border bg-ra-light overflow-hidden", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-ra-border bg-ra-tertiary/30">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-ra-accent" />
          <span className="text-sm font-medium text-ra-text">Agent 活动监控</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-ra-text-secondary">
          <span>
            <span className="text-blue-400 font-medium">{activeAgents.length}</span> 运行中
          </span>
          <span>
            <span className="text-emerald-400 font-medium">{completedAgents.length}</span> 已完成
          </span>
          <span>
            <span className="text-ra-accent font-medium">{totalTokens.toLocaleString()}</span> tokens
          </span>
        </div>
      </div>

      {/* Agent List */}
      <div className="divide-y divide-ra-border/50">
        {agents.map((agent) => (
          <div
            key={agent.agentId}
            className={cn(
              "px-4 py-3 hover:bg-ra-tertiary/30 transition-colors cursor-pointer",
              selectedAgent === agent.agentId && "bg-ra-tertiary/20"
            )}
            onClick={() => setSelectedAgent(
              selectedAgent === agent.agentId ? null : agent.agentId
            )}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn("p-1.5 rounded-lg", getStatusColor(agent.status))}>
                  {getStatusIcon(agent.status)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-ra-text">{agent.agentName}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-ra-tertiary text-ra-text-secondary">
                      {agent.role}
                    </span>
                  </div>
                  {agent.currentTask && (
                    <p className="text-xs text-ra-text-secondary mt-1 line-clamp-1">
                      {agent.currentTask}
                    </p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                {agent.progress !== undefined && agent.status === "running" && (
                  <div className="w-24">
                    <div className="flex justify-between text-[10px] text-ra-text-tertiary mb-1">
                      <span>{Math.round(agent.progress)}%</span>
                    </div>
                    <div className="h-1 bg-ra-tertiary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-400 rounded-full transition-all duration-300"
                        style={{ width: `${agent.progress}%` }}
                      />
                    </div>
                  </div>
                )}
                
                <div className="text-right">
                  <span className={cn(
                    "text-[10px] font-medium px-2 py-0.5 rounded-full",
                    getStatusColor(agent.status)
                  )}>
                    {getStatusText(agent.status)}
                  </span>
                  {agent.tokensUsed && (
                    <p className="text-[10px] text-ra-text-tertiary mt-1">
                      {agent.tokensUsed.toLocaleString()} tokens
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Expanded Details */}
            {selectedAgent === agent.agentId && (
              <div className="mt-3 pt-3 border-t border-ra-border/50">
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-ra-text-tertiary">开始时间</span>
                    <p className="text-ra-text mt-1">
                      {agent.startedAt 
                        ? new Date(agent.startedAt).toLocaleTimeString("zh-CN")
                        : "—"}
                    </p>
                  </div>
                  <div>
                    <span className="text-ra-text-tertiary">最后更新</span>
                    <p className="text-ra-text mt-1">
                      {new Date(agent.lastUpdate).toLocaleTimeString("zh-CN")}
                    </p>
                  </div>
                  <div>
                    <span className="text-ra-text-tertiary">Token使用量</span>
                    <p className="text-ra-text mt-1">
                      {(agent.tokensUsed || 0).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <span className="text-ra-text-tertiary">预估成本</span>
                    <p className="text-ra-text mt-1">{agent.cost || "—"}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 mt-3">
                  <button className="flex items-center gap-1 px-2 py-1 rounded text-[10px] text-ra-text-secondary hover:bg-ra-tertiary">
                    <Eye className="h-3 w-3" />
                    查看详情
                  </button>
                  {agent.status === "running" && (
                    <button className="flex items-center gap-1 px-2 py-1 rounded text-[10px] text-amber-300 hover:bg-amber-500/10">
                      <PauseCircle className="h-3 w-3" />
                      暂停
                    </button>
                  )}
                  {agent.status === "failed" && (
                    <button className="flex items-center gap-1 px-2 py-1 rounded text-[10px] text-ra-accent hover:bg-ra-accent/10">
                      <RotateCcw className="h-3 w-3" />
                      重试
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-ra-border bg-ra-base/50">
        <span className="text-[10px] text-ra-text-tertiary">
          任务ID: {taskId}
        </span>
        <span className="text-[10px] text-ra-text-tertiary">
          {agents.length} 个Agent
        </span>
      </div>
    </div>
  );
}
