import { useEffect, useRef, useState } from "react";
import { 
  Terminal, 
  Copy, 
  Download, 
  Trash2, 
  Search,
  Filter,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { cn } from "@/lib/cn";
import { useTaskUpdates } from "@/hooks/use-websocket";

interface LogEntry {
  id: string;
  timestamp: string;
  level: "info" | "warn" | "error" | "debug" | "success";
  source: string;
  message: string;
  details?: any;
}

interface LiveLogStreamProps {
  taskId: string;
  className?: string;
  maxEntries?: number;
  autoScroll?: boolean;
  showControls?: boolean;
}

export function LiveLogStream({
  taskId,
  className,
  maxEntries = 500,
  autoScroll = true,
  showControls = true,
}: LiveLogStreamProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isExpanded, setIsExpanded] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { logs: wsLogs, isConnected } = useTaskUpdates(taskId);

  useEffect(() => {
    if (wsLogs && wsLogs.length > 0) {
      const newLogs = wsLogs.map((log: any, index: number) => ({
        id: `${Date.now()}-${index}`,
        timestamp: log.timestamp || new Date().toISOString(),
        level: log.level || "info",
        source: log.source || "system",
        message: log.message || "",
        details: log.details,
      }));
      
      setLogs((prev) => {
        const combined = [...prev, ...newLogs];
        return combined.slice(-maxEntries);
      });
    }
  }, [wsLogs, maxEntries]);

  useEffect(() => {
    if (autoScroll && !isPaused && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll, isPaused]);

  const filteredLogs = logs.filter((log) => {
    if (filter !== "all" && log.level !== filter) return false;
    if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  const handleCopyAll = () => {
    const text = filteredLogs
      .map((log) => `[${log.timestamp}] [${log.level.toUpperCase()}] [${log.source}] ${log.message}`)
      .join("\n");
    navigator.clipboard.writeText(text);
  };

  const handleDownload = () => {
    const text = filteredLogs
      .map((log) => `[${log.timestamp}] [${log.level.toUpperCase()}] [${log.source}] ${log.message}`)
      .join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `task-${taskId}-logs.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    setLogs([]);
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "info":
        return "text-blue-400";
      case "warn":
        return "text-amber-300";
      case "error":
        return "text-red-400";
      case "debug":
        return "text-gray-400";
      case "success":
        return "text-emerald-400";
      default:
        return "text-ra-text-secondary";
    }
  };

  const getLevelBadge = (level: string) => {
    switch (level) {
      case "info":
        return "bg-blue-500/20 text-blue-400";
      case "warn":
        return "bg-amber-500/20 text-amber-300";
      case "error":
        return "bg-red-500/20 text-red-400";
      case "debug":
        return "bg-gray-500/20 text-gray-400";
      case "success":
        return "bg-emerald-500/20 text-emerald-400";
      default:
        return "bg-ra-tertiary text-ra-text-secondary";
    }
  };

  return (
    <div className={cn("rounded-xl border border-ra-border bg-ra-light overflow-hidden", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-ra-border bg-ra-tertiary/30">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-ra-accent" />
          <span className="text-sm font-medium text-ra-text">实时日志</span>
          <span className={cn(
            "px-2 py-0.5 rounded-full text-[10px] font-medium",
            isConnected ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
          )}>
            {isConnected ? "已连接" : "断开"}
          </span>
        </div>
        
        {showControls && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={cn(
                "px-2 py-1 rounded text-xs font-medium transition-colors",
                isPaused ? "bg-amber-500/20 text-amber-300" : "bg-ra-tertiary text-ra-text-secondary hover:text-ra-text"
              )}
            >
              {isPaused ? "继续" : "暂停"}
            </button>
            <button
              onClick={handleCopyAll}
              className="p-1.5 rounded hover:bg-ra-tertiary text-ra-text-tertiary hover:text-ra-text"
              title="复制全部"
            >
              <Copy className="h-4 w-4" />
            </button>
            <button
              onClick={handleDownload}
              className="p-1.5 rounded hover:bg-ra-tertiary text-ra-text-tertiary hover:text-ra-text"
              title="下载日志"
            >
              <Download className="h-4 w-4" />
            </button>
            <button
              onClick={handleClear}
              className="p-1.5 rounded hover:bg-ra-tertiary text-ra-text-tertiary hover:text-ra-text"
              title="清空日志"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 rounded hover:bg-ra-tertiary text-ra-text-tertiary hover:text-ra-text"
            >
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </div>
        )}
      </div>

      {isExpanded && (
        <>
          {/* Controls */}
          {showControls && (
            <div className="flex items-center gap-2 px-4 py-2 border-b border-ra-border bg-ra-base/50">
              <div className="relative flex-1 max-w-xs">
                <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-ra-text-tertiary" />
                <input
                  type="text"
                  placeholder="搜索日志..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-7 pr-3 py-1.5 text-xs rounded border border-ra-border bg-ra-base text-ra-text focus:outline-none focus:ring-1 focus:ring-ra-accent"
                />
              </div>
              <div className="flex items-center gap-1">
                {["all", "info", "warn", "error", "success"].map((level) => (
                  <button
                    key={level}
                    onClick={() => setFilter(level)}
                    className={cn(
                      "px-2 py-1 rounded text-[10px] font-medium transition-colors",
                      filter === level
                        ? "bg-ra-accent/20 text-ra-accent"
                        : "text-ra-text-tertiary hover:text-ra-text"
                    )}
                  >
                    {level === "all" ? "全部" : level.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Log entries */}
          <div
            ref={containerRef}
            className="max-h-[400px] overflow-auto font-mono text-xs custom-scrollbar-modern"
          >
            {filteredLogs.length === 0 ? (
              <div className="p-8 text-center text-ra-text-tertiary">
                <Terminal className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>等待日志输出...</p>
              </div>
            ) : (
              filteredLogs.map((log) => (
                <div
                  key={log.id}
                  className={cn(
                    "px-4 py-2 border-b border-ra-border/50 hover:bg-ra-tertiary/30 transition-colors",
                    log.level === "error" && "bg-red-500/5"
                  )}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-ra-text-tertiary shrink-0">
                      {new Date(log.timestamp).toLocaleTimeString("zh-CN")}
                    </span>
                    <span className={cn(
                      "px-1.5 py-0.5 rounded text-[10px] font-medium shrink-0",
                      getLevelBadge(log.level)
                    )}>
                      {log.level.toUpperCase()}
                    </span>
                    <span className="text-ra-accent shrink-0">{log.source}</span>
                    <span className={cn("flex-1", getLevelColor(log.level))}>
                      {log.message}
                    </span>
                  </div>
                  {log.details && (
                    <pre className="mt-2 ml-16 p-2 rounded bg-ra-base text-ra-text-secondary overflow-x-auto">
                      {typeof log.details === "string" 
                        ? log.details 
                        : JSON.stringify(log.details, null, 2)}
                    </pre>
                  )}
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-2 border-t border-ra-border bg-ra-base/50">
            <span className="text-[10px] text-ra-text-tertiary">
              {filteredLogs.length} / {logs.length} 条日志
            </span>
            <span className="text-[10px] text-ra-text-tertiary">
              任务ID: {taskId}
            </span>
          </div>
        </>
      )}
    </div>
  );
}
