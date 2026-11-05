# Magpie 能力实证审计（2026-11-04，本机只读）

```text
STATUS: AUDIT COMPLETE (read-only, local machine)
AUTHORITY: 只读观测；未执行任何写入命令、未做任何付费模型调用、未读取或导出凭据
SCOPE: M1–M5（见 MULTI_ACCOUNT_ORCHESTRATION_SPEC.md §12.2）
```

## 0. 结论摘要

| 审计项 | 结论 | 对本计划的影响 |
|---|---|---|
| M1 版本与端点 | **已核实** | Magpie 应用 **0.12.6**，协议 `magpie 0.1.2782`，环回 `127.0.0.1:3425` |
| M2 账户内自动切换 | **已支持**（CLI 能力存在） | Nerelan 的账户选择应降级为**未启用 Magpie 时的 fallback** |
| M3 `quota wait` | **已支持** | 本轮的"空闲等待 60s 上限"是**降级实现**，有 Magpie 时应优先用官方阻塞等待 |
| M4 命名空间覆盖 | **11 个账户 / 11 个 provider**，含 workbuddy、workbuddy-ai、trae-cn、copilot | 现有 `_MAGPIE_PROVIDER_KEYS` 只映射 claude/codex；其余仍只能作遥测（因本仓无可路由执行器） |
| M5 请求级账户归因 + 真实成本 | **已支持**（`usage --csv` 含 `cost_usd`/`provider_account`/`tries`/`status`） | **列表价估算应降级为 fallback**；现金成本直接取 Magpie 实测 |

一句话：**评审第 1 点比我的初判更接近事实**——Magpie 已经提供了账户切换、`quota wait`、按用量/节奏路由、
以及请求级真实成本。Nerelan 继续自建这些能力即构成重复建设。

---

## 1. 方法与边界

只做了三类**只读**动作：

1. 三个既有端点的 GET（本仓已在用的）：`/api/hello`、`/v1/models`、`/v1/magpie/quotas?kept=1`。
2. 本机 CLI 的 `--help` / `quota --json` / `usage --csv`（**只读查询**）。
3. 端口连通性探测。

**未做**：`accounts switch`、`group add/set`、`provider fallback`、`quota wait`（会阻塞）、任何模型调用、
任何凭据读取或导出。本文中所有账号标识均已聚合成计数，不出现邮箱、密钥或账户名。

---

## 2. M1 版本与端点

```text
GET /api/hello              -> {"name":"magpie","version":"0.1.2782"}
GET /api/version            -> {"version":"0.12.6"}
GET /v1/models              -> {"data":[{id:"auto/gemini-4-argon", magpie_label:"… routing group", …}]}
GET /v1/magpie/quotas?kept=1-> {"data":[{provider, name, kind, plan, windows:[{name,used,remaining,resetsAt,holdsWhy}], …}]}
GET /v1/magpie/usage        -> {"period":"30d","calls":5502,"errors":194,"retried":43,…}
```

- 不存在 `/openapi.json`（不是 FastAPI 风格的自描述服务）。
- 可执行文件：`F:\magpie\magpie.exe`（另有 `magpie-bun.exe` 运行时）。

## 3. M2/M3：账户切换与额度等待

CLI 明确列出（`magpie.exe --help` 原文节选）：

```text
magpie accounts switch <agent> next      to the next account in order with room, or the one with the most left
magpie accounts switch-only claude [on|off]   only switch Claude's own sign-in…
magpie group add <name> models=<m1>,<m2> [routing=smart|order|rotate|usage|pace|weight|free|fast|cheap|drain]
magpie provider fallback <id> <provider/model>…   use these when it's out of quota or down
magpie quota wait <provider|account> [--timeout <d>] [--quiet]   block until … has allowance again
```

判定：

- **M2 ✅**：存在"按剩余额度/用量/节奏/速度/价格"的路由组策略与"切到有余额账户"的命令。
- **M3 ✅**：存在阻塞式 `quota wait`，带超时。
- **M6（新增）**：还存在 `provider fallback`——**provider 级故障降级**，与本仓的模型级
  `fallback_ladder` 重叠。

> 诚实标注：以上是**CLI 能力存在性**，不是"端到端已实测通过"。我未执行 `switch`/`wait`
> （前者会改动用户的 agent 登录态，后者会阻塞），因此标记为**能力已确认、行为未实测**。
> 行为验证应按 P0 的 M2/M3 场景在独立窗口内进行，且需要 Owner 在场观察登录态变化。

## 4. M4：账户与命名空间覆盖

`magpie quota --json` 聚合结果（仅计数）：

