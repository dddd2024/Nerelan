<!-- Single-upstream static research. Canonical Issue #1706. Not an implementation authorization. -->

# Harbor (Terminal-Bench harness) pinned deep audit — Job Lock, Regrade, scoring denominator, phase concurrency, trust boundaries

> **2026-11-19 | SINGLE_PROJECT | PINNED_STATIC_SOURCE_REVIEW | DOCS_ONLY | NOT_INSTALLED | TESTS_NOT_RUN | NOT_BENCHMARKED | NOT_IMPLEMENTED | NOT_MERGED**
>
> Upstream: [harbor-framework/harbor@a215bfa03ccc026d22a0f11d5d6c51a8a46f0510](https://github.com/harbor-framework/harbor/commit/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510), [Apache-2.0](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/LICENSE), [pyproject v0.26.0](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/pyproject.toml); Nerelan compared with [main@b48cc9b82893be222e2ccdb307dd4a81bebee935](https://github.com/dddd2024/Nerelan/commit/b48cc9b82893be222e2ccdb307dd4a81bebee935). **This research audits only the Harbor repository**, not Terminal-Bench datasets, hosted Harbor services, or performance claims.

## 0. 事前去重 / 具体增量

- 检查 [research hub #1576](https://github.com/dddd2024/Nerelan/issues/1576) 正文、**45 条评论**、GitHub Issues（`Harbor`、`harbor-framework`、`Terminal-Bench` 及 `Research / Reuse` title）、Nerelan 代码搜索 `Harbor`：没有独立 **Harbor** 固定 SHA 源码专项；已有 `Terminal-Bench` 只是 [#1527](https://github.com/dddd2024/Nerelan/issues/1527) 中“比较多种 Agent×Model”的设计参照，[#1264](https://github.com/dddd2024/Nerelan/issues/1264) 是外部排行榜先验，**不是可运行评测协议的代码审查**。上游正式仓库已迁为 `harbor-framework/harbor`，不要基于旧 `laude-institute/harbor` 的名字创建虚假并列项目。
- 上一轮 [Inspect AI #1697](https://github.com/dddd2024/Nerelan/issues/1697) 审过 scoring coverage/agent-complete scoring-only resume；本轮**不重复**。独立增量：**(1) 比较变更前识别 reused / regrade / rerun，(2) 版本化 trial job locks 包含技能、任务、环境、验证输入，(3) artifact manifest 完整性与 regrade 的环境隔离前置条件，(4) 全局 Trial×Agent 阶段池和重试成本丢失风险，(5) Job 插件最小生命周期但无 Host 权限保证。**
- 现有实施 Owner：#1527 Agent×Model Bake-off、#1267 成本/成功率、#653 exact artifact functional truth、#1504 budget、#1342 Magpie usage、#1546 durability、#299 sandbox、#303 workspace trust、#253/#790 plugins、#1507 exploration。**不新建重复实施 Issue**。

## 1. 模块级源码证据与复用裁决

### A. Evaluation Lock / identity（**P0 BORROW_PATTERN**, 不建立第二份合同）

- [`models/job/lock.py` L67–89](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/job/lock.py#L67-L89) `TaskLock` 以 `sha256:` 格式验证任务内容 digest；[L176–251](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/job/lock.py#L176-L251) `TrialLock` 包含 Task、Agent、Verifier、Environment、User Prompt、额外指令、技能目录内容 hash、Docker Compose 覆盖等；[L272–296](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/job/lock.py#L272-L296) `JobLock` 固定并行数和重试策略。并非仅记录“模型名字”。
- [`job_plan.py` L67–101, L144–176](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/job_plan.py#L67-L101) 对每条 resolved Trial 建立 1:1 lock；[`lock.py` L356–389](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/job/lock.py#L356-L389) JobLock 从已确定的 TaskDownload 和 TrialConfig 构建。
- Nerelan [`cost_quality_benchmark.py` L32–48](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/cost_quality_benchmark.py#L32-L48) 已有 `BenchmarkContract` 及 `requirements_digest / acceptance_digest / tools_digest / budget` 等，[`functional_validation.py` L191–237](https://github.com/dddd2024/Nerelan/blob/b48cc9b82893be222e2ccdb307dd4a81bebee935/reverse_agent/platform_v1/functional_validation.py#L191-L237) 已冻结 exact base+goal+checks。**增量**：把实际 executor/version、model binding、tool schema & policy、Skill/MCP、sandbox image+os+network、Verifier version/allowed inputs、cache treatment、retry policy、trial replicate seed/id 纳入同一个*衍生评测快照*，与现有 TaskStore contract 建立 digest 引用，不建 Harbor JobDB。
- 无所谓“锁文件完全证明复现”：外部 provider 的动态行为、账户、定价/限额、配置环境变化仍要记录实际 observed identity。锁一致只证明**声明的已锁定输入**一致。

### B. Diff / Reuse / Regrade / Rerun（**P0 HIGH VALUE BORROW_PATTERN**）

- [`job_diff.py` L29–89, L178–335](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/job_diff.py#L178-L335) 对旧/new trial lock 判定 `REUSE`、`REGRADE`、`RERUN`。若同名同版本 Task digest 不同直接报错；未版本化样本强制重跑；对 **non-task inputs** 不兼容也重跑；对源 Trial 未成功/不完整也重跑；一个源 Trial 只能消费一次，不能用于制造多个新的独立 replicate。可重评分须 check task compatibility。
- [`trial/regrade.py` L1–14, L98–123](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/trial/regrade.py#L1-L123)：`RegradeTrial` 从记录恢复 agent 与 artifacts，**不重新运行 Agent**，需要新 Verifier 使用 `SEPARATE` environment（Agent live env 已不存在）；[L276–308](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/trial/regrade.py#L276-L308) manifest 缺失/不可读 fail-closed；[L418–580](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/trial/regrade.py#L418-L580) 对声明输入检查 manifest: missing/failed/skipped、目标路径不匹配、文件缺失、类型不匹配、排除规则不匹配等都拒绝。旧 manifest exclusion 信息缺失时**会 warn 并继续**：对 Nerelan 提升为 fail-closed。
- **Important boundary** [`models/trial/artifact_manifest.py` L1–20](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/trial/artifact_manifest.py#L1-L20)：该 manifest 只存 source/destination/type/status/service/exclude，**没有内置 per-file content SHA**。因此证明“路径还存在、类型正确”≠证明字节与旧验收完全一致。Nerelan 已有 immutable Git tree / artifact digest：**重评分必须绑定 artifact bytes/digest + original approved contract + new verifier digest + source run ID/epoch，拒绝换字节但路径相同**。
- 对比 Inspect AI 上轮 `resume_for_scoring` 是**单次执行失败恢复**；Harbor 的 `regrade` 更像**旧产物评测协议升级后的再审**，即更清晰的研究增量。Nerelan 应实现一个 provider-free `compare_trial_evidence()` **纯函数**在 #1527 下试验，但必须避免重写 TaskStore 状态机或把“旧 run 重评分”当“新的模型独立成功”。

### C. Verifier isolation / stale reward fail-closed（**P0 BORROW_PATTERN**）

- [`trial/single_step.py` L38–114](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/trial/single_step.py#L38-L114)： Agent 运行→日志/产物收集→`SEPARATE` 时先停 Agent 环境→在独立环境评分；`SHARED` 则共用同一环境。[`tests/unit/test_trial_verifier_separate.py` L239–455](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/tests/unit/test_trial_verifier_separate.py#L239-L455) 有 upstream test 验证不同 sidecar 构造和 stop order（**仅阅读未运行**）。
- [`verifier/verifier.py` L167–207](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/verifier/verifier.py#L167-L207)：每次评分前删掉旧 reward txt/json；[L91–124](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/verifier/verifier.py#L91-L124) 拒绝 NaN/inf/非数值；[L198–310](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/verifier/verifier.py#L198-L310) 执行测试、复制输出后 reward file 缺失时报错，而非默认 0 或沿用旧 reward。
- **Cannot infer fully independent acceptance**：SEPARATE environment 只保证执行路径/环境不同；还必须证明 Verifier 检查本身不被候选 Agent 改写、没有越权的脚本输入/依赖、不能读取同工作区的隐藏答案，且测试由 Nerelan Host 批准。直接套用 Harbor reward 不是独立 review/功能真值 [#653](https://github.com/dddd2024/Nerelan/issues/653)。

### D. Coverage / cost denominators / historical retry spending（**P0 TEST_FIRST**）

- [`models/trial/result.py` L129–152](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/trial/result.py#L129-L152) `reward_valid` 依赖 rewards 存在与错误策略，[`models/job/result.py` L129–175](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/job/result.py#L129-L175) 一条 trial 到最终结果就记入 `n_completed_trials`，但 `eval_stats.n_trials` 只计 `reward_valid` 的 trial。即**“完成/有结果”、“有效 reward”、“真实成功”三个分母不同**。主排行榜不能忽略错误/未评分样本。
- [`models/trial/result.py` L152–191](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/trial/result.py#L152-L191)：`compute_token_cost_totals` 对有效存在的 AgentContext 汇总。若部分 step 缺失 usage，它把可见项相加，不等于**所有参与请求已结算**；[ `models/metric/usage_info.py` L6–34](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/metric/usage_info.py#L6-L34) 是单调用已知 usage 结构、非 Magpie 的实际订阅账。
- [`trial/queue.py` L172–242](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/trial/queue.py#L172-L242)：重试创建**新的 Trial**、在两次间删除旧 trial_dir，失败时可能整个多步 Trial 重新执行；仅返回最终 `TrialResult`。**静态推论**：如果只使用最终结果汇总费用，而没有另一个底层请求账本，前几次失败尝试的成本可能漏算；这不是实测的 Harbor 账单缺陷，须通过 fake callback/usage fixture 证明。Nerelan 已经要求 `all roles, all retries, UNKNOWN not zero`：不能因为重试目录被删就删除任务级用量/网关 Request 收据。
- [`trial/error_policy.py` L15–126](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/trial/error_policy.py#L15-L126)：`should_retry/should_grade/has_valid_reward` 三轴把 Agent timeout、rate limit、auth、verifier invalid 区分；默认 `UNKNOWN_ERROR_POLICY=retry,grade,valid`，unknown exception 还可能在有 reward 时被视为有效。**Nerelan 不能照搬未知错误默认可继续**；要根据 `remote side effect?` + `oracle authority?` 逐项 fail-closed，之后再允许 Host 重派。

### E. Agent concurrency / quota fairness（**P1 BORROW_PATTERN**, no second scheduler）

- [`trial/queue.py` L29–48, L90–170](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/trial/queue.py#L29-L170)：全局 trial semaphore，另有 per-agent `n_concurrent`，共享 `concurrency_group`，**AGENT_START 获得 / AGENT_END 释放**，取消和 END 做兜底释放；配置冲突限制 fail fast。只在 Agent 运行阶段占 Agent permit，让 verifier/准备阶段可与其他 Agent 交错。[`models/trial/config.py` L66–210](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/trial/config.py#L66-L210) per-agent pool key 若未显式分组会按 agent 配置的敏感值 hash 而非透出；仍不意味着 API account/额度实际可用。
- 对 Nerelan 的可借鉴机制是 **按 (executor, Magpie provider account or group, phase) 的 slot accounting**，与既有 window allocator/pace/quota/Coordinator 对照、避免因为 Verifier 占位导致可用 Agent idle。但**必须保留现有 lease fencing/slot reconciliation**，别让 async semaphore 替换跨重启/跨 host 配额。已有关 [#1527](https://github.com/dddd2024/Nerelan/issues/1527)、[#1342](https://github.com/dddd2024/Nerelan/issues/1342)、[#1267](https://github.com/dddd2024/Nerelan/issues/1267)。

### F. Plugin and sandbox scope（**REJECT DIRECT**）

- [`models/job/plugin.py` L1–27](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/models/job/plugin.py#L1-L27) 的 JobPlugin 仅 `on_job_start/on_job_end` 两个生命周期钩子；[ `cli/job_plugins.py` L20–102](https://github.com/harbor-framework/harbor/blob/a215bfa03ccc026d22a0f11d5d6c51a8a46f0510/src/harbor/cli/job_plugins.py#L20-L102) 可用字符串 import path 动态实例化 Python 类并调用钩子，**并没有证明这是不可信第三方隔离**。Nerelan #253/#790 的 Pack/MCP 工具权限不能直接复制这一导入机制：若配置来自不可信项目，这就是宿主执行代码。
- Harbor 环境支持许多 sandbox backends，但这不等于 Nerelan Windows Host 下的安全隔离；网络/凭据/硬件/挂载仍由实际 provider 和政策证明。**不建议部署 Harbor 后台服务、API、统计库或 Docker**来完成本研究。

## 2. 四分类 / 分层决策

| Nerelan existing scope | Verdict | 最小借鉴内容 | NOT to copy | Existing Owner |
|---|---|---|---|---|
| Eval Contract + Agent×Model pair | **ALREADY_REUSED + P0 BORROW** | `TrialEvidenceLock` 消化 task/artifact/agent/executor/model/verifier/skill/env/seed/replicate digests，保留历史真实路由身份 | 第二个 JobDB / benchmark contract | #1527/#1267 |
| Eval incremental rerun | **P0 BORROW_PATTERN** | `REUSE/REGRADE/RERUN` 的纯差异判定；新 verifier 只查冻结旧产物、不重跑 Agent | 仅凭路径存在重用、成功样本双计 | #1527/#653 |
| Functional oracle | **P0 BORROW_PATTERN** | 独立 verifier environment，旧 reward 删除、缺失/非法值 fail closed，artifacts exact digest | 将 reward 当独立人审与发布通过 | #653/#299 |
| Usage / Cost | **KEEP + P0** | 覆盖率分母和 retry lineage，所有失败尝试保留收据 | 只看最终 Trial 账本 / UNKNOWN=0 | #1342/#1504/#1267 |
| Pool / Concurrency | **P1 BORROW_PATTERN** | Agent phase slot 和 experiment-wide slot 分离 | asyncio semaphore 代替 durable lease | #1527/#1546 |
| Plugins / Sandbox | **REJECT DIRECT** | 钩子签名可参考 | 任意 import path、默认 shell、额外后台服务 | #253/#790/#299 |

## 3. 可证伪的 provider-free fixtures（本轮未执行）

1. **Lock truth**：同一任务同一目标，Agent CLI/版本、Model ID、Tool/Skill 内容、MCP/Verifier、环境镜像、网络政策中任一实际变更，`TrialEvidenceLock` identity 发生变化；只改变 UI 名字/时间戳、绝不应伪造一个新的重复收费 Trial。
2. **Diff matrix**：精确合同相同且 old accepted → `REUSE`（不能计入新的独立成功次数）；新 verifier 兼容+旧 artifact bytes 存在 → `REGRADE`；Task 内容同版本但 digest 冲突/Verifier required artifacts missing → `RERUN / FAIL_CLOSED`；old errored 或不同 Agent/环境 → `RERUN`。
3. **Artifact substitution**：旧 manifest 全为 `ok`、文件路径/类型无变化，但字节被替换。Harbor manifest shape 本身无内容 digest，Nerelan 必须靠既有 SHA/Git tree 拒绝重评。
4. **Verifier leak**：Agent 可控制的 reward.json 包含 `1`，但 separate verifier 跑前清除；新 verifier 不生成结果 ⇒ `INVALID_SCORE` 而不是 PASS 或 0。新增 NaN/inf、缺文件/非法 JSON 的验证用例。
5. **Scoring denominator**：10 个预期 trial，6 个有有效 reward，其中 3 个独立接受，2 个失败、2 个未评分：`valid_scoring_coverage=6/10`、`scored_accuracy=3/6`、`accepted_of_admitted=3/10`，全部分母都标明。
6. **Retry accounting**：第 1 次 Trial 花 10 单位后异常，第 2 次花 20 单位成功，最终的 provider-ledger 总量必须是 30；删除尝试文件或 retry job 不得抹去已使用额度；副作用 unknown 情况不得自动整段重试。
7. **Phase scheduling**：全局 trial=3，某 Provider/Agent phase=1，两条候选 Agent 在等待中，Verifier 和环境 setup 仍可推进；END/CANCEL 释放 permits；Host restart 必须由 durable lease 再核对。
8. **No privilege**：项目自带的 custom verifier、agent class/job plugin import path、可疑 Docker mounts、agent-visible verifier secret 一律不因“Harbor 支持”而获得 Host 执行或凭据权限。
9. **Economic acceptance**：从相同 frozen base 的 trivial/medium/large 真任务开始，不同 Agent×Model×Environment；计入 planner、provider retries、grader、review、cache、stale artifacts、沙箱构建和返工，按照 **independently accepted changes per actual total cost** 比较，而不是 benchmark leaderboard 单一 reward。尚未获真测证据，不提出新默认路由策略。

## 4. Evidence status

**实际执行过**：核实 GitHub 研究索引与 45 条 hub 评论/关键词 Issues/代码查重、固定 Harbor 上游提交/Apache license 和版本、逐文件读取 lock/diff/regrade/verifier/retry/queue/error-policy/usage/plugin/测试源码，并与 Nerelan 当前 `cost_quality_benchmark.py`、`capability_benchmarks.py`、`functional_validation.py`、`run_store.py`、`task_runtime.py` 对照；设计上述无模型实测的失效反例。

**未执行/不能声称**：未安装/运行 Harbor、pytest、Docker 或真实模型；未进行任何 Agent×Model 经济性测试；未核验 Windows 行为；未修改 Nerelan 运行时；未跑 CI 或独立审查；未发布/合入。Research Issue + docs-only Draft PR != 实现、通过、允许使用第三方程序。


---

## Research filing
- Canonical Issue: https://github.com/dddd2024/Nerelan/issues/1706
- Research Hub: https://github.com/dddd2024/Nerelan/issues/1576
- Docs Draft PR reference is recorded in Issue #1706 after PR creation.
- Evidence status: PINNED_SOURCE_REVIEW / PROVIDER_FREE_TESTS_NOT_EXECUTED / NO_EXTERNAL_MODEL_SPEND / NO_RUNTIME_CHANGES / NOT_MERGED.
