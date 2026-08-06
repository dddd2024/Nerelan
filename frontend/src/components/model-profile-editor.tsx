import { useEffect, useState, type FormEvent } from "react";
import { CheckCircle2, PlugZap, Save, Star, Trash2 } from "lucide-react";
import {
  ModelProfileInputSchema,
  type ModelExecutor,
  type ModelProfile,
  type ModelProfileInput,
  type ModelProvider,
} from "@/schemas/model-profile";
import { cn } from "@/lib/cn";

interface ModelProfileEditorProps {
  profile: ModelProfile | null;
  creating: boolean;
  busy: boolean;
  onSave: (input: ModelProfileInput) => Promise<void>;
  onTest: (profileId: string, apiKey?: string) => Promise<void>;
  onSetDefault: (profileId: string) => Promise<void>;
  onDelete: (profileId: string) => Promise<void>;
}

const EMPTY_PROFILE: ModelProfileInput = {
  id: "",
  name: "",
  provider: "litellm-proxy",
  baseUrl: "http://localhost:4000/v1",
  modelId: "",
  executor: "openhands",
  enabled: true,
  isDefault: false,
};

export function ModelProfileEditor({
  profile,
  creating,
  busy,
  onSave,
  onTest,
  onSetDefault,
  onDelete,
}: ModelProfileEditorProps) {
  const [draft, setDraft] = useState<ModelProfileInput>(EMPTY_PROFILE);
  const [apiKey, setApiKey] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    setDraft(
      profile
        ? {
            id: profile.id,
            name: profile.name,
            provider: profile.provider,
            baseUrl: profile.baseUrl,
            modelId: profile.modelId,
            executor: profile.executor,
            enabled: profile.enabled,
            isDefault: profile.isDefault,
          }
        : EMPTY_PROFILE,
    );
    setApiKey("");
    setValidationError(null);
  }, [profile, creating]);

  function update<K extends keyof ModelProfileInput>(
    key: K,
    value: ModelProfileInput[K],
  ) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = ModelProfileInputSchema.safeParse({
      ...draft,
      ...(apiKey ? { apiKey } : {}),
    });
    if (!parsed.success) {
      setValidationError(parsed.error.issues[0]?.message ?? "配置无效");
      return;
    }
    setValidationError(null);
    await onSave(parsed.data);
    setApiKey("");
  }

  const savedProfileId = creating ? null : profile?.id ?? null;

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-4 rounded-xl border border-ra-border bg-ra-secondary p-4"
      data-testid="model-profile-editor"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-ra-text">
            {creating ? "新建模型配置" : profile?.name ?? "选择模型配置"}
          </h2>
          <p className="mt-1 text-xs text-ra-text-tertiary">
            API Key 只发送到模型控制服务，不写入浏览器存储。
          </p>
        </div>
        {profile?.isDefault && !creating && (
          <span className="inline-flex items-center gap-1 rounded-full border border-ra-accent px-2 py-1 text-xs text-ra-accent">
            <Star className="h-3 w-3" aria-hidden="true" />
            默认配置
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="配置 ID">
          <input
            aria-label="配置 ID"
            value={draft.id}
            disabled={!creating}
            onChange={(event) => update("id", event.target.value)}
            className={inputClass}
            autoComplete="off"
          />
        </Field>
        <Field label="配置名称">
          <input
            aria-label="配置名称"
            value={draft.name}
            onChange={(event) => update("name", event.target.value)}
            className={inputClass}
            autoComplete="off"
          />
        </Field>
        <Field label="Provider">
          <select
            aria-label="Provider"
            value={draft.provider}
            onChange={(event) =>
              update("provider", event.target.value as ModelProvider)
            }
            className={inputClass}
          >
            <option value="litellm-proxy">LiteLLM Proxy</option>
            <option value="openai-compatible">OpenAI Compatible</option>
          </select>
        </Field>
        <Field label="执行器">
          <select
            aria-label="执行器"
            value={draft.executor}
            onChange={(event) =>
              update("executor", event.target.value as ModelExecutor)
            }
            className={inputClass}
          >
            <option value="openhands">OpenHands</option>
            <option value="codex-acp">Codex ACP</option>
          </select>
        </Field>
        <Field label="Base URL" className="md:col-span-2">
          <input
            aria-label="Base URL"
            value={draft.baseUrl}
            onChange={(event) => update("baseUrl", event.target.value)}
            className={inputClass}
            inputMode="url"
            autoComplete="url"
          />
        </Field>
        <Field label="Model ID">
          <input
            aria-label="Model ID"
            value={draft.modelId}
            onChange={(event) => update("modelId", event.target.value)}
            className={inputClass}
            autoComplete="off"
          />
        </Field>
        <Field label="API Key 环境变量">
          <input
            aria-label="API Key 环境变量"
            value={draft.apiKeyEnv ?? ""}
            onChange={(event) =>
              update("apiKeyEnv", event.target.value || undefined)
            }
            className={inputClass}
            placeholder="例如 SENSENOVA_API_KEY"
            autoComplete="off"
          />
        </Field>
        <Field label="API Key（仅本次提交）" className="md:col-span-2">
          <input
            aria-label="API Key（仅本次提交）"
            type="password"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            className={inputClass}
            autoComplete="new-password"
            placeholder={
              profile?.secretStatus === "missing"
                ? "尚未配置"
                : "已配置；留空表示不替换"
            }
          />
        </Field>
      </div>

      <label className="inline-flex items-center gap-2 text-sm text-ra-text-secondary">
        <input
          type="checkbox"
          checked={draft.enabled}
          onChange={(event) => update("enabled", event.target.checked)}
        />
        启用该配置
      </label>

      {validationError && (
        <p role="alert" className="text-sm text-red-300">
          {validationError}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2 border-t border-ra-border pt-3">
        <button type="submit" disabled={busy} className={primaryButtonClass}>
          <Save className="h-4 w-4" aria-hidden="true" />
          保存配置
        </button>
        <button
          type="button"
          disabled={!savedProfileId || busy}
          onClick={() =>
            savedProfileId ? onTest(savedProfileId, apiKey || undefined) : undefined
          }
          className={secondaryButtonClass}
        >
          <PlugZap className="h-4 w-4" aria-hidden="true" />
          测试连接
        </button>
        <button
          type="button"
          disabled={!savedProfileId || profile?.isDefault || busy}
          onClick={() =>
            savedProfileId ? onSetDefault(savedProfileId) : undefined
          }
          className={secondaryButtonClass}
        >
          <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
          设为默认
        </button>
        <button
          type="button"
          disabled={!savedProfileId || busy}
          onClick={() =>
            savedProfileId ? onDelete(savedProfileId) : undefined
          }
          className={cn(secondaryButtonClass, "md:ml-auto text-red-300")}
        >
          <Trash2 className="h-4 w-4" aria-hidden="true" />
          删除配置
        </button>
      </div>
    </form>
  );
}

function Field({
  label,
  className,
  children,
}: {
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <label className={cn("flex flex-col gap-1", className)}>
      <span className="text-xs font-medium text-ra-text-tertiary">{label}</span>
      {children}
    </label>
  );
}

const inputClass = cn(
  "w-full rounded-md border border-ra-border bg-ra-input px-3 py-2",
  "text-sm text-ra-text placeholder:text-ra-text-tertiary",
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
  "disabled:cursor-not-allowed disabled:opacity-60",
);

const primaryButtonClass = cn(
  "inline-flex items-center gap-2 rounded-md bg-ra-accent px-3 py-2",
  "text-sm font-medium text-ra-base disabled:cursor-not-allowed disabled:opacity-50",
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-white",
);

const secondaryButtonClass = cn(
  "inline-flex items-center gap-2 rounded-md border border-ra-border px-3 py-2",
  "text-sm text-ra-text-secondary hover:bg-ra-tertiary hover:text-ra-text",
  "disabled:cursor-not-allowed disabled:opacity-50",
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent",
);
