/**
 * Errors in the words of their real cause. A page opened in an ordinary browser
 * lacks the launcher's client credential and gets 401: that is not "the
 * service is down" and not "task not found".
 *
 * #1555: preserve the actual error class where observable instead of mapping
 * every failure to a generic "cannot reach service" message.  The host sends
 * ``error_class`` and ``retryable`` in error payloads; ``PlatformClientError``
 * carries them so callers can distinguish a slow/busy endpoint from a stopped
 * process or an intentional cancellation.
 */
export const CLIENT_CREDENTIAL_MISSING = "这个窗口没有 Nerelan 的访问凭证：请在 Nerelan 启动器打开的窗口里使用。";

const CODE_MESSAGES: Record<string, string> = {
  owner_selection_confirmation_unavailable: "界面里还不能确认并启动执行窗口：请在终端运行 owner_window 命令启动。",
  owner_window_goal_not_admissible: "这个目标的状态不能开启执行窗口。",
  repository_discovery_failed: "主机读不到 GitHub 仓库列表：常见原因是主机没有登录 GitHub（gh auth login）或网络不通。",
  github_adapter_unavailable: "主机的 GitHub 连接还没准备好，请稍后重试。",
  repository_workspace_unconfigured: "主机还没有配置这个仓库的本地工作区。",
};

export function isCredentialError(status: number | undefined): boolean {
  return status === 401 || status === 403;
}

export function httpErrorMessage(status: number, code = "", errorClass = ""): string {
  if (isCredentialError(status)) return CLIENT_CREDENTIAL_MISSING;
  if (CODE_MESSAGES[code]) return CODE_MESSAGES[code];
  if (errorClass === "cancelled") return "请求已取消，不影响当前内容。";
  if (errorClass === "timeout") return "等待响应超时，请稍后重试。";
  if (errorClass === "invalid_response") return "收到的响应无法读取，请稍后重试。";
  if (code === "busy" || errorClass === "busy") return "Nerelan 正忙，稍后会自动重试。";
  if (errorClass === "server_error") return "Nerelan 服务遇到错误，请稍后重试。";
  if (status === 404) return "请求的内容不存在，可能已被移除。";
  if (status >= 502) return "Nerelan 服务返回错误，请稍后重试。";
  if (status === 0) return "请求未完成，暂时无法确认原因。";
  return code ? `平台请求未完成（${code}）` : `平台请求未完成（HTTP ${status}）`;
}