```text
accounts: 11
providers: claude, codex, copilot, minimax-code, opencode-zen-free,
           openrouter, raccoon, trae-cn, workbuddy, workbuddy-ai, zcode
kinds:     subscription(9), balance(2)
windows:   5 hours, 7 days, Chat requests, Completions, Credits, Extra credits, Premium requests
fields:    balance, error, kind, last, lastServedAt, name, plan, provider, readAt, resets, until, user, windows
```

判定：

- **M4 部分 ✅**：Magpie 确实覆盖 `workbuddy` / `workbuddy-ai` / `trae-cn` / `copilot` / `zcode` 等，
  而本仓 `_MAGPIE_PROVIDER_KEYS` 只映射 `claude` / `codex`。
- **但这不等于"应当纳入准入"**：本仓可路由的执行器只有 codex / claude_code（`NATIVE_CLI_PROVIDERS`）。
  其余 9 个账户**没有可派发的路由**，纳入准入只会制造"有额度但没人能用"的假象。
  → 维持"未映射 provider 只作遥测"，但**在 UI 与文档中明确说明原因**（已有 `account_attribution`
  的 `no_route_identity` 五态，措辞正确）。
- 另有 `kind=balance`（openrouter / minimax-code）——**余额型**资源，属于"现金/信用额度"，
  不能与订阅窗口用同一套 percentage 语义处理。这点直接支持本轮的三口径成本模型。

## 5. M5：请求级归因与真实成本

`magpie usage --csv --last 2h` 的列（实测 242 行）：

```text
time, agent, requested_model, provider, host, model, served_model, swapped,
input_tokens, output_tokens, cache_write_tokens, cache_read_tokens, reasoning_tokens,
cost_usd, duration_ms, ttft_ms, status, error, session, kind,
provider_key_id, provider_key_name, provider_account, route_id, request_id, endpoint,
error_message, error_type, source, rejected, session_provider, session_account,
session_official_login, caller_key_id, caller_key_name, response_id, upstream,
cache_write_5m_tokens, cache_write_1h_tokens, tries, handed_on,
tier_asked, tier_sent, tier_served, upstream_stop, credits
```

实测聚合（2 小时窗口）：请求 **242**，`cost_usd` 合计 **$1.1302**，`status` 全为 0，
`rejected=0`，`tries>1` 为 0，`swapped` 为 0。

判定：**M5 ✅，且强于本仓现状**：

| 本仓现状 | Magpie 已有 |
|---|---|
| `equivalent_cost()` 用 models.dev **列表价估算** | `cost_usd` **真实计费** |
| 金额只能到任务粒度 | 到**单次请求**，含 `served_model` 与 `tier_*` |
| 重试次数靠自己的事件流推断 | `tries` / `handed_on` 直接给出 |
| 账户归因靠 `account_ref` 推导 | `provider_account` / `session_account` 直接给出 |
| 是否被上游换模型不可知 | `swapped` / `requested_model` vs `served_model` |

## 6. 重叠矩阵与处置

| Nerelan 组件 | Magpie 对应能力 | 处置 |
|---|---|---|
| `multi_account/scheduler.py`（选账户、冷却、退避） | `accounts switch next`、`group routing=usage/pace/cheap` | **降级为 fallback**：Magpie 在位且启用时不参与决策；仅在 Magpie 关闭/不可用/未覆盖该 provider 时生效 |
| `retry_at` + `idle_wait`（本轮新增） | `quota wait --timeout` | **降级为 fallback**：有 `quota wait` 时优先官方阻塞等待 |
| `fallback_ladder.py`（模型/执行器降级） | `provider fallback` | **保留**：Nerelan 管"换模型后语义是否等价、任务要不要重验"，Magpie 管"这条请求换谁接" |
| `equivalent_cost` 列表价 | `usage --csv.cost_usd` | **降级为 fallback**：有 Magpie 实测时，现金成本口径取实测；列表价仅用于无实测的规划期估算 |
| `account_attribution`（UI 五态） | `quota --json` 的 window/kind | **保留**：多一层"本仓能否路由"的判定，Magpie 不提供 |
| `orchestration_selector`（单/多 Agent 经济性） | 无 | **保留**：这是任务级决策，Magpie 不涉及 |

## 7. 落地顺序（P1，均在无写入、可回滚前提下）

### 7.0 第一步已实现（2026-11-04）：只读接入 `usage --csv`

模块：`reverse_agent/platform_v1/magpie_usage_ingest.py`（纯只读，不参与派发）

