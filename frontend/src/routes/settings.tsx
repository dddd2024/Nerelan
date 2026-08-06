import { useEffect, useMemo, useState } from "react";
import { Plus, Settings } from "lucide-react";
import { ModelProfileEditor } from "@/components/model-profile-editor";
import {
  useDeleteModelProfile,
  useModelProfiles,
  useSetDefaultModelProfile,
  useTestModelProfile,
  useUpsertModelProfile,
} from "@/hooks/use-model-profiles";
import type {
  ModelProfile,
  ModelProfileInput,
} from "@/schemas/model-profile";
import { cn } from "@/lib/cn";

/**
 * Model configuration workspace adapted from the OpenHands settings pattern.
 * Provider secrets are submitted to the model-control service and are never
 * persisted by this browser UI.
 */
export function SettingsPage() {
  const profilesQuery = useModelProfiles();
  const upsertMutation = useUpsertModelProfile();
  const deleteMutation = useDeleteModelProfile();
  const defaultMutation = useSetDefaultModelProfile();
  const testMutation = useTestModelProfile();

  const profiles = profilesQuery.data ?? [];
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (creating || profiles.length === 0) return;
    if (selectedId && profiles.some((profile) => profile.id === selectedId)) {
      return;
    }
    setSelectedId(
      profiles.find((profile) => profile.isDefault)?.id ?? profiles[0].id,
    );
  }, [creating, profiles, selectedId]);

  const selectedProfile = useMemo<ModelProfile | null>(
    () => profiles.find((profile) => profile.id === selectedId) ?? null,
    [profiles, selectedId],
  );

  const busy =
    upsertMutation.isPending ||
    deleteMutation.isPending ||
    defaultMutation.isPending ||
    testMutation.isPending;

  function clearMessages() {
    setStatus(null);
    setError(null);
  }

  async function handleSave(input: ModelProfileInput) {
    clearMessages();
    try {
      const saved = await upsertMutation.mutateAsync(input);
      setCreating(false);
      setSelectedId(saved.id);
      setStatus("配置已保存");
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  async function handleTest(profileId: string, apiKey?: string) {
    clearMessages();
    try {
      const result = await testMutation.mutateAsync({ profileId, apiKey });
      if (result.ok) {
        setStatus("连接成功");
      } else {
        setError(result.message);
      }
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  async function handleSetDefault(profileId: string) {
    clearMessages();
    try {
      await defaultMutation.mutateAsync(profileId);
      setStatus("已设为默认配置");
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  async function handleDelete(profileId: string) {
    clearMessages();
    try {
      await deleteMutation.mutateAsync(profileId);
      setCreating(false);
      setSelectedId(null);
      setStatus("配置已删除");
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }

  return (
    <div
      data-testid="settings-page"
      className={cn(
        "h-full overflow-auto bg-transparent px-4 py-4 custom-scrollbar",
        "lg:px-[42px] lg:py-[42px]",
      )}
    >
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-5">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-ra-text-tertiary" />
              <h1 className="text-lg font-semibold text-ra-text-secondary">
                模型配置
              </h1>
            </div>
            <p className="mt-2 max-w-2xl text-sm text-ra-text-tertiary">
              管理 OpenAI-compatible 与 LiteLLM 模型入口。Codex ACP
              仅作为执行器选择，登录凭据继续由可信主机单独管理。
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              clearMessages();
              setCreating(true);
              setSelectedId(null);
            }}
            className={cn(
              "inline-flex items-center justify-center gap-2 rounded-md",
              "bg-ra-accent px-3 py-2 text-sm font-medium text-ra-base",
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-white",
            )}
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            新建配置
          </button>
        </header>

        <div className="rounded-lg border border-ra-border bg-ra-secondary px-4 py-3 text-xs text-ra-text-tertiary">
          浏览器不会把 API Key 写入 localStorage、sessionStorage 或任务数据。
          生产模式下，密钥由模型控制服务的进程内存或环境变量提供。
        </div>

        {status && (
          <p role="status" className="text-sm text-green-300">
            {status}
          </p>
        )}
        {error && (
          <p role="alert" className="text-sm text-red-300">
            {error}
          </p>
        )}

        {profilesQuery.isLoading ? (
          <p className="text-sm text-ra-text-tertiary">正在加载模型配置…</p>
        ) : profilesQuery.isError ? (
          <p role="alert" className="text-sm text-red-300">
            {errorMessage(profilesQuery.error)}
          </p>
        ) : (
          <div className="grid min-h-0 grid-cols-1 gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
            <aside className="flex flex-col gap-2 rounded-xl border border-ra-border bg-ra-secondary p-3">
              <h2 className="px-1 text-xs font-semibold uppercase tracking-wide text-ra-text-tertiary">
                已保存配置
              </h2>
              {profiles.length === 0 ? (
                <p className="px-1 py-3 text-sm text-ra-text-tertiary">
                  还没有模型配置。
                </p>
              ) : (
                profiles.map((profile) => (
                  <button
                    key={profile.id}
                    type="button"
                    onClick={() => {
                      clearMessages();
                      setCreating(false);
                      setSelectedId(profile.id);
                    }}
                    className={cn(
                      "flex w-full flex-col gap-1 rounded-lg border px-3 py-2 text-left",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
                      !creating && selectedId === profile.id
                        ? "border-ra-accent bg-ra-tertiary"
                        : "border-transparent hover:border-ra-border hover:bg-ra-tertiary",
                    )}
                  >
                    <span className="flex w-full items-center gap-2">
                      <span className="truncate text-sm font-medium text-ra-text">
                        {profile.name}
                      </span>
                      {profile.isDefault && (
                        <span className="ml-auto rounded-full bg-ra-accent/15 px-2 py-0.5 text-[10px] text-ra-accent">
                          默认
                        </span>
                      )}
                    </span>
                    <span className="truncate text-xs text-ra-text-tertiary">
                      {profile.modelId} · {profile.executor}
                    </span>
                    <span className="text-[10px] text-ra-text-tertiary">
                      密钥：{secretStatusLabel(profile.secretStatus)}
                    </span>
                  </button>
                ))
              )}
            </aside>

            <ModelProfileEditor
              profile={selectedProfile}
              creating={creating}
              busy={busy}
              onSave={handleSave}
              onTest={handleTest}
              onSetDefault={handleSetDefault}
              onDelete={handleDelete}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : "模型配置操作失败";
}

function secretStatusLabel(status: ModelProfile["secretStatus"]): string {
  switch (status) {
    case "environment":
      return "环境变量";
    case "session":
      return "进程会话";
    case "missing":
      return "未配置";
  }
}
