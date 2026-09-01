Nerelan — 逆向工程能力（兼容 GUI / Harness）

Nerelan 是当前产品名称。本文件说明仓库中仍保留的逆向工程能力、兼容入口与安全边界。

一、品牌与兼容标识

当前品牌：Nerelan
当前 GitHub 仓库：dddd2024/Nerelan
逆向工程能力：Nerelan Reverse Engineering

以下名称仍作为技术兼容标识保留，不代表当前品牌名称或当前 canonical GitHub 仓库身份：

- 旧 GitHub 仓库 slug / GitHub redirect：dddd2024/reverse-agent
- Python 包 / import namespace：reverse_agent
- 环境变量前缀：REVERSE_AGENT_*
- 兼容状态目录 / key：.reverse-agent、reverse-agent.appearance
- 兼容启动器文件名：launch_reverse_agent.bat

BRAND-2B 之后，新的产品默认值、当前文档和未来治理 authority 使用 `dddd2024/Nerelan`。不得为了字符串统一而重命名上述技术兼容接口，也不得回写历史 Decisions、执行报告、旧分支、SHA 或证据。

二、推荐启动方式

主平台：

  launch_reverse_agent.bat

或：

  powershell -ExecutionPolicy Bypass -File .\dev-up.ps1

兼容逆向 GUI：

  python app.py

GUI 当前以 Nerelan 逆向工程能力呈现。

三、逆向工程能力

- 本地 EXE / URL 输入。
- Auto / Static Analysis / Dynamic Debug 三种分析模式。
- IDA、OllyDbg 及相关自动化脚本集成。
- 可选运行时候选验证。
- CTF / 逆向 Skill 提示增强。
- 可复现 Harness、断点续跑、样本级结果与聚合统计。
- solve_reports\ 下的报告、证据与工具 artifact。
- project_state\ 下的轻量协作状态与审计接口。

四、Harness

示例：

  python -m reverse_agent.harness --dataset .\cases.json --run-name smoke_suite --analysis-mode "Static Analysis"

比较两个 Harness run：

  python -m reverse_agent.harness compare --base-run <base> --head-run <head>

Harness 仍通过 reverse_agent Python namespace 调用；这是兼容接口，不是品牌回退。

五、安全边界

运行时验证和外部逆向工具可能执行或加载目标样本。未知二进制默认不应在宿主机直接执行；只应在明确授权、隔离且可恢复的环境中启用相关能力。

历史 Decisions、执行报告、旧分支、SHA、证据与旧路径必须保持原样，不因品牌迁移而重写。
