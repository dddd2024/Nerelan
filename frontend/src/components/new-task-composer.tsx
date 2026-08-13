import { useState, useCallback, useEffect, useMemo } from "react";
import { Plus, Send, X } from "lucide-react";
import { PermissionSelector } from "@/components/permission-selector";
import { AuthorizationSummary } from "@/components/authorization-summary";
import { CustomPolicyEditor } from "@/components/custom-policy-editor";
import { useBindings } from "@/hooks/use-model-access";
import { useRepositories } from "@/hooks/use-repositories";
import type { Repository } from "@/hooks/use-repositories";
import type { CreateTaskInput } from "@/hooks/use-tasks";
import { profileToPolicy } from "@/lib/profile-mapper";
import type { PolicyContract, PermissionMode } from "@/types";
import { cn } from "@/lib/cn";

export type ExecutorChoice = "opencode" | "deterministic_fixture";

interface ExecutorOption {
  value: ExecutorChoice;
  label: string;
  description: string;
}

const EXECUTOR_OPTIONS: ExecutorOption[] = [
  {
    value: "opencode",
    label: "OpenCode (真实执行)",
    description: "OpenCode · 通过绑定选择模型",
  },
  {
    value: "deterministic_fixture",
    label: "Deterministic Fixture (测试)",
    description: "确定性模拟执行，仅用于测试",
  },
];

interface NewTaskComposerProps {
  open: boolean;
  onClose: () => void;
  onSubmit?: (input: CreateTaskInput) => void | Promise<void>;
}

