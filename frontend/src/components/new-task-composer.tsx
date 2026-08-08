import { useState, useCallback, useEffect } from "react";
import { Plus, Send, X } from "lucide-react";
import { PermissionSelector } from "@/components/permission-selector";
import { AuthorizationSummary } from "@/components/authorization-summary";
import { CustomPolicyEditor } from "@/components/custom-policy-editor";
import { useModelProfiles } from "@/hooks/use-model-profiles";
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
    description: "OpenCode · Host configured model",
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

/**
 * OpenHands 1.8.0 NewConversation / InteractiveChatBox adaptation.
 *
 * The composer binds each new task to an executor. In OpenCode mode the
 * task is executed by the host-configured OpenCode session; the frontend
 * does not require, send, or display a model-control profile id for
 * OpenCode. In deterministic_fixture mode the existing mock/provider-free
 * path remains explicit and requires a model profile for compatibility.
 */
export function NewTaskComposer({
  open,
  onClose,
  onSubmit,
}: NewTaskComposerProps) {
  const [title, setTitle] = useState("");
  const [modelProfileId, setModelProfileId] = useState("coding-default");
  const [executorChoice, setExecutorChoice] = useState<ExecutorChoice>("opencode");
  const [permissionMode, setPermissionMode] = useState<PermissionMode>(
    "ASK_FOR_APPROVAL",
  );
  const [customPolicy, setCustomPolicy] = useState<PolicyContract | null>(null);
  const [showCustomEditor, setShowCustomEditor] = useState(false);
  const profilesQuery = useModelProfiles();
  const enabledProfiles = (profilesQuery.data ?? []).filter(
    (profile) => profile.enabled,
  );
  const isOpenCode = executorChoice === "opencode";

  useEffect(() => {
    const requestedDefault = enabledProfiles.find((profile) => profile.isDefault);
    const fallback = requestedDefault ?? enabledProfiles[0];
    if (fallback) {
      setModelProfileId(fallback.id);
    } else if (enabledProfiles.length === 0) {
      setModelProfileId("");
    }
  }, [enabledProfiles]);

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

  if (!open) return null;

  const policy: PolicyContract = customPolicy
    ? customPolicy
    : profileToPolicy(permissionMode);
  const canSubmit = isOpenCode
    ? Boolean(title.trim())
    : Boolean(title.trim() && modelProfileId);

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
                    onChange={() => setExecutorChoice(option.value)}
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
            {isOpenCode && (
              <p
                data-testid="opencode-model-note"
                className="mt-1 text-xs text-ra-text-tertiary"
              >
                模型由本机 OpenCode 配置提供
              </p>
            )}
          </div>

          <div className="w-full mt-3">
            <label
              htmlFor="task-model-profile"
              className="block text-xs text-ra-text-tertiary mb-1"
            >
              模型配置
            </label>
            <div className="flex flex-col gap-1">
              <select
                id="task-model-profile"
                aria-label="模型配置"
                value={modelProfileId}
                onChange={(event) => setModelProfileId(event.target.value)}
                disabled={
                  isOpenCode || profilesQuery.isLoading || enabledProfiles.length === 0
                }
                data-testid="task-model-profile-select"
                className={cn(
                  "w-full rounded-md border border-ra-border bg-ra-input",
                  "px-3 py-1.5 text-sm text-ra-text",
                  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                )}
              >
                {profilesQuery.isLoading && <option value="">正在加载…</option>}
                {!profilesQuery.isLoading && enabledProfiles.length === 0 && (
                  <option value="">请先在设置中创建模型配置</option>
                )}
                {enabledProfiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name} · {profile.modelId}
                  </option>
                ))}
              </select>
            </div>
            {profilesQuery.isError && (
              <p role="alert" className="mt-1 text-xs text-red-300">
                {profilesQuery.error instanceof Error
                  ? profilesQuery.error.message
                  : "模型配置加载失败"}
              </p>
            )}
          </div>

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
                  modelProfileId,
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
