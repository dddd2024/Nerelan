import * as React from "react";
import { 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  PlayCircle,
  MoreVertical,
  Trash2,
  Edit,
  Eye
} from "lucide-react";
import { cn } from "@/lib/cn";

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  priority: "low" | "medium" | "high" | "critical";
  createdAt: string;
  updatedAt: string;
  assignee?: string;
  progress?: number;
  tags?: string[];
}

interface TaskCardProps {
  task: Task;
  onSelect?: (task: Task) => void;
  onEdit?: (task: Task) => void;
  onDelete?: (task: Task) => void;
  onView?: (task: Task) => void;
}

const statusConfig = {
  pending: { icon: Clock, color: "text-yellow-500", bg: "bg-yellow-500/10", label: "待处理" },
  running: { icon: PlayCircle, color: "text-blue-500", bg: "bg-blue-500/10", label: "运行中" },
  completed: { icon: CheckCircle, color: "text-emerald-500", bg: "bg-emerald-500/10", label: "已完成" },
  failed: { icon: AlertCircle, color: "text-red-500", bg: "bg-red-500/10", label: "失败" },
  cancelled: { icon: AlertCircle, color: "text-gray-500", bg: "bg-gray-500/10", label: "已取消" }
};

const priorityConfig = {
  low: { color: "text-gray-500", bg: "bg-gray-500/10", label: "低" },
  medium: { color: "text-yellow-500", bg: "bg-yellow-500/10", label: "中" },
  high: { color: "text-orange-500", bg: "bg-orange-500/10", label: "高" },
  critical: { color: "text-red-500", bg: "bg-red-500/10", label: "紧急" }
};

export function TaskCard({ task, onSelect, onEdit, onDelete, onView }: TaskCardProps) {
  const [showActions, setShowActions] = React.useState(false);
  const status = statusConfig[task.status];
  const priority = priorityConfig[task.priority];
  const StatusIcon = status.icon;

  return (
    <div
      className={cn(
        "group relative rounded-xl border border-ra-border bg-ra-light p-4 hover:border-ra-accent/50 transition-all cursor-pointer",
        task.status === "running" && "border-blue-500/30"
      )}
      onClick={() => onSelect?.(task)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={cn("p-1.5 rounded-lg", status.bg)}>
            <StatusIcon className={cn("h-4 w-4", status.color)} />
          </div>
          <div>
            <h3 className="text-sm font-medium text-ra-text line-clamp-1">{task.title}</h3>
            <p className="text-xs text-ra-text-tertiary mt-0.5">{status.label}</p>
          </div>
        </div>
        
        <div className="relative">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowActions(!showActions);
            }}
            className="p-1 rounded-lg hover:bg-ra-tertiary text-ra-text-tertiary hover:text-ra-text opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <MoreVertical className="h-4 w-4" />
          </button>
          
          {showActions && (
            <div className="absolute right-0 top-8 z-10 w-48 rounded-lg border border-ra-border bg-ra-base shadow-lg py-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onView?.(task);
                  setShowActions(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-ra-text-secondary hover:bg-ra-tertiary hover:text-ra-text"
              >
                <Eye className="h-4 w-4" />
                查看详情
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit?.(task);
                  setShowActions(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-ra-text-secondary hover:bg-ra-tertiary hover:text-ra-text"
              >
                <Edit className="h-4 w-4" />
                编辑
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete?.(task);
                  setShowActions(false);
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10"
              >
                <Trash2 className="h-4 w-4" />
                删除
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Description */}
      {task.description && (
        <p className="text-sm text-ra-text-secondary line-clamp-2 mb-3">{task.description}</p>
      )}

      {/* Progress */}
      {task.progress !== undefined && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-ra-text-tertiary mb-1">
            <span>进度</span>
            <span>{task.progress}%</span>
          </div>
          <div className="h-1.5 bg-ra-tertiary rounded-full overflow-hidden">
            <div 
              className="h-full bg-ra-accent rounded-full transition-all duration-300"
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={cn(
            "px-2 py-0.5 rounded-full text-[10px] font-medium",
            priority.bg,
            priority.color
          )}>
            {priority.label}
          </span>
          {task.tags?.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-ra-tertiary text-ra-text-secondary"
            >
              {tag}
            </span>
          ))}
        </div>
        
        <div className="text-xs text-ra-text-tertiary">
          {new Date(task.updatedAt).toLocaleDateString("zh-CN")}
        </div>
      </div>
    </div>
  );
}
