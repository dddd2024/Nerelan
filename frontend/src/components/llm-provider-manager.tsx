import { useState } from "react";
import { 
  Plus, 
  Trash2, 
  Edit, 
  Check, 
  X, 
  TestTube,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle
} from "lucide-react";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";

interface LLMProvider {
  id: string;
  name: string;
  type: "openai" | "anthropic" | "google" | "ollama" | "custom";
  apiKey?: string;
  baseUrl?: string;
  models: string[];
  isEnabled: boolean;
  lastTested?: string;
  testStatus?: "success" | "failed" | "pending";
}

interface LLMProviderManagerProps {
  providers?: LLMProvider[];
  onAdd?: (provider: Omit<LLMProvider, "id">) => void;
  onUpdate?: (id: string, provider: Partial<LLMProvider>) => void;
  onDelete?: (id: string) => void;
  onTest?: (id: string) => void;
}

const defaultProviders: LLMProvider[] = [
  {
    id: "openai-1",
    name: "OpenAI",
    type: "openai",
    models: ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
    isEnabled: true,
    testStatus: "success",
  },
  {
    id: "anthropic-1",
    name: "Anthropic",
    type: "anthropic",
    models: ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
    isEnabled: true,
    testStatus: "success",
  },
  {
    id: "ollama-1",
    name: "Ollama (本地)",
    type: "ollama",
    baseUrl: "http://localhost:11434",
    models: ["llama2", "codellama", "mistral"],
    isEnabled: false,
    testStatus: "pending",
  },
];

const providerTypes = [
  { value: "openai", label: "OpenAI", color: "text-emerald-400" },
  { value: "anthropic", label: "Anthropic", color: "text-purple-400" },
  { value: "google", label: "Google AI", color: "text-blue-400" },
  { value: "ollama", label: "Ollama (本地)", color: "text-amber-300" },
  { value: "custom", label: "自定义", color: "text-gray-400" },
];

