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

interface NewTaskComposerProps {
  open: boolean;
  onClose: () => void;
  onSubmit?: (input: CreateTaskInput) => void | Promise<void>;
}

/**
 * OpenHands 1.8.0 NewConversation / InteractiveChatBox adaptation.
 *
 * The composer binds each new task to a saved model profile. It does not
 * receive or persist provider credentials; those remain in the trusted-host
 * model-control service.
 */
export function NewTaskComposer({
  open,
  onClose,
  onSubmit,
}: NewTaskComposerProps) {
  const [title, setTitle] = useState("");
  const [modelProfileId, setModelProfileId] = useState("");
  const [permissionMode, setPermissionMode] = useState<PermissionMode>(
    "ASK_FOR_APPROVAL",
  );
  const [customPolicy, setCustomPolicy] = useState<PolicyContract | null>(null);
  const [showCustomEditor, setShowCustomEditor] = useState(false);
  const profilesQuery = useModelProfiles();
  const enabledProfiles = (profilesQuery.data ?? []).filter(
    (profile) => profile.enabled,
  );

  useEffect(() => {
    if (
      modelProfileId &&
      enabledProfiles.some((profile) => profile.id === modelProfileId)
    ) {
      return;
    }
    setModelProfileId(
      enabledProfiles.find((profile) => profile.isDefault)?.id ??
        enabledProfiles[0]?.id ??
        "",
    );
  }, [enabledProfiles, modelProfileId]);

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
  const canSubmit = Boolean(title.trim() && modelProfileId);

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

          <div className="w-full mt-3">
            <label
              htmlFor="task-model-profile"
              className="block text-xs text-ra-text-tertiary mb-1"
            >
              模型配置
            </label>
            <select
              id="task-model-profile"
              aria-label="模型配置"
              value={modelProfileId}
              onChange={(event) => setModelProfileId(event.target.value)}
              disabled={profilesQuery.isLoading || enabledProfiles.length === 0}
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
                void onSubmit?.({
                  title: title.trim(),
                  modelProfileId,
                  permissionProfile: permissionMode,
                  policy,
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
