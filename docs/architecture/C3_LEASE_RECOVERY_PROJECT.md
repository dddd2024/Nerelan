# 立项：C3 租约与恢复一致性（长时间无人值守）

> 独立审查修正：此前声称 W2/W3 已接线不成立。候选只有执行前检查，不能保护执行后
> 产物和恢复路径。生产调用已撤出，保留的 helper/kill9 仅为组件探针。
> 当前边界以 [交付状态](MULTI_ACCOUNT_DELIVERY_STATUS.md) 为准；C3 未完成验收。

```text
STATUS: PROPOSED — 未实现，未改动任何租约/恢复代码
AUTHORITY: 需独立立项 + 独立评审（风险高于普通 R1）
OWNER DECISION: 2026-11-04，列为长时间无人值守能力的高优先级任务
RELATED: MULTI_ACCOUNT_ORCHESTRATION_SPEC.md §7 C3 / §12.3
```

## 1. 要解决的真实风险

"任务失败"可以重试；**"两个执行器同时以为自己拥有同一个任务"** 不能。
后者会写坏工作区、重复创建 PR、重复触发外部副作用，而且事后很难还原。

现有实现已有基础（`durable_execution.py`）：

- 租约 epoch 作为**单调 fencing token**（模块 docstring §11）；
- 陈旧 owner/epoch 的写入**fail-closed**（`StaleLeaseError` / `durable_single_fenced_*`）；
- `_HeartbeatContext` 在执行期间续期；
- `_recover_durable_lease(..., require_interrupted=True)` 只恢复 `INTERRUPTED` 的 run。

**缺口不在"有没有 fencing"，而在四个方面**：

1. fencing 是否覆盖了**全部**写入面（工作区文件、外部副作用、证据、用量），还是只覆盖了数据库行；
2. **休眠/时钟跳变**下 heartbeat 的语义（本机休眠时进程不运行，唤醒后时间已过）；
3. **恢复协议**在"旧执行器其实还活着"时的行为；
4. 上述三者**没有故障注入证据**。

## 2. 失败模式清单（必须逐一有测试）

| # | 场景 | 期望 | 当前证据 |
|---|---|---|---|
| F1 | 宿主休眠 > lease 时长后唤醒，旧执行器仍在内存中继续跑 | 旧写入被拒（fencing），任务不被重复派发 | 未验证 |
| F2 | 进程被 `kill -9`，租约未过期 | 重启后按 checkpoint 恢复，不产生第二个写入者 | 未验证（有 `require_interrupted` 保护，未注入） |
| F3 | 网络/文件系统短暂失联，heartbeat 失败 | 不得因一次续期失败就放弃租约，也不得无限重试 | 未验证 |
| F4 | 系统时钟向前/向后跳变 | 过期判定不因墙钟跳变而误判 | 未验证 |
| F5 | 恢复时 checkpoint 落后于工作区实际内容 | 以 checkpoint 为准，拒绝"超前"产物 | 未验证 |
| F6 | 外部副作用已发生但任务被判失败 | 幂等键去重，不重复建 PR / 不重复评论 | 部分（有 `idempotency_key`，未注入验证） |

## 3. 必须成立的不变式

- **I1 单写者**：任一 `task_id` 在任一时刻，最多一个 `(owner, epoch)` 能成功写入受保护状态。
- **I2 单调性**：新 epoch 严格大于旧 epoch；epoch 不得回退或复用。
- **I3 检查点单调**：恢复只接受"不早于最新 checkpoint"的产物；更早的产物一律丢弃。
- **I4 副作用幂等**：所有对外动作以 `(task_id, action, epoch)` 或业务幂等键去重。
- **I5 休眠不伪造心跳**：休眠期间不得由后台定时器"补发"心跳；唤醒后必须先做一次显式对账，
  再决定续租或放弃。

> I5 是对"更频繁 keepalive 就能修好"这一直觉的否定：休眠时进程不跑，心跳本就不该发生；
> 醒来后的**对账**才是正确动作。

## 4. 设计草案（待评审，不是结论）

1. **写入面普查**：枚举所有能被执行器写到的位置（DB 行、工作区文件、证据目录、外部 API），
   逐项标注"已 fencing / 未 fencing / 天然幂等"。产出矩阵，作为实现前置。
2. **fencing token 外带**：把 `(run_id, owner, epoch)` 写进工作区分支名或 `.fence` 文件，
   使**文件系统写入**也能被校验（当前只校验 DB 行）。
3. **唤醒对账协议**：`on_wake()` → 读取租约 → 若 `expiry > now` 且自己是 owner → 续租；
   否则按 `INTERRUPTED` 恢复流程，且必须 `require_interrupted=True`。
4. **时钟语义**：过期判定统一用单调时钟 + 持久化墙钟双写，跳变时以单调差值为准。
5. **幂等键**：外部动作统一走 `idempotency_key`，恢复时先查已发生的动作再执行。

## 5. 测试计划（故障注入矩阵）

| 注入手段 | 覆盖 F | 断言 |
|---|---|---|
| 进程内 monkeypatch 单调时钟跳跃 | F4 | 过期判定不误判；epoch 不回退 |
| 子进程 `kill -9` + 重启恢复 | F2 | 唯一写入者；checkpoint 一致 |
| 暂停线程（模拟休眠）后恢复 | F1, F5 | 旧 epoch 写入被拒；超前产物被丢弃 |
| 断网/只读 FS 模拟 | F3 | 续期失败有界重试；不静默丢租约 |
| 重复调用外部动作适配器 | F6 | 只产生一次副作用 |

每条注入必须**先复现缺陷**（红）再修（绿），否则不算证据。