| 能力 | 实现 |
|---|---|
| 取数 | `read_usage(exe, last="6h")`：一次有界子进程（固定 argv、`shell=False`、超时 25s），非零退出/超时返回 `[]` |
| 解析 | `parse_usage_csv()`：28 列中只保留时间/模型/令牌/成本/状态/重试/会话，其余（密钥名、错误体）**直接丢弃** |
| 脱敏 | 账户身份 → `acct_` + SHA-256 前 12 位；**原始邮箱/密钥名永不落盘** |
| 口径 | `cost_basis_values()`：`subscription` → `cash=0, quota=报告成本`；`payg` → `cash=报告成本, quota=0`；未知 → 双侧 `None` |
| 聚合 | `cost_facts()`：按账户/厂商汇总，并单独给出 `failed_cost_share`（买了但没成功的比例） |
| 缓存 | `merge_into_cache()`：JSONL 按 `request_id` 去重、保留最新 5000 条、原子写 |

**实测（`--last 2h`，本机）**：272 条请求入库；会话账户 10 条 → `quota_value_usd=1.676`、`cash=0`；
其余 262 条为免费/无价模型 → 记为 **`unknown_cost`（未知，不是 0）**。这与"订阅花额度、API 花钱"
的区分一致，也说明 **`cost_usd` 不是统一现金**，必须按会话归属分类。

前置配置（均需显式设置，无机器路径默认值）：

```text
REVERSE_AGENT_MAGPIE_EXE=F:\magpie\magpie.exe      # 必填；非绝对路径/不存在 → 视为未配置
REVERSE_AGENT_RUNTIME_DIR=<dir>                    # 可选；缓存默认 <cwd>/.platform_v1_runtime
```

验证：`tests/platform_v1/test_magpie_usage_ingest.py` 9 例（默认跳过实时用例）；
设 `REVERSE_AGENT_MAGPIE_EXE` 后 10 例全通过（含一次真实读取）。

**未做**：未把结果接入派发/评分决策；未做"请求 → 任务"关联（Magpie 的 `session` 与 Nerelan
的 task/execution 尚无 join key），因此 `all_in_economics(basis="cash"|"quota")` 目前仍缺
`accepted` 维度，属 P1 第 2 步。

### 7.1 第二步已实现（2026-11-04）：请求 → 任务的保守归因

Magpie 的 `session` 是 UUID，与 Nerelan 的 `task_id` 没有共享 join key。因此不臆造 ID，
改用**可证伪的保守归因**（`magpie_usage_ingest.correlate_usage`）：

| 规则 | 说明 |
|---|---|
| 匹配键 | 行 `agent`（codex / claude / claude-desktop）× 尝试 `executor_kind`；**不是** `provider`（厂商） |
| 时间窗 | 尝试的 `created_at → updated_at` ± 120 s（`ATTRIBUTION_SLACK_SECONDS`） |
| 唯一性 | **只有恰好一个尝试匹配才计入**；两个尝试都匹配 → `ambiguous`，**绝不均分** |
| 缺口可见 | `unattributed` 带原因（`no_time_or_agent` / `no_matching_attempt`） |
| 周期诊断 | `summary.overlap` = `full`/`partial`/`none` + `overlap_attempts`，区分"没数据"与"匹配失败" |

成本侧：`economics_runs(correlated, strict=True)` 对**未被完整归因**的尝试返回 `None`
（未知），而非 `0.0`。理由很直接：一次尝试只要有没有被匹配到的请求，它就可能花了这里看不到的钱；
记成 0 会得出"每次变更为 $0"的荒谬结论。

**真实数据实测（本机）**：

```text
requests=617  attributed=0  ambiguous=0  overlap=none  overlapping_attempts=0
cash : runs=55 accepted=28 per_accepted=None unpriced=55
quota: runs=55 accepted=28 per_accepted=None unpriced=55
```

原因不是逻辑失败：任务库最新一次执行在 **2026-10-18**，而用量窗口是**今天**，两者完全不重叠。
系统如实报 `overlap=none` 且把成本判为 `UNKNOWN`，而不是伪造一个 $0 结论。
（期间还修掉两个实测才暴露的缺陷：把 `provider` 当成 `agent` 用；未匹配尝试被计为 0。）

### 7.1.1 精确 join key（2026-11-04 已实现，替代时间窗猜测）

**关键发现**：执行器其实**早就拿到了** agent 的会话 id，只是没落库。

| 环节 | 事实 |
|---|---|
| 采集 | `claude_protocol.py:137` / `codex_protocol.py:248` 已从 `system.init` / `thread.started` 解析出 `session_id` / `thread_id` |
| 传递 | `ClaudeCodeExecutor(CodexExecutor)`，两条路径共用同一个完成事件 |
| 落库 | 本轮新增一行：`EXECUTOR_COMPLETED.metadata.agent_session_id`（`codex_executor.py`） |
| 回读 | `magpie_usage_ingest._agent_sessions()` 取每个任务**最新**一次完成事件的该字段 |
| 匹配 | `correlate_usage` 先按 `session` 精确匹配，**精确命中既不看时间窗、也不可能 ambiguous**；未命中再退回时间窗 |

