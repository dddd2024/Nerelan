import type { DoctorReport } from "@/lib/platform-client";

const COPY: Record<string, { name: string; fix: string; href?: string }> = {
  task_api_reachable: { name: "任务服务", fix: "请重新打开 Nerelan，恢复任务服务连接。" },
  task_store_readable: { name: "任务记录", fix: "请重启 Nerelan，确认任务记录可以读取。" },
  task_store_storage_path: { name: "任务保存位置", fix: "请确认任务数据目录及数据库文件存在且可访问。" },
  runtime_status_available: { name: "平台运行状态", fix: "请重启 Nerelan，恢复平台状态读取。" },
  repository_workspace_readiness: { name: "项目工作目录", fix: "请在创建目标时选择可访问的项目目录。" },
  executor_readiness: { name: "Agent 工具（至少一个）", fix: "请安装并登录至少一个 Agent 工具，再到资源设置检查可用状态。", href: "/settings/resources" },
  executor_opencode: { name: "OpenCode 工具", fix: "请安装 OpenCode 并在资源设置中配置连接。", href: "/settings/resources" },
  executor_codex: { name: "Codex 工具", fix: "请安装并登录 Codex，再检查资源设置中的状态。", href: "/settings/resources" },
  executor_claude_code: { name: "Claude Code 工具", fix: "请安装并登录 Claude Code，或在资源设置中配置连接。", href: "/settings/resources" },
  connection_binding_readiness: { name: "模型连接与绑定", fix: "请在模型设置中为工具选择连接和模型。", href: "/settings/models" },
  desktop_lifecycle_readiness: { name: "桌面服务", fix: "请重新打开 Nerelan，确认桌面服务正常启动。" },
};

export function doctorChecklist(report: DoctorReport) {
  const tools = report.checks.filter((check) => check.component === "executor_tool");
  const anyToolReady = tools.some((check) => check.state === "READY");
  const items = report.checks.map((check) => {
    const tool = check.component === "executor_tool";
    const ready = check.id === "executor_readiness" && tools.length > 0
      ? anyToolReady : check.state === "READY";
    const optional = !check.required || (tool && anyToolReady && !ready);
    const copy = COPY[check.id];
    return {
      id: check.id,
      name: copy?.name ?? check.id,
      state: ready ? "就绪" : optional ? "可选" : "需要处理",
      blocking: !ready && !optional,
      message: copy
        ? ready ? "已就绪，无需处理。"
          : `${check.state === "UNKNOWN" ? "暂时无法自动确认；" : ""}${copy.fix}`
        : check.summary,
      href: copy?.href,
    };
  });
  return { items, needsAttention: items.some((item) => item.blocking) };
}