export function NewTaskComposer({
  open,
  onClose,
  onSubmit,
}: NewTaskComposerProps) {
  const [title, setTitle] = useState("");
  const [executorChoice, setExecutorChoice] = useState<ExecutorChoice>("opencode");
  const [selectedBindingId, setSelectedBindingId] = useState("");
  const [selectedRepositoryUrl, setSelectedRepositoryUrl] = useState("");
  const [permissionMode, setPermissionMode] = useState<PermissionMode>(
    "ASK_FOR_APPROVAL",
  );
  const [customPolicy, setCustomPolicy] = useState<PolicyContract | null>(null);
  const [showCustomEditor, setShowCustomEditor] = useState(false);
  const bindingsQuery = useBindings();
  const reposQuery = useRepositories();
  const opencodeBindings = useMemo(
    () =>
      (bindingsQuery.data ?? []).filter(
        (b) => b.enabled && b.executorId === "opencode",
      ),
    [bindingsQuery.data],
  );
  const repositories: Repository[] = useMemo(
    () => (Array.isArray(reposQuery.data) ? reposQuery.data : []),
    [reposQuery.data],
  );
  const [dataReceived, setDataReceived] = useState(false);
  const [repoDataReceived, setRepoDataReceived] = useState(false);
  const [userInteracted, setUserInteracted] = useState(false);
  const isOpenCode = executorChoice === "opencode";

  useEffect(() => {
    if (dataReceived || userInteracted) {
      return;
    }
    if (bindingsQuery.data === undefined) {
      return;
    }
    const usable = opencodeBindings.length > 0 ? opencodeBindings[0] : null;
    if (usable) {
      setSelectedBindingId(usable.bindingId);
    }
    setDataReceived(true);
  }, [
    bindingsQuery.data,
    opencodeBindings,
    dataReceived,
    userInteracted,
  ]);

  useEffect(() => {
    if (repoDataReceived || userInteracted) return;
    if (reposQuery.data === undefined) return;
    if (repositories.length > 0) {
      setSelectedRepositoryUrl(repositories[0].html_url);
    }
    setRepoDataReceived(true);
  }, [reposQuery.data, repositories, repoDataReceived, userInteracted]);

  const handlePermissionChange = useCallback(
    (mode: PermissionMode) => {
      if (mode === "CUSTOM") {
        setPermissionMode("CUSTOM");
        setShowCustomEditor(true);
      } else {
        setPermissionMode(mode);
        setCustomPolicy(null);
      }
    },
    [],
  );

  const handleCustomPolicyChange = useCallback(
    (updated: PolicyContract) => {
      setCustomPolicy(updated);
    },
    [],
  );

  const handleCustomEditorClose = useCallback(() => {
    setShowCustomEditor(false);
  }, []);

  const handleRepositoryChange = useCallback(
    (event: React.ChangeEvent<HTMLSelectElement>) => {
      setUserInteracted(true);
      const url = event.target.value;
      setSelectedRepositoryUrl(url);
    },
    [],
  );

  if (!open) return null;

  const policy: PolicyContract = customPolicy
    ? customPolicy
    : profileToPolicy(permissionMode);

  const hasValidOpenCodeBinding =
    isOpenCode &&
    opencodeBindings.length > 0 &&
    opencodeBindings.some((b) => b.bindingId === selectedBindingId);

  const hasSelectedRepository =
    isOpenCode && Boolean(selectedRepositoryUrl.trim());

  const canSubmit = isOpenCode
    ? Boolean(title.trim() && hasValidOpenCodeBinding && hasSelectedRepository)
    : Boolean(title.trim());

  const selectedBinding = opencodeBindings.find(
    (b) => b.bindingId === selectedBindingId,
  );

  const selectedRepository = repositories.find(
    (r) => r.html_url === selectedRepositoryUrl,
  );

  return (
    <div
      data-testid="new-task-composer"
      className={cn(
        "fixed inset-0 z-[100] bg-black/80 rounded-xl",
        "flex flex-col md:absolute md:inset-auto md:bottom-4 md:left-4 md:right-4 md:w-[calc(100%-32px)]",
      )}
    >
      <button
        type="button"
        aria-label="关闭"
        tabIndex={-1}
        onClick={onClose}
        className="absolute inset-0 rounded-xl"
      />
      <div className="relative m-4 mt-16 md:mt-0">
        <div
          data-testid="new-task-composer-content"
          className={cn(
            "bg-ra-sidebar box-border content-stretch flex flex-col",
            "items-start justify-center p-4 pt-3 relative rounded-[15px]",
            "w-full max-w-2xl mx-auto",
          )}
        >
          <div className="flex items-center gap-2 w-full mb-2">
            <Plus className="h-4 w-4 text-ra-accent" />
            <h2 className="text-sm font-semibold text-ra-text-secondary">
              新建任务
            </h2>
            <button
              type="button"
              aria-label="关闭"
              onClick={onClose}
              className="ml-auto rounded-md p-1 text-ra-text-tertiary hover:text-ra-text hover:bg-ra-tertiary focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="w-full">
            <label
              htmlFor="task-title"
              className="block text-xs text-ra-text-tertiary mb-1"
            >
              任务标题
            </label>
            <input
              id="task-title"
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="描述您的任务…"
              className={cn(
                "w-full rounded-md border border-ra-border bg-ra-input",
                "px-3 py-1.5 text-sm text-ra-text placeholder-ra-text-tertiary",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
              )}
              data-testid="task-title-input"
            />
          </div>

          <div className="w-full mt-3" data-testid="executor-selector">
            <span className="block text-xs text-ra-text-tertiary mb-1">
              执行器
            </span>
            <div className="flex flex-col gap-1">
              {EXECUTOR_OPTIONS.map((option) => (
                <label
                  key={option.value}
                  data-testid={`executor-option-${option.value}`}
                  aria-label={option.label}
                  className={cn(
                    "flex items-start gap-2 rounded-md border px-3 py-2 cursor-pointer",
                    "border-ra-border focus-within:ring-2 focus-within:ring-ra-accent",
                    executorChoice === option.value
                      ? "border-ra-accent bg-ra-tertiary"
                      : "bg-ra-input",
                  )}
                >
                  <input
                    type="radio"
                    name="task-executor"
                    value={option.value}
                    checked={executorChoice === option.value}
                    onChange={() => {
                      setExecutorChoice(option.value);
                      setUserInteracted(true);
                    }}
                    className="mt-0.5"
                  />
                  <span className="flex flex-col">
                    <span className="text-sm text-ra-text">{option.label}</span>
                    <span className="text-xs text-ra-text-tertiary">
                      {option.description}
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </div>

          {isOpenCode ? (
            <div className="w-full mt-3">
              <div className="w-full mb-3">
                <label
                  htmlFor="task-opencode-binding"
                  className="block text-xs text-ra-text-tertiary mb-1"
                >
                  OpenCode 绑定
                </label>
                <div className="flex flex-col gap-1">
                  <select
                    id="task-opencode-binding"
                    aria-label="OpenCode 绑定"
                    value={selectedBindingId}
                    onChange={(event) => {
                      setUserInteracted(true);
                      setSelectedBindingId(event.target.value);
                    }}
                    disabled={bindingsQuery.isLoading || opencodeBindings.length === 0}
                    data-testid="task-opencode-binding-select"
                    className={cn(
                      "w-full rounded-md border border-ra-border bg-ra-input",
                      "px-3 py-1.5 text-sm text-ra-text",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                      "disabled:cursor-not-allowed disabled:opacity-50",
                    )}
                  >
                    {bindingsQuery.isLoading && <option value="">正在加载…</option>}
                    {!bindingsQuery.isLoading && opencodeBindings.length === 0 && (
                      <option value="">
                        请先在设置中创建 OpenCode 绑定
                      </option>
                    )}
                    {opencodeBindings.map((binding) => (
                      <option key={binding.bindingId} value={binding.bindingId}>
                        {binding.name} · {binding.modelId}
                      </option>
                    ))}
                  </select>
                </div>
                {bindingsQuery.isError && (
                  <p role="alert" className="mt-1 text-xs text-red-300">
                    绑定加载失败
                  </p>
                )}
                {!bindingsQuery.isLoading && opencodeBindings.length === 0 && (
                  <p className="mt-1 text-xs text-amber-300" data-testid="no-binding-hint">
                    没有可用的 OpenCode 绑定，请前往设置创建。
                  </p>
                )}
                {selectedBinding && (
                  <p className="mt-1 text-xs text-ra-text-tertiary" data-testid="selected-binding-info">
                    已选：{selectedBinding.name} · {selectedBinding.modelId}
                  </p>
                )}
              </div>

              <div className="w-full">
                <label
                  htmlFor="task-opencode-repository"
                  className="block text-xs text-ra-text-tertiary mb-1"
                >
                  GitHub 仓库
                </label>
                <div className="flex flex-col gap-1">
                  <select
                    id="task-opencode-repository"
                    aria-label="GitHub 仓库"
                    value={selectedRepositoryUrl}
                    onChange={handleRepositoryChange}
                    disabled={
                      reposQuery.isLoading || repositories.length === 0
                    }
                    data-testid="task-opencode-repository-select"
                    className={cn(
                      "w-full rounded-md border border-ra-border bg-ra-input",
                      "px-3 py-1.5 text-sm text-ra-text",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                      "disabled:cursor-not-allowed disabled:opacity-50",
                    )}
                  >
                    {reposQuery.isLoading && (
                      <option value="">正在加载仓库列表…</option>
                    )}
                    {!reposQuery.isLoading && repositories.length === 0 && (
                      <option value="">
                        无法加载仓库列表，请确认 GitHub 登录状态
                      </option>
                    )}
                    {repositories.map((repo) => (
                      <option
                        key={repo.full_name}
                        value={repo.html_url}
                      >
                        {repo.full_name}{repo.is_private ? " (私有)" : " (公开)"}
                      </option>
                    ))}
                  </select>
                </div>
                {reposQuery.isError && (
                  <p
                    role="alert"
                    className="mt-1 text-xs text-red-300"
                    data-testid="repository-discovery-error"
                  >
                    仓库发现失败：{reposQuery.error?.message ?? "未知错误"}。请确认 GitHub CLI 已登录。
                  </p>
                )}
                {!reposQuery.isLoading && repositories.length === 0 && (
                  <p
                    className="mt-1 text-xs text-amber-300"
                    data-testid="no-repositories-hint"
                  >
                    未找到可用的 GitHub 仓库，请确认 GitHub 登录状态。
                  </p>
                )}
                {selectedRepository && (
                  <p
                    className="mt-1 text-xs text-ra-text-tertiary"
                    data-testid="selected-repository-info"
                  >
                    已选：{selectedRepository.full_name} ·{" "}
                    {selectedRepository.visibility}
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div className="w-full mt-3" />
          )}

          <div className="flex flex-col gap-2 w-full mt-3">
            <PermissionSelector
              value={permissionMode}
              onChange={handlePermissionChange}
              label="权限配置"
              id="permission-mode-composer"
            />
          </div>

          <AuthorizationSummary policy={policy} />

          <div className="flex items-center justify-between w-full mt-3 pt-2 border-t border-ra-border">
            <span className="text-xs text-ra-text-tertiary">
              {permissionModeLabel(permissionMode)}
            </span>
            <button
              type="button"
              data-testid="submit-new-task"
              onClick={() => {
                if (!canSubmit) return;
                const idempotencyKey = crypto.randomUUID();
                void onSubmit?.({
                  title: title.trim(),
                  executorKind: executorChoice,
                  bindingRef: isOpenCode ? selectedBindingId : undefined,
                  repository: isOpenCode ? selectedRepositoryUrl : undefined,
                  permissionProfile: permissionMode,
                  policy,
                  idempotencyKey,
                });
                onClose();
              }}
              disabled={!canSubmit}
              className={cn(
                "flex items-center justify-center rounded-full",
                "border border-ra-text-secondary size-[35px]",
                "hover:bg-ra-tertiary disabled:opacity-50 disabled:cursor-not-allowed",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
              )}
            >
              <Send
                className="h-4 w-4"
                color={canSubmit ? "#ffffff" : "#9299aa"}
              />
            </button>
          </div>
        </div>
      </div>

      {showCustomEditor && (
        <CustomPolicyEditor
          open={showCustomEditor}
          policy={customPolicy || profileToPolicy("CUSTOM")}
          onChange={handleCustomPolicyChange}
          onClose={handleCustomEditorClose}
        />
      )}
    </div>
  );
}

function permissionModeLabel(mode: PermissionMode): string {
  switch (mode) {
    case "ASK_FOR_APPROVAL":
      return "请求批准";
    case "CONTROLLER_REVIEW":
      return "主控代审";
    case "OWNER_CONTROL":
      return "Owner托管";
    case "CUSTOM":
      return "自定义";
  }
}