因此"精确归因"是**一行落库 + 一段回读**，没有改命令行参数、没有改派发决策、没有新增依赖。

**join key 已实证（只读核对）**：取 Magpie 6 小时窗口内的 `session` 值，与
`~/.claude/projects/**` 下的会话文件名比对 —— **1/1 命中**。也就是说 Magpie 的 `session`
就是执行器从 `system.init` 解析出的那个 `session_id`，不是同名异物。
核对过程只做"文件名是否存在"的匹配，**未读取任何会话内容、未打印任何路径**。

诚实标注：历史任务没有这个字段（本轮之前的运行），所以

```text
exact_attempts = 0   # 现有 77 个尝试全部是旧数据
```

要看到 `exact_attempts > 0` 与 `ambiguous` 下降，需要**新一轮执行**产生带 id 的事件。

整条链已在测试中跑通（真实子进程执行器 + 真实 TaskStore + 真实完成事件 + 只读成本模块）：
`test_codex_executor.py::test_agent_session_id_drives_exact_cost_attribution` ——
执行器写入 `agent_session_id`，请求即使**相隔两天**也能被精确归因，`cost_per_accepted_all_in=0.25`。

覆盖测试：`test_codex_executor.py::test_native_subprocess_worktree_progress_and_final_response`
断言 `agent_session_id == "fixture-thread"`；`test_magpie_usage_ingest.py` 另有 5 例覆盖
"精确胜过竞争窗口""精确无视时钟""未知 id 回退时间窗""取最新事件""无 id 仍可按时间归因"。

### 7.2 并列统计报表（2026-11-04 已实现）

`reverse_agent/platform_v1/cost_report.py` —— 决策 1 要求的"新旧口径并列统计"的产物：

```bash
python -m reverse_agent.platform_v1.cost_report --last 6h        # 或 --from-cache
```

输出四组数（同一份数据、互不混合）：

| 列 | 含义 |
|---|---|
| `legacy` | `cost_per_accepted`：只算合格运行的列表价成本（当前决策在用） |
| `list_price` | 全尝试成本 / 合格数，按**列表价估算** |
| `cash` | 全尝试成本 / 合格数，按 Magpie **实际计费**（仅按量流量） |
| `quota` | 全尝试成本 / 合格数，按 Magpie 报告的**额度机会价值**（订阅流量） |

本机实测（数据不重叠，故全部 `n/a`，这是**正确**的而不是缺陷）：

```text
attempts=77 requests=613 attributed=0 ambiguous=0 overlap=none
basis       mode          runs accepted  per_accepted
cash        single          55       28           n/a
list_price  single          55       28           n/a
quota       single          55       28           n/a
legacy      single          55       28           n/a
```

`list_price` 也为 `n/a` 是因为那 55 个历史任务没有令牌观测（`task_usage_observations` 为空），
无法定价 —— 报表选择报 `n/a` 而不是 0。

**实验前自检**：`python -m reverse_agent.platform_v1.cost_report --doctor` 会逐项回答"能不能跑对照"。
本机实测（Magpie 已配置）：`magpie_cli_configured ✅ / magpie_reachable ✅ / usage_rows 445 ✅ /
tasks_with_session_id ❌ 0/77 / windows_overlap ❌ none` → `NOT READY`，
下一步提示"先跑一次带 session id 的执行"。这正是当前真实状态，不是失败。

覆盖测试：`tests/platform_v1/test_cost_report.py` 10 例（新旧并列、拒绝编造、caveats、
快照不覆盖基线、跨版本拒绝、doctor 的 ready/blockers/warnings 三种结局）。

### 7.3 账户路由归属开关（2026-11-04 已实现，默认不改变行为）

`multi_account/routing.py` + 配置项 `account_routing` / 环境变量 `REVERSE_AGENT_ACCOUNT_ROUTING`：

| 取值 | 生效 owner | 说明 |
|---|---|---|
| `local`（默认） | Nerelan | 与改动前完全一致 |
| `magpie` | Magpie | Nerelan 不再用本地账户健康裁决去否决重路由，也不再产生本地等待提示 |
| `auto` | 见下 | **只有**同时满足 `REVERSE_AGENT_MAGPIE=1` 与 `REVERSE_AGENT_MAGPIE_ACCOUNT_SWITCHING=1` 才解析为 `magpie`，否则 `local` |