#### 已建骨架（2026-11-04，仅测试，未改生产代码）

`tests/platform_v1/test_lease_invariants.py` —— 直接打 `TaskStore` 的租约/检查点 API：

| 已覆盖 | 断言 | 对应 |
|---|---|---|
| 首次认领归属 | `epoch == 1`、owner 唯一、token 校验通过 | I1 |
| 二次认领被拒 | `durable_run_already_active` | I1 |
| 恢复递增 epoch | `recovered.epoch == lease.epoch + 1` | I2 |
| 旧 owner 被 fence | `_validate_durable_lease` → `lease_fenced`；`_fenced_add_evidence` 拒写且不落库 | F1（DB 半） |
| 活租约不可被"恢复" | `durable_recover_wrong_task_status` | F2（守卫半） |
| 两个救援者不能都赢 | 第二次 recover 抛错 | I1 |
| 检查点不倒退/不跳级/幂等/带 fence | `checkpoint_sequence_regression`、重复接受不产生重复历史 | I3 |
| **休眠后不能把 lease 续回来** | 过期且被恢复后，旧 owner 的 heartbeat → `lease_fenced` | **I5** |

**工作区令牌（F1 的文件半）已实现并接线，默认关闭**：

- 模块 + 接线（W1 发布 / W2 产物收集前校验 / W3 恢复后接管）见
  [C3_WORKSPACE_FENCE_DESIGN.md](C3_WORKSPACE_FENCE_DESIGN.md)；
- 开关 `REVERSE_AGENT_WORKSPACE_FENCE` 默认关闭 → 行为逐字节不变（有测试断言"关闭时不留任何文件"）；
- 端到端 `kill -9` 场景仍未验证——单测证明判据正确，不证明整条恢复链在真实崩溃下正确。

#### F2 端到端已覆盖（2026-11-04）：真实进程 `kill -9`

`scripts/lease_kill9_check.py`（人工运行，默认不进 CI）：

```bash
python scripts/lease_kill9_check.py          # 自清理，输出 PASS/FAIL
python scripts/lease_kill9_check.py --keep   # 保留临时工作区供排查
NERELAN_RUN_KILL9=1 python -m pytest tests/platform_v1/test_kill9_acceptance.py -q
```

流程与实测（本机一次运行）：

| 步骤 | 观测 |
|---|---|
| 子进程真实认领租约、**写工作区标记 + 令牌**后阻塞 | `marker_written_before_kill=True`（证明它确实执行过） |
| `kill`（不可捕获） | `child_killed_ms=10`，子进程无清理机会 |
| 新 owner 恢复 | `epoch_advanced_by_one=True` |
| 死亡 owner 再校验/写证据 | `old_owner_fenced=True`、`dead_owner_write_refused=True`、`dead_owner_evidence_absent=True` |
| 工作区令牌接管 | `workspace_token_owner=owner-new` |
| 再认领同一任务 | `no_second_run=True`（`durable_run_already_active`） |

**这就是之前"单测证明判据、不证明整条链"的那一步**：现在跨真实进程边界验证过了。

#### 尚未覆盖（需环境/时间）

- F3：心跳期间存储短暂不可用（需要可注入的存储故障层）；
- F6：外部副作用幂等（PR/评论重复创建，需要真实远端或适配器）；
- 24h 连续运行 + 3 次休眠 + 2 次强杀（C3 §6 A3 的长跑门槛）。

#### 工作区令牌：模块已实现，接线待评审

`reverse_agent/platform_v1/workspace_fence.py` + 设计草案
[C3_WORKSPACE_FENCE_DESIGN.md](C3_WORKSPACE_FENCE_DESIGN.md)：

- `.nerelan-lease.json` 原子写入 worktree，记录 `(run_id, owner, epoch)`；
- 陈旧 owner 校验必失败，缺失/损坏按"无主→认领"，**绝不把不匹配当成可认领**；
- 接线只有三处（W1 发布、W2 产物收集前校验、W3 恢复后覆盖），开关默认关闭；
- 17 例测试全绿（含接线与"关闭即无副作用"）。

## 6. 验收标准

- A1：F1–F6 全部有可复跑的注入测试，且**在修复前能复现失败**。
- A2：I1–I5 各有至少一个断言（不是文档承诺）。
- A3：24h 连续无人值守 + 至少 3 次休眠/唤醒 + 2 次强杀，无丢任务、无重复执行。
- A4：恢复后 `git status` 干净（无残留脏工作区），无孤儿 worktree（已有 `workspace_reclaim` 可复用）。
- A5：不降低既有门禁：`baseline` / `state-gate` / `landing-state-gate` 仍全绿。

## 7. 非目标（明确不做）

- 不引入 Temporal/DBOS（触发条件见规范 §2.2）。
- 不重写 LangGraph 编排或 `durable_execution` 的整体结构；只在**写入面**补 fencing 与协议。
- 不改动治理门禁、评审流程、发布边界。
- 不在本轮与多账户改动混提（两者风险叠加会难以定位回归）。

## 8. 交付物

1. 写入面矩阵（§4.1 产出）；
2. 唤醒对账协议与状态机图；
3. 故障注入测试套件（`tests/platform_v1/test_lease_recovery_*.py`）；
4. 一次 24h 长跑记录（含休眠/强杀时间线）；
5. 独立评审意见（必须由未参与实现的评审者给出）。

## 9. 风险与回滚

- 风险：过度 fencing 会让正常恢复变慢或误拒（假阳性），因此每条 fencing 都必须有"合法路径"测试。
- 回滚：所有改动集中在 `durable_execution` 的写入面与对账入口，可按开关退回现有行为；
  开关默认关闭，验证通过后再开。
