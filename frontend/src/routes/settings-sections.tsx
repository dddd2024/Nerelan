import { Link } from "react-router";
import { AgentTeamEditor } from "@/components/agent-team-editor";
import { ResourceOverview } from "@/components/resource-overview";
import { ThemeSelector } from "@/components/theme-selector";
import { useBindings } from "@/hooks/use-model-access";

const SECTIONS = [
  { path: "/settings/resources", title: "AI 资源与账号", description: "本地连接、账号会话、Magpie 与迁移状态" },
  { path: "/settings/models", title: "模型与路由", description: "执行器到模型的绑定；实际使用的模型以运行记录为准" },
  { path: "/settings/usage", title: "用量与额度", description: "查看实际观测和估算用量；未知额度不会显示为零" },
  { path: "/settings/agents", title: "Agent 与执行", description: "配置执行团队及已保存的角色绑定" },
  { path: "/settings/appearance", title: "外观", description: "主题和配色；仅影响当前界面" },
  { path: "/settings/advanced", title: "高级配置", description: "旧版连接与绑定合并编辑器，迁移完成前保留" },
] as const;

export function SettingsHubPage() {
  return (
    <main data-testid="settings-hub" className="h-full overflow-auto bg-ra-workspace px-4 py-5 lg:px-7 lg:py-7 custom-scrollbar">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-lg font-semibold text-ra-text">设置</h1>
        <p className="mt-2 text-sm text-ra-text-secondary">
          按功能管理配置；资源展示模式不会更改真实模型路由或迁移账号。
        </p>
        <nav aria-label="设置分类" className="mt-6 divide-y divide-ra-border border-y border-ra-border">
          {SECTIONS.map((section) => (
            <Link key={section.path} to={section.path}
              className="group flex min-h-16 items-center justify-between gap-4 px-2 py-3 hover:bg-ra-tertiary/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
              <span className="min-w-0">
                <span className="block text-sm font-medium text-ra-text">{section.title}</span>
                <span className="mt-1 block text-xs text-ra-text-secondary">{section.description}</span>
              </span>
              <span aria-hidden="true" className="text-ra-text-tertiary">›</span>
            </Link>
          ))}
        </nav>
      </div>
    </main>
  );
}

function SettingsSubpage({ title, description, children }: {
  title: string; description: string; children: React.ReactNode;
}) {
  return (
    <main data-testid="settings-subpage" className="h-full overflow-auto bg-ra-workspace px-4 py-5 lg:px-7 lg:py-7 custom-scrollbar">
      <div className="mx-auto flex max-w-5xl flex-col gap-5">
        <Link to="/settings" className="self-start text-sm text-ra-text-tertiary hover:text-ra-text hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ra-accent">
          ← 返回设置
        </Link>
        <header>
          <h1 className="text-lg font-semibold text-ra-text">{title}</h1>
          <p className="mt-2 text-sm text-ra-text-secondary">{description}</p>
        </header>
        {children}
      </div>
    </main>
  );
}

export function SettingsUsagePage() {
  return <SettingsSubpage title="用量与额度" description="区分可验证的实际观测与参考价格估算；界面切换不会迁移账户或修改模型路由。">
    <ResourceOverview />
  </SettingsSubpage>;
}

export function SettingsAgentsPage() {
  const bindings = useBindings();
  return <SettingsSubpage title="Agent 与执行" description="团队与角色绑定配置。授权和实际派发仍由 Nerelan 后端控制。">
    {bindings.isError ? (
      <p role="alert" className="text-sm text-ra-status-error">无法读取模型绑定，请检查资源连接。</p>
    ) : (
      <AgentTeamEditor bindings={bindings.data ?? []} />
    )}
  </SettingsSubpage>;
}

export function SettingsAppearancePage() {
  return <SettingsSubpage title="外观" description="只修改本地界面外观，不改变模型、账号、用量或任务权限。">
    <ThemeSelector />
  </SettingsSubpage>;
}