export function LLMProviderManager({
  providers = defaultProviders,
  onAdd,
  onUpdate,
  onDelete,
  onTest,
}: LLMProviderManagerProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [newProvider, setNewProvider] = useState<Partial<LLMProvider>>({
    type: "openai",
    name: "",
    apiKey: "",
    baseUrl: "",
    models: [],
  });

  const handleAdd = () => {
    if (newProvider.name && newProvider.type) {
      onAdd?.(newProvider as Omit<LLMProvider, "id">);
      setNewProvider({ type: "openai", name: "", apiKey: "", baseUrl: "", models: [] });
      setIsAdding(false);
    }
  };

  const getProviderIcon = (type: string) => {
    switch (type) {
      case "openai":
        return <span className="text-emerald-400 font-bold">O</span>;
      case "anthropic":
        return <span className="text-purple-400 font-bold">A</span>;
      case "google":
        return <span className="text-blue-400 font-bold">G</span>;
      case "ollama":
        return <span className="text-amber-300 font-bold">L</span>;
      default:
        return <span className="text-gray-400 font-bold">?</span>;
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-emerald-400" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-400" />;
      default:
        return <span className="h-4 w-4 rounded-full bg-ra-tertiary" />;
    }
  };

  return (
    <div className="rounded-xl border border-ra-border bg-ra-light overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-ra-border bg-ra-tertiary/30">
        <div>
          <h3 className="text-sm font-medium text-ra-text">LLM 提供商管理</h3>
          <p className="text-xs text-ra-text-secondary mt-0.5">
            {providers.length} 个提供商，{providers.filter((p) => p.isEnabled).length} 个已启用
          </p>
        </div>
        <Button
          variant="default"
          size="sm"
          onClick={() => setIsAdding(true)}
        >
          <Plus className="h-4 w-4 mr-1" />
          添加提供商
        </Button>
      </div>

      {/* Add new provider form */}
      {isAdding && (
        <div className="px-4 py-3 border-b border-ra-border bg-ra-base/50">
          <div className="flex items-center gap-2 mb-3">
            <h4 className="text-sm font-medium text-ra-text">添加新提供商</h4>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-ra-text-secondary">类型</label>
              <select
                value={newProvider.type}
                onChange={(e) => setNewProvider({ ...newProvider, type: e.target.value as any })}
                className="w-full mt-1 px-3 py-1.5 text-sm rounded border border-ra-border bg-ra-base text-ra-text focus:outline-none focus:ring-1 focus:ring-ra-accent"
              >
                {providerTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-ra-text-secondary">名称</label>
              <input
                type="text"
                value={newProvider.name}
                onChange={(e) => setNewProvider({ ...newProvider, name: e.target.value })}
                placeholder="例如：My OpenAI"
                className="w-full mt-1 px-3 py-1.5 text-sm rounded border border-ra-border bg-ra-base text-ra-text focus:outline-none focus:ring-1 focus:ring-ra-accent"
              />
            </div>
            <div>
              <label className="text-xs text-ra-text-secondary">API Key</label>
              <input
                type="password"
                value={newProvider.apiKey}
                onChange={(e) => setNewProvider({ ...newProvider, apiKey: e.target.value })}
                placeholder="sk-..."
                className="w-full mt-1 px-3 py-1.5 text-sm rounded border border-ra-border bg-ra-base text-ra-text focus:outline-none focus:ring-1 focus:ring-ra-accent"
              />
            </div>
            <div>
              <label className="text-xs text-ra-text-secondary">Base URL (可选)</label>
              <input
                type="text"
                value={newProvider.baseUrl}
                onChange={(e) => setNewProvider({ ...newProvider, baseUrl: e.target.value })}
                placeholder="https://api.openai.com/v1"
                className="w-full mt-1 px-3 py-1.5 text-sm rounded border border-ra-border bg-ra-base text-ra-text focus:outline-none focus:ring-1 focus:ring-ra-accent"
              />
            </div>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <Button variant="default" size="sm" onClick={handleAdd}>
              <Check className="h-4 w-4 mr-1" />
              保存
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setIsAdding(false)}>
              <X className="h-4 w-4 mr-1" />
              取消
            </Button>
          </div>
        </div>
      )}

      {/* Provider list */}
      <div className="divide-y divide-ra-border/50">
        {providers.map((provider) => (
          <div key={provider.id} className="px-4 py-3 hover:bg-ra-tertiary/30 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "w-8 h-8 rounded-lg flex items-center justify-center",
                  "bg-ra-tertiary"
                )}>
                  {getProviderIcon(provider.type)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-ra-text">{provider.name}</span>
                    {getStatusIcon(provider.testStatus)}
                  </div>
                  <p className="text-xs text-ra-text-secondary mt-0.5">
                    {providerTypes.find((t) => t.value === provider.type)?.label}
                    {provider.models.length > 0 && ` · ${provider.models.length} 个模型`}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onTest?.(provider.id)}
                  className="p-1.5 rounded hover:bg-ra-tertiary text-ra-text-tertiary hover:text-ra-text"
                  title="测试连接"
                >
                  <TestTube className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setExpandedId(expandedId === provider.id ? null : provider.id)}
                  className="p-1.5 rounded hover:bg-ra-tertiary text-ra-text-tertiary hover:text-ra-text"
                >
                  {expandedId === provider.id ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Expanded details */}
            {expandedId === provider.id && (
              <div className="mt-3 pt-3 border-t border-ra-border/50">
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-ra-text-tertiary">状态</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={cn(
                        "w-2 h-2 rounded-full",
                        provider.isEnabled ? "bg-emerald-400" : "bg-gray-400"
                      )} />
                      <span className="text-ra-text">
                        {provider.isEnabled ? "已启用" : "已禁用"}
                      </span>
                    </div>
                  </div>
                  <div>
                    <span className="text-ra-text-tertiary">最后测试</span>
                    <p className="text-ra-text mt-1">
                      {provider.lastTested
                        ? new Date(provider.lastTested).toLocaleString("zh-CN")
                        : "未测试"}
                    </p>
                  </div>
                  <div className="col-span-2">
                    <span className="text-ra-text-tertiary">模型</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {provider.models.map((model) => (
                        <span
                          key={model}
                          className="px-2 py-0.5 rounded bg-ra-tertiary text-ra-text-secondary text-[10px]"
                        >
                          {model}
                        </span>
                      ))}
                    </div>
                  </div>
                  {provider.baseUrl && (
                    <div className="col-span-2">
                      <span className="text-ra-text-tertiary">Base URL</span>
                      <p className="text-ra-text mt-1 font-mono text-[10px]">
                        {provider.baseUrl}
                      </p>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center gap-2 mt-3">
                  <Button variant="outline" size="sm">
                    <Edit className="h-3 w-3 mr-1" />
                    编辑
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onUpdate?.(provider.id, { isEnabled: !provider.isEnabled })}
                  >
                    {provider.isEnabled ? "禁用" : "启用"}
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => onDelete?.(provider.id)}
                  >
                    <Trash2 className="h-3 w-3 mr-1" />
                    删除
                  </Button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-ra-border bg-ra-base/50">
        <p className="text-[10px] text-ra-text-tertiary">
          API Key 安全存储在本地，不会上传到任何服务器。
        </p>
      </div>
    </div>
  );
}
