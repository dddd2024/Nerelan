import { useState, useEffect } from "react";
import { 
  Activity, 
  BarChart3, 
  Clock, 
  Cpu, 
  HardDrive, 
  MemoryStick,
  Network,
  TrendingUp,
  AlertTriangle,
  CheckCircle
} from "lucide-react";
import { cn } from "@/lib/cn";
import { Chart, MiniChart } from "@/components/ui/chart";

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: { in: number; out: number };
  uptime: string;
  activeConnections: number;
  requestsPerSecond: number;
  avgResponseTime: number;
  errorRate: number;
}

interface AgentMetrics {
  totalAgents: number;
  activeAgents: number;
  completedTasks: number;
  failedTasks: number;
  totalTokensUsed: number;
  totalCost: string;
  avgTaskDuration: string;
  successRate: number;
}

interface ObservabilityDashboardProps {
  className?: string;
  refreshInterval?: number;
}

export function ObservabilityDashboard({ 
  className,
  refreshInterval = 5000 
}: ObservabilityDashboardProps) {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpu: 35,
    memory: 62,
    disk: 45,
    network: { in: 1250, out: 890 },
    uptime: "3天 12小时",
    activeConnections: 5,
    requestsPerSecond: 12.5,
    avgResponseTime: 230,
    errorRate: 0.5,
  });

  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics>({
    totalAgents: 12,
    activeAgents: 3,
    completedTasks: 156,
    failedTasks: 8,
    totalTokensUsed: 1250000,
    totalCost: "$45.20",
    avgTaskDuration: "2.3分钟",
    successRate: 95.1,
  });

  const [cpuHistory, setCpuHistory] = useState<number[]>([
    30, 35, 42, 38, 45, 40, 35, 32, 38, 42, 45, 40,
  ]);

  const [memoryHistory, setMemoryHistory] = useState<number[]>([
    58, 60, 62, 61, 63, 65, 62, 60, 61, 62, 63, 62,
  ]);

  // 模拟实时数据更新
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics((prev) => ({
        ...prev,
        cpu: Math.min(100, Math.max(0, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.min(100, Math.max(0, prev.memory + (Math.random() - 0.5) * 5)),
        requestsPerSecond: Math.max(0, prev.requestsPerSecond + (Math.random() - 0.5) * 2),
        avgResponseTime: Math.max(100, prev.avgResponseTime + (Math.random() - 0.5) * 50),
      }));

      setCpuHistory((prev) => [...prev.slice(1), systemMetrics.cpu]);
      setMemoryHistory((prev) => [...prev.slice(1), systemMetrics.memory]);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval, systemMetrics.cpu]);

  const cpuChartData = cpuHistory.map((value, index) => ({
    time: index.toString(),
    value,
  }));

  const memoryChartData = memoryHistory.map((value, index) => ({
    time: index.toString(),
    value,
  }));

  const getMetricColor = (value: number, threshold: number = 80) => {
    if (value >= threshold) return "text-red-400";
    if (value >= threshold * 0.7) return "text-amber-300";
    return "text-emerald-400";
  };

  const getMetricBg = (value: number, threshold: number = 80) => {
    if (value >= threshold) return "bg-red-500/20";
    if (value >= threshold * 0.7) return "bg-amber-500/20";
    return "bg-emerald-500/20";
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* System Metrics */}
      <div className="rounded-xl border border-ra-border bg-ra-light p-6">
        <h2 className="text-lg font-medium text-ra-text mb-4 flex items-center gap-2">
          <Cpu className="h-5 w-5 text-ra-accent" />
          系统资源
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricCard
            icon={<Cpu className="h-4 w-4" />}
            label="CPU 使用率"
            value={`${Math.round(systemMetrics.cpu)}%`}
            color={getMetricColor(systemMetrics.cpu)}
            bgColor={getMetricBg(systemMetrics.cpu)}
          />
          <MetricCard
            icon={<MemoryStick className="h-4 w-4" />}
            label="内存使用率"
            value={`${Math.round(systemMetrics.memory)}%`}
            color={getMetricColor(systemMetrics.memory)}
            bgColor={getMetricBg(systemMetrics.memory)}
          />
          <MetricCard
            icon={<HardDrive className="h-4 w-4" />}
            label="磁盘使用率"
            value={`${Math.round(systemMetrics.disk)}%`}
            color={getMetricColor(systemMetrics.disk)}
            bgColor={getMetricBg(systemMetrics.disk)}
          />
          <MetricCard
            icon={<Network className="h-4 w-4" />}
            label="网络流量"
            value={`${(systemMetrics.network.in / 1000).toFixed(1)} MB/s`}
            color="text-ra-accent"
            bgColor="bg-ra-accent/10"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-medium text-ra-text mb-3">CPU 使用趋势</h3>
            <Chart
              data={cpuChartData}
              lines={[{ key: "value", color: "#60a5fa", name: "CPU %" }]}
              height={150}
            />
          </div>
          <div>
            <h3 className="text-sm font-medium text-ra-text mb-3">内存使用趋势</h3>
            <Chart
              data={memoryChartData}
              lines={[{ key: "value", color: "#10b981", name: "Memory %" }]}
              height={150}
            />
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="rounded-xl border border-ra-border bg-ra-light p-6">
        <h2 className="text-lg font-medium text-ra-text mb-4 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-ra-accent" />
          性能指标
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            icon={<Activity className="h-4 w-4" />}
            label="请求/秒"
            value={systemMetrics.requestsPerSecond.toFixed(1)}
            color="text-ra-accent"
            bgColor="bg-ra-accent/10"
          />
          <MetricCard
            icon={<Clock className="h-4 w-4" />}
            label="平均响应时间"
            value={`${Math.round(systemMetrics.avgResponseTime)}ms`}
            color={systemMetrics.avgResponseTime > 500 ? "text-amber-300" : "text-emerald-400"}
            bgColor={systemMetrics.avgResponseTime > 500 ? "bg-amber-500/20" : "bg-emerald-500/20"}
          />
          <MetricCard
            icon={<AlertTriangle className="h-4 w-4" />}
            label="错误率"
            value={`${systemMetrics.errorRate.toFixed(2)}%`}
            color={systemMetrics.errorRate > 1 ? "text-red-400" : "text-emerald-400"}
            bgColor={systemMetrics.errorRate > 1 ? "bg-red-500/20" : "bg-emerald-500/20"}
          />
          <MetricCard
            icon={<TrendingUp className="h-4 w-4" />}
            label="活跃连接"
            value={systemMetrics.activeConnections.toString()}
            color="text-ra-accent"
            bgColor="bg-ra-accent/10"
          />
        </div>
      </div>

      {/* Agent Metrics */}
      <div className="rounded-xl border border-ra-border bg-ra-light p-6">
        <h2 className="text-lg font-medium text-ra-text mb-4 flex items-center gap-2">
          <Activity className="h-5 w-5 text-ra-accent" />
          Agent 指标
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricCard
            icon={<Activity className="h-4 w-4" />}
            label="活跃 Agent"
            value={`${agentMetrics.activeAgents} / ${agentMetrics.totalAgents}`}
            color="text-blue-400"
            bgColor="bg-blue-500/20"
          />
          <MetricCard
            icon={<CheckCircle className="h-4 w-4" />}
            label="成功率"
            value={`${agentMetrics.successRate}%`}
            color={agentMetrics.successRate > 90 ? "text-emerald-400" : "text-amber-300"}
            bgColor={agentMetrics.successRate > 90 ? "bg-emerald-500/20" : "bg-amber-500/20"}
          />
          <MetricCard
            icon={<TrendingUp className="h-4 w-4" />}
            label="完成任务"
            value={agentMetrics.completedTasks.toString()}
            color="text-emerald-400"
            bgColor="bg-emerald-500/20"
          />
          <MetricCard
            icon={<Clock className="h-4 w-4" />}
            label="平均任务时长"
            value={agentMetrics.avgTaskDuration}
            color="text-ra-accent"
            bgColor="bg-ra-accent/10"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-ra-tertiary/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-ra-text-secondary">Token 使用量</span>
              <span className="text-sm font-medium text-ra-text">
                {(agentMetrics.totalTokensUsed / 1000000).toFixed(2)}M
              </span>
            </div>
            <div className="h-2 bg-ra-base rounded-full overflow-hidden">
              <div
                className="h-full bg-ra-accent rounded-full"
                style={{ width: `${Math.min(100, (agentMetrics.totalTokensUsed / 2000000) * 100)}%` }}
              />
            </div>
          </div>
          <div className="p-4 rounded-lg bg-ra-tertiary/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-ra-text-secondary">总成本</span>
              <span className="text-sm font-medium text-ra-text">{agentMetrics.totalCost}</span>
            </div>
            <div className="h-2 bg-ra-base rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-400 rounded-full"
                style={{ width: `${Math.min(100, (parseFloat(agentMetrics.totalCost.replace("$", "")) / 100) * 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ 
  icon, 
  label, 
  value, 
  color, 
  bgColor 
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
  bgColor: string;
}) {
  return (
    <div className={cn("p-4 rounded-lg border border-ra-border/50", bgColor)}>
      <div className="flex items-center gap-2 mb-2">
        <div className={color}>{icon}</div>
        <span className="text-xs text-ra-text-secondary">{label}</span>
      </div>
      <p className={cn("text-2xl font-bold", color)}>{value}</p>
    </div>
  );
}
