import { useState, useCallback } from "react";
import { Plus, Send, X } from "lucide-react";
import { PermissionSelector } from "@/components/permission-selector";
import { AuthorizationSummary } from "@/components/authorization-summary";
import { CustomPolicyEditor } from "@/components/custom-policy-editor";
import { profileToPolicy } from "@/lib/profile-mapper";
import type { PolicyContract, PermissionMode } from "@/types";
import { cn } from "@/lib/cn";

interface NewTaskComposerProps {
  open: boolean;
  onClose: () => void;
}

/**
 * OpenHands 1.8.0 NewConversation / InteractiveChatBox adaptation.
 *
 * Upstream sources:
 *   frontend/src/components/features/home/new-conversation/new-conversation.tsx
 *     (tag 1.8.0) — Card with PlusIcon, "Start from scratch"
 *   frontend/src/components/features/conversation/conversation-main/
 *     chat-interface-wrapper.tsx — dark input container
 *   frontend/src/components/features/chat/components/chat-input-container.tsx
 *     — `bg-[#25272D] rounded-[15px] p-4`
 *   frontend/src/components/features/chat/components/chat-input-row.tsx
 *     — flex-row items-end gap-2, file icon + input + send button
 *   frontend/src/components/features/chat/chat-send-button.tsx
 *     — circular button `rounded-full border border-white size-[35px]`
 *     with ArrowUp icon
 *
 * Structurally ported: dark input container (bg-ra-sidebar, rounded-xl),
 * flex-row layout with left-aligned controls and right-aligned send
 * button. Permission selector integrated inline before the input,
 * mirroring how OpenHands places model/conversation controls in the
 * chat-input-actions area.
 *
 * Modifications: send button triggers task creation with selected
 * permission profile instead of agent runtime. No file upload,
 * no model selection, no slash commands.
 * License: MIT (inherited from OpenHands)
 * /
export function NewTaskComposer({ open, onClose }: NewTaskComposerProps) {
  const [title, setTitle] = useState("");
  const [permissionMode, setPermissionMode] = useState<PermissionMode>(
    "ASK_FOR_APPROVAL",
  );
  const [customPolicy, setCustomPolicy] = useState<PolicyContract | null>(null);
  const [showCustomEditor, setShowCustomEditor] = useState(false);

  if (!open) return null;

  const policy: PolicyContract = customPolicy
    ? customPolicy
    : profileToPolicy(permissionMode);

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

  return (
    <div
      data-testid="new-task-composer"
      className={cn(
        "fixed inset-0 z-[100] bg-black/80 rounded-xl",
        "flex flex-col md:absolute md:inset-auto md:bottom-4 md:left-4 md:right-4 md:w-[calc(100%-32px)]",
      )}
    >
      {/* Backdrop click to close */}
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
              onChange={(e) => setTitle(e.target.value)}
              placeholder="描述您的任务…"
              className={cn(
                "w-full rounded-md border border-ra-border bg-ra-input",
                "px-3 py-1.5 text-sm text-ra-text placeholder-ra-text-tertiary",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                "resize-none custom-scrollbar",
              )}
              data-testid="task-title-input"
            />
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
                onClose();
              }}
              disabled={!title.trim()}
              className={cn(
                "flex items-center justify-center rounded-full",
                "border border-ra-text-secondary size-[35px]",
                "hover:bg-ra-tertiary disabled:opacity-50 disabled:cursor-not-allowed",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
              )}
            >
              <Send
                className="h-4 w-4"
                color={title.trim() ? "#ffffff" : "#9299aa"}
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