第二个开关是必要的：审计只证明了"能力存在"，没有证明"本机行为正确"（M2/M3 标注为能力已确认、
行为未实测）。仅凭端口可达就把路由权交出去，正是规范里禁止的未经验证的行为变更。

owner 为 `magpie` 时的两处行为变化（均为"少做"，不是"多做"）：

- `dispatch.reroute_guard` 恒返回 `skip=False, reason=routing_delegated_to_magpie`
  —— 不再用本地 `EXHAUSTED` 判定否决重路由（那是重复上游决策）；
- `dispatch.idle_wait_seconds` 返回 `None` —— 不再让协调器按本地冷却时间睡眠，
  等待由 Magpie 的 `quota wait` 负责。

`dispatch.account_routing()` 暴露 `{requested, owner, reason, magpie_enabled, switching_acknowledged}`，
运维可直接看到"为什么没有交给 Magpie"。

覆盖测试：`tests/platform_v1/test_multi_account_routing.py`（9 例，含 auto 的两把锁、
未知取值回退、owner 切换后的 guard/等待差异）。

### 7.4 `quota wait` 适配（2026-11-04 已实现，**可中断，opt-in 接入**）

`magpie_wait.py::wait_for_allowance(target, timeout="10m")`：

| 保障 | 实现 |
|---|---|
| 有界 | 硬超时 = 请求窗口 + 15s 宽限；`TimeoutExpired` → `reason="timeout"` |
| 可拒绝 | target 必须是 `[A-Za-z0-9._@:+-]`，含空格/`;`/`&&`/换行/前导 `-` 一律 `invalid_target`，**不启动进程** |
| 不抛错 | 缺二进制 / OSError / 非零退出 → `magpie_error` 或 `magpie_not_configured` |
| 不注入 | 固定 argv、`shell=False`、显式绝对路径 |

**可中断改造（关键）**：原实现用 `subprocess.run`，`stop()` 根本无法打断——这种阻塞调用不能进主循环。
现改为 `Popen` + 每 0.2s 轮询 `cancel`（直接复用协调器的 `_stop` 事件）：

```text
cancel 已置位 → terminate 子进程 → reason="cancelled"
超出自身硬上界 → terminate → reason="timeout"
子进程忽略 terminate → kill 兜底
```

**接入方式（opt-in）**：协调器新增 `quota_wait(wait_seconds)`，仅在
`idle_wait >= QUOTA_WAIT_MIN_SECONDS(60s)` **且** 配置了 `REVERSE_AGENT_MAGPIE_WAIT_TARGET` 时才委托；
单次委托上限 `QUOTA_WAIT_MAX_SECONDS(3600s)`；返回"有额度"则立即继续 tick，否则照常 `_stop.wait`。
未设置目标 → 行为与之前完全一致（默认本地轮询）。

覆盖测试：`tests/platform_v1/test_magpie_wait.py` 14 例，其中 4 例是协调器集成
（不设目标不委托、低于阈值不委托、超长被截断并记录 `quota_wait_*` 错误、**`_stop` 被当作 cancel 令牌**）。

### 7.5 后续步骤（未实现）

1. **真正共享的 join key**：让 Nerelan 把 `task_id` 写进执行器可上报的位置
   （如调用 Magpie 网关时的请求头/会话名），把"时间窗归因"升级为"精确归因"，
   届时 `overlap=partial` 与 `ambiguous` 才可能降到 0。
4. **`quota wait` 探测**：仅在 `idle_wait` 想睡 > 60s 且 Magpie 可用时，改为委托 `quota wait`；
   失败退回现有轮询。
5. **不执行任何写入**：`accounts switch` / `group add` / `provider fallback` 均属改变用户环境，
   必须由 Owner 显式授权后单独进行。

## 8. 本轮未做（明确）

- 未执行 `accounts switch` / `group add` / `provider fallback`（会改动用户登录态或路由配置）。
- 未执行 `quota wait`（阻塞命令）。
- 未发起任何模型调用（无付费、无额度消耗）。
- 未读取、打印或导出任何凭据与账号身份。
- 未把 Magpie 接入生产派发路径——本审计只产出事实与处置建议。

## 9. 证据可复现命令

```bash
F:/magpie/magpie.exe --help
F:/magpie/magpie.exe quota --json            # 只看聚合字段，勿外发
F:/magpie/magpie.exe usage --csv --last 2h   # 只看列名与聚合，勿外发
curl -s http://127.0.0.1:3425/api/hello
curl -s http://127.0.0.1:3425/v1/magpie/quotas?kept=1
```
