# Promptfoo — Agent × Model 公平评测、缓存污染与副作用源码专项

**完整研究 Issue：** [#1606](https://github.com/dddd2024/Nerelan/issues/1606) · **研究索引：** [#1576](https://github.com/dddd2024/Nerelan/issues/1576) · **日期：** 2026-11-16。

**固定源码：** [promptfoo/promptfoo@d6f16a99dfa50768de0aa7853bd057e4feb2d253](https://github.com/promptfoo/promptfoo/commit/d6f16a99dfa50768de0aa7853bd057e4feb2d253)（MIT）。**Nerelan 基线：** [main@0a9997046386bac5ca291410ce428c160f3ea763](https://github.com/dddd2024/Nerelan/commit/0a9997046386bac5ca291410ce428c160f3ea763)。

**研究状态：** `STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_TESTED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY`。本轮只读代码和上游测试；未运行 Promptfoo、模型、用户账户、工作区或 CI。已存在正式评测代码/实施 Issue，不产生第二评测引擎。

---

# Promptfoo 源码专项：Agent×Model 评测公平性、缓存污染、工作区副作用和真实成本

> **2026-11-16 · RESEARCH_ONLY / STATIC_SOURCE_REVIEW / NOT_INSTALLED / NOT_TESTED / DOCS_ONLY / NO_IMPLEMENTATION_AUTHORITY**
> **唯一上游**：[promptfoo/promptfoo@d6f16a99dfa50768de0aa7853bd057e4feb2d253](https://github.com/promptfoo/promptfoo/commit/d6f16a99dfa50768de0aa7853bd057e4feb2d253)，MIT；**Nerelan 对照基线**：[main@0a9997046386bac5ca291410ce428c160f3ea763](https://github.com/dddd2024/Nerelan/commit/0a9997046386bac5ca291410ce428c160f3ea763)。

## 0. 开始前查重：有评测实施规划，不存在 Promptfoo 独立源码专项

- 阅读 [canonical research hub #1576](https://github.com/dddd2024/Nerelan/issues/1576)：前六份、后续十份独立源码研究（#1578、#1581、#1585、#1587、#1590、#1592、#1594、#1598、#1600、#1603）和之前 19 项历史项目；搜索 Nerelan GitHub Issue 全文 `promptfoo` 与 `promptfoo/promptfoo` 均 0。已有评测核心方向 [#1527](https://github.com/dddd2024/Nerelan/issues/1527) 多 Executor×Model 配对、[#1267](https://github.com/dddd2024/Nerelan/issues/1267) single-vs-multi 质量成本基准，不重复开评测实施 Issue。
- 此次增量：不是重看 Agent Loop 或 CLI，也不是把 Promptfoo 当 Magpie 替代品；而是审查可否让 Nerelan 的质量-成本比较“重复可证伪、不受缓存污染、用独立证据、可归因工作区与全部费用”。

## 1. 与 Nerelan 当前主干逐模块对照

**Nerelan 已有实现：** [cost_quality_benchmark.py](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/cost_quality_benchmark.py) 已记录同一 BenchmarkContract identity、从 TaskStore 汇总 role/retry/usage、独立验收布尔值、拒绝不同合同对照和 UNKNOWN cash；[capability_benchmarks.py](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/capability_benchmarks.py) 有已有数据的 candidate/stage/adopt 和模型能力先验；[model_profiles.py](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/model_profiles.py) 按 binding / 状态聚合成功、token、time；[usage_ledger.py](https://github.com/dddd2024/Nerelan/blob/0a9997046386bac5ca291410ce428c160f3ea763/reverse_agent/platform_v1/usage_ledger.py) 明确保留未知用量为 None 不转换成零。不要复制一个外部评测数据库、模型账户池、第二个 Scheduler/Agent Loop。

### A. 原生多个 Agent Provider 适配：P1 借鉴类型化测试输入，不全量挪用

- [providers/opencode-sdk.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/providers/opencode-sdk.ts)、[providers/openai/codex-sdk.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/providers/openai/codex-sdk.ts) 与 [providers/claude-agent-sdk.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/providers/claude-agent-sdk.ts) 已分别提供真实 harness SDK 对接。存在工作目录、沙箱/工具权限、模型、session、缓存与 trace 的不同参数/行为；不能将一个模型 ID 的性能直接视为不同 harness 上相同。OpenCode provider 的默认工具配置含 `* = false` 和工作目录存在时只读工具白名单，但不能替代 Nerelan Host 权限/沙箱。
- **适合借鉴：** 将每条试验 arm 显式绑定 `executor/harness version + model/route + workspace snapshot + tool/permission policy + skill/pack manifest digest + task spec/acceptance`；对同一真实任务公平评测，每个 arm 固定环境与预算条件，但保留各 Harness 能力差异并单独归因。

### B. 评测工作区隔离与副作用：P1 优先复用测试，P0 不可称为 sandbox

- [providers/agentWorkspace.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/providers/agentWorkspace.ts) 为每个 eval step 克隆干净 Git 仓库或复制工作目录，检查符号链接/仓库环境选择变量并清理临时工作区，支持 diff 摘要；源码开头明确“**workspace isolation is not a security sandbox**”。它发现工作区被替换为 symlink 时会拒绝让 grader 回退到非预期目录。
- **Nerelan 已有** per-task linked worktree；借鉴负面测试：恶意 symlink、Git env 污染、现有 worktree 被替换、测试中断后 cleanup、diff/Artifact 所属 task 错绑。普通 `copy_working_dir` 不意味着主机文件/网络/秘密已安全隔离，依然由 #299 sandbox 和 #179 Host 管。
- [evaluator/runEval.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/evaluator/runEval.ts) 在 stateful target call 已完成但后续 trace/grading 失败的策略中保留 completedTargets 和已发生的 token/cost，标记 interruptedStrategy，防止普通 resume 静默重复发送；仍需要对非幂等外部副作用做真实 readback，不能把保存部分结果误叫 exactly-once。

### C. **P0 缓存污染反例：重复不是新样本**

- [cache.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/cache.ts) 默认启用 disk cache，默认 TTL **14 天**；[runEval.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/evaluator/runEval.ts) 通过 repeat-index 为每次重复分配 `repeat:0`, `repeat:1` 等命名空间；这避免同一轮不同 repeat 相互使用缓存，但[repeatCache.test.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/test/evaluator/repeatCache.test.ts) 明确测试了另一次新 evaluation 再次运行时 **仍命中之前相同 repeat 缓存**（cached=true，provider 未重新调用）。
- **对 Nerelan 的后果**：若用于发现成功率/故障率/模型稳定性以及真实支出，不得把缓存命中当新的独立试验，不得把命中的 0 本轮 spend 当本次模型的真实边际服务费用。正式 live bake-off 应强制 no-cache/unique run provenance 并验真实请求次数；非 live 回归可显式缓存且必须标注 `REPLAYED_FIXTURE`，不能纳入独立样本数。对 Magpie 的账单对齐和任务独立验收仍必需。

### D. 多层质量判分、Trace 与成本口径：P1 借鉴，拒绝无条件提升可信度

- [assertions/trajectory.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/assertions/trajectory.ts) 提供 tool-used、顺序、参数匹配（部分/严格/忽略字段）、步骤数、goal-success 等轨迹断言。缺失 trace/spans 时会抛错，而不是凭自然语言推断有工具调用。Goal-success 用 LLM grader，对执行器是否真正修改了仓库或外部网站没有独立事实保证。
- [assertions/toolCallF1.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/assertions/toolCallF1.ts) 的工具名 F1 使用 expected/actual **集合交集**，不反映调用次数、顺序、参数、实际执行成功与副作用收据；适用于辅助诊断，不适合作为主成功指标。脚本/静态断言+功能测试+独立审查应具备判分权重高于自报工具轨迹。
- [assertions/cost.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/assertions/cost.ts) 用 provider-returned cost 与阈值比较，缺失 cost 明确抛错；[openai/codex-sdk.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/providers/openai/codex-sdk.ts) 对自定义/旧 Codex 二进制不能可靠提供 cache-write token 的情况会返回 undefined 而非估算值；[runEval.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/evaluator/runEval.ts) 能累加 target 和 grader usage，并在 interruptedStrategy 下保留完成调用的费用。但 **provider 估价** 不等于 Nerelan 经 Magpie requests 结算的实际现金成本，订阅和配额单位需要另外计入；依 Nerelan 当前 UNKNOWN-on-missing contract 为准。
- [evaluator/derivedMetricFormula.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/evaluator/derivedMetricFormula.ts) 将评分公式限定为 AST 的数字/变量/四则运算/条件表达式，缺少分数变量时报错。这比直接 eval 可审计。但没有必要把组合打分公式当作独立质量验收标准，公式的版本/系数应事先冻结并报告单项指标。

### E. 不可信断言本身是执行代码：P0 权限门禁

- [assertions/javascript.ts](https://github.com/promptfoo/promptfoo/blob/d6f16a99dfa50768de0aa7853bd057e4feb2d253/src/assertions/javascript.ts) 在非 safe mode 下将用户给定 inline JavaScript 变为 `new Function('output','context','process', code)`，并传 process shim；safe mode 可拒绝内联脚本，但允许用户指定的 file reference 也需要独立的信任与隔离审查。
- **NO-GO**：未经 Owner/R3 审批，不能把从 GitHub 或陌生 Promptfoo YAML/插件包得到的 evaluator assertion、任意 Python/JS 脚本、exec provider 直接运行在 Nerelan trusted host；还应将 trace、prompt、Grader 输出做脱敏与限流。评测插件不是安全可信的可执行权限。

## 2. 精简复用矩阵

| 模块 | 判定 | 对 Nerelan 的具体增量 | 现有 Owner |
|---|---|---|---|
| Agent × Model 统一评测 | **P1 BORROW_PATTERN** | 多 Harness provider 规格 + 独立工作区与结果格式，既有 TaskStore/Executor 不替换 | #1527 |
| 用例、复现、重复 | **P0 TEST_FIRST** | 禁用 live cache 伪样本，标记 replay，逐 arm 的 commit/工具权限/模型及验收版本 | #1527 #1267 |
| 轨迹/工具行为断言 | **P1 BORROW_PATTERN** | 断言“没有越权工具”“必要工具/顺序/参数”“异常步骤上限”；主验收仍为功能与独立 reviewer | #653 #803 |
| 成本与额度 | **KEEP NERELAN + P1** | target/grader/retry/cache 归因测试；Magpie 请求明细与订阅配额为事实 | #1531 #1504 |
| 沙箱/恶意 Assert DSL | **P0 REJECT_DIRECT_EXECUTION** | 复制工作区不是安全沙箱；不可执行陌生 JS/Python assertions | #299 #447 |
| 模型评分/合成指标 | **P1 CONDITIONAL** | 纯受限 AST 公式和 scorer 输出，必须追溯原始证据与区间/不确定性 | #1527 #1267 |
| 第二个 Agent 编排器/Token Gateway | **REJECT_DUPLICATION** | 保留 Nerelan TaskStore、路由和 Magpie | #1546 #1342 |

## 3. 可证伪的 provider-free 实验（**尚未运行**）

**B1 缓存污染**：两次相同 benchmark × repeat=3 的假 Provider；第一轮实际调用 3 次、第二轮缓存 3 次。Nerelan live 采样必须拒收后者为新样本，不把重复缓存样本的虚假成功率/0 cost 写入 model_profiles。
**B2 三 Harness 同任务合同**：fake OpenCode/Codex/Claude wrappers 同输入但不同工具策略和缓存机制；严格固定 commit/模型 endpoint/权限/后处理/验收，结果归因到 (harness, model, binding, policy, task_kind, difficulty)，不得混淆。
**B3 Workspace/副作用**：symlink 逃逸、Git env 注入、dirty repo、workspace 删除/替换、取消后被删除的 workspace、脚本写出了工作目录；拒绝危险宿主动作，禁止 grader 偷看未批准文件；保留任务收据。
**B4 工具轨迹真假**：工具名 F1=1 但未真正运行、调用参数错误或副作用失败；工具轨迹评分可以高，但独立验收必须 FAIL/UNKNOWN，绝不能依据模型话术提升路由。
**B5 预算与欠账**：Provider 返回 undefined cost、Codex 缓存写入计数缺失、grader 二次收费、目标调用成功但评分中断、重试和服务端 Usage reconciliation 延迟；每项 UNKNOWN/ESTIMATE/ACTUAL 标记并拒绝虚构成本优势。
**B6 不可信评测断言**：陌生 YAML 的 JavaScript 试图读取 env/SSH key/网络，必须阻止，safe mode/隔离执行前置，不得通过 evaluator 合法身份自动提权。
**B7 公平统计**：预注册三档任务集合，重复独立成功率及失败 CI、通过独立 reviewers 的质量证据和总已验收成本；避免只选最高分样本、只算通过例成本或把失败/重试/规划和人工成本丢掉。

## 4. 总裁定与授权边界

**P1 SELECTIVE_BORROW_TEST_HARNESS / P0 NO_GO_CACHE_CONTAMINATION_AND_UNTRUSTED_ASSERTIONS / NO_SECOND_EVAL_RUNTIME**。最值得抄的是可证伪的**重复评测与缓存隔离测试、多个 Harness provider 合同、工具轨迹断言、工作区污染负例、分离 target 与 grader 成本**。对项目核心降低成本的评估必须依赖 Nerelan 主干已有 quality-accepted-task total cost + Magpie 实际成本；Promptfoo 的 pass/score/cost 不能直接晋升为路由事实。

仅 GitHub 静态源码阅读和研究文档，未 npm install、未运行 promptfoo eval、未执行任何 JS/agent、未调用模型/真实账户、未跑实验/CI 或独立评审；不创建竞争 implementation Issue，不批准 R2/R3 后端依赖或调用。

---

## 工件验收和边界声明

本 PR 只有一份研究文档，不修改 TS/Python Runtime、评测基准、模型路由、Token 账本、第三方依赖、工作流或授权策略。后续任何引入 Promptfoo SDK/CLI、运行不可信断言、读取用户的仓库或执行 Agent，必须独立通过 Nerelan `AGENTS.md` 对应 R2/R3 安全与权限门槛；此研究记录无权授权。

现有实施 Owner 继续为 [#1527](https://github.com/dddd2024/Nerelan/issues/1527)、[#1267](https://github.com/dddd2024/Nerelan/issues/1267)、[#299](https://github.com/dddd2024/Nerelan/issues/299)、[#1531](https://github.com/dddd2024/Nerelan/issues/1531)。研究台账采用 #1576 的追加评论，而非与旧研究索引堆叠 PR 修改冲突的索引文件。

**合并前置条件（未完成）：** exact-head CI / baseline state gate、独立审查、许可证和 R1 政策确认。新测试只是建议，没有宣称功能或成本收益已经获得实证。