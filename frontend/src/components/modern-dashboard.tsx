import { useState, useEffect } from "react";
import { 
  Activity, 
  Zap, 
  Target, 
  Clock, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  PlayCircle,
  Settings,
  RefreshCw
} from "lucide-react";
import { cn } from "@/lib/cn";

interface DashboardStats {
  activeTasks: number;
  completedTasks: number;
  successRate: number;
  avgResponseTime: string;
  tokenUsage: number;
  costToday: string;
}

interface RecentActivity {
  id: string;
  type: "task_completed" | "task_started" | "error" | "warning";
  message: string;
  timestamp: string;
  agent?: string;
}

interface SystemStatus {
  coordinator: "online" | "offline" | "maintenance";
  agents: number;
  lastHeartbeat: string;
  uptime: string;
}

export function ModernDashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    activeTasks: 3,
    completedTasks: 47,
    successRate: 94.5,
    avgResponseTime: "2.3s",
    tokenUsage: 125400,
    costToday: "$12.45"
  });

  const [activities, setActivities] = useState<RecentActivity[]>([
    {
      id: "1",
      type: "task_completed",
      message: "代码重构任务完成",
      timestamp: "2分钟前",
      agent: "CodeAgent"
    },
    {
      id: "2",
      type: "task_started",
      message: "开始执行测试任务",
      timestamp: "5分钟前",
      agent: "TestAgent"
    },
    {
      id: "3",
      type: "warning",
      message: "API调用接近速率限制",
      timestamp: "10分钟前",
      agent: "MonitorAgent"
    },
    {
      id: "4",
      type: "task_completed",
      message: "文档生成任务完成",
      timestamp: "15分钟前",
      agent: "DocAgent"
    }
  ]);

  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    coordinator: "online",
    agents: 5,
    lastHeartbeat: "刚刚",
    uptime: "3天 12小时"
  });

  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // 模拟刷新数据
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsRefreshing(false);
  };

  return (
    <div className="min-h-full bg-[var(--oh-surface)] px-4 py-7 sm:px-8 lg:px-12 lg:py-10">
      <div className="mx-auto max-w-[1400px]">
        {/* 头部区域 */}
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-ra-text-tertiary">
              Agent 控制中心
            </p>
            <h1 className="mt-2 text-3xl font-medium tracking-[-0.025em] text-ra-text sm:text-4xl">
              仪表板
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-ra-text-secondary">
              实时监控您的多Agent系统状态、性能指标和任务进度。
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg border border-ra-border bg-ra-light/50 text-sm text-ra-text-secondary hover:bg-ra-light transition-colors",
                isRefreshing && "opacity-50 cursor-not-allowed"
              )}
            >
              <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
              刷新
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-ra-accent text-ra-base text-sm font-medium hover:bg-ra-accent-hover transition-colors">
              <PlayCircle className="h-4 w-4" />
              新建任务
            </button>
          </div>
        </header>

        {/* 状态卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatusCard
            title="活跃任务"
            value={stats.activeTasks.toString()}
            icon={<Activity className="h-5 w-5" />}
            trend="+2"
            trendUp={true}
            color="blue"
          />
          <StatusCard
            title="已完成任务"
            value={stats.completedTasks.toString()}
            icon={<CheckCircle className="h-5 w-5" />}
            trend="+12"
            trendUp={true}
            color="green"
          />
          <StatusCard
            title="成功率"
            value={`${stats.successRate}%`}
            icon={<Target className="h-5 w-5" />}
            trend="+1.2%"
            trendUp={true}
            color="purple"
          />
          <StatusCard
            title="平均响应时间"
            value={stats.avgResponseTime}
            icon={<Clock className="h-5 w-5" />}
            trend="-0.3s"
            trendUp={true}
            color="orange"
          />
        </div>

        {/* 主要内容区域 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* 系统状态 */}
          <div className="lg:col-span-1 rounded-xl border border-ra-border bg-ra-light p-6">
            <h2 className="text-lg font-medium text-ra-text mb-4 flex items-center gap-2">
              <Zap className="h-5 w-5 text-ra-accent" />
              系统状态
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-ra-text-secondary">协调器</span>
                <span className={cn(
                  "flex items-center gap-2 text-sm font-medium",
                  systemStatus.coordinator === "online" ? "text-emerald-400" : "text-amber-300"
                )}>
                  <span className={cn(
                    "h-2 w-2 rounded-full",
                    systemStatus.coordinator === "online" ? "bg-emerald-400" : "bg-amber-300"
                  )} />
                  {systemStatus.coordinator === "online" ? "在线" : "离线"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ra-text-secondary">活跃Agent</span>
                <span className="text-sm font-medium text-ra-text">{systemStatus.agents} 个</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ra-text-secondary">最后心跳</span>
                <span className="text-sm text-ra-text">{systemStatus.lastHeartbeat}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ra-text-secondary">运行时间</span>
                <span className="text-sm text-ra-text">{systemStatus.uptime}</span>
              </div>
            </div>
            
            <div className="mt-6 pt-4 border-t border-ra-border">
              <h3 className="text-sm font-medium text-ra-text mb-3">资源使用</h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs text-ra-text-secondary mb-1">
                    <span>Token使用量</span>
                    <span>{(stats.tokenUsage / 1000).toFixed(1)}K / 200K</span>
                  </div>
                  <div className="h-2 bg-ra-tertiary rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-ra-accent rounded-full" 
                      style={{ width: `${(stats.tokenUsage / 200000) * 100}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs text-ra-text-secondary mb-1">
                    <span>今日成本</span>
                    <span>{stats.costToday} / $50.00</span>
                  </div>
                  <div className="h-2 bg-ra-tertiary rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-emerald-400 rounded-full" 
                      style={{ width: `${(parseFloat(stats.costToday.replace('$', '')) / 50) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 最近活动 */}
          <div className="lg:col-span-2 rounded-xl border border-ra-border bg-ra-light p-6">
            <h2 className="text-lg font-medium text-ra-text mb-4 flex items-center gap-2">
              <Activity className="h-5 w-5 text-ra-accent" />
              最近活动
            </h2>
            <div className="space-y-3">
              {activities.map((activity) => (
                <ActivityItem key={activity.id} activity={activity} />
              ))}
            </div>
          </div>
        </div>

        {/* 快速操作 */}
        <div className="rounded-xl border border-ra-border bg-ra-light p-6">
          <h2 className="text-lg font-medium text-ra-text mb-4 flex items-center gap-2">
            <Zap className="h-5 w-5 text-ra-accent" />
            快速操作
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <QuickAction
              title="创建新任务"
              description="启动一个新的Agent任务"
              icon={<PlayCircle className="h-6 w-6" />}
              color="blue"
              onClick={() => {}}
            />
            <QuickAction
              title="查看运行历史"
              description="浏览过去的Agent执行记录"
              icon={<Clock className="h-6 w-6" />}
              color="green"
              onClick={() => {}}
            />
            <QuickAction
              title="系统设置"
              description="配置Agent和系统参数"
              icon={<Settings className="h-6 w-6" />}
              color="purple"
              onClick={() => {}}
            />
            <QuickAction
              title="性能监控"
              description="查看详细的性能指标"
              icon={<TrendingUp className="h-6 w-6" />}
              color="orange"
              onClick={() => {}}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusCard({ 
  title, 
  value, 
  icon, 
  trend, 
  trendUp, 
  color 
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
  trend: string;
  trendUp: boolean;
  color: "blue" | "green" | "purple" | "orange";
}) {
  const colorClasses = {
    blue: "text-blue-400 bg-blue-400/10",
    green: "text-emerald-400 bg-emerald-400/10",
    purple: "text-purple-400 bg-purple-400/10",
    orange: "text-orange-400 bg-orange-400/10"
  };

  return (
    <div className="rounded-xl border border-ra-border bg-ra-light p-6 hover:border-ra-accent/50 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className={cn("p-2 rounded-lg", colorClasses[color])}>
          {icon}
        </div>
        <span className={cn(
          "text-xs font-medium px-2 py-1 rounded-full",
          trendUp ? "text-emerald-400 bg-emerald-400/10" : "text-red-400 bg-red-400/10"
        )}>
          {trend}
        </span>
      </div>
      <div>
        <h3 className="text-2xl font-bold text-ra-text">{value}</h3>
        <p className="text-sm text-ra-text-secondary mt-1">{title}</p>
      </div>
    </div>
  );
}

function ActivityItem({ activity }: { activity: RecentActivity }) {
  const iconMap = {
    task_completed: <CheckCircle className="h-4 w-4 text-emerald-400" />,
    task_started: <PlayCircle className="h-4 w-4 text-blue-400" />,
    error: <AlertCircle className="h-4 w-4 text-red-400" />,
    warning: <AlertCircle className="h-4 w-4 text-amber-300" />
  };

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-ra-tertiary/50 transition-colors">
      <div className="mt-0.5">
        {iconMap[activity.type]}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-ra-text">{activity.message}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-ra-text-tertiary">{activity.timestamp}</span>
          {activity.agent && (
            <>
              <span className="text-xs text-ra-text-tertiary">·</span>
              <span className="text-xs text-ra-accent">{activity.agent}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function QuickAction({ 
  title, 
  description, 
  icon, 
  color, 
  onClick 
}: {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: "blue" | "green" | "purple" | "orange";
  onClick: () => void;
}) {
  const colorClasses = {
    blue: "text-blue-400 hover:border-blue-400/50",
    green: "text-emerald-400 hover:border-emerald-400/50",
    purple: "text-purple-400 hover:border-purple-400/50",
    orange: "text-orange-400 hover:border-orange-400/50"
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex flex-col items-start p-4 rounded-xl border border-ra-border bg-ra-base hover:bg-ra-tertiary/50 transition-all text-left",
        colorClasses[color]
      )}
    >
      <div className="mb-3">{icon}</div>
      <h3 className="text-sm font-medium text-ra-text">{title}</h3>
      <p className="text-xs text-ra-text-secondary mt-1">{description}</p>
    </button>
  );
}
