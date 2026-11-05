# C3 设计草案：工作区租约令牌（Workspace Lease Token）

```text
STATUS: MODULE + WIRING IMPLEMENTED, FLAG OFF BY DEFAULT, AWAITING INDEPENDENT REVIEW
MODULE: reverse_agent/platform_v1/workspace_fence.py
WIRING: durable_execution.py（single + sequential 各 W1/W2，恢复路径 W3）
TEST: tests/platform_v1/test_lease_invariants.py (17 passed)
FLAG: REVERSE_AGENT_WORKSPACE_FENCE=1（默认关闭 → 行为逐字节不变）
```

## 1. 问题（为什么数据库 fencing 不够）

现有租约令牌只保护 **SQLite 行**：

- `_validate_durable_lease` / `_fenced_add_evidence` / `_accept_checkpoint` 都会比对 `(owner, epoch)`，
  陈旧写入被拒——这部分已经可靠（见 `test_lease_invariants.py` 9 例）。

但**工作区里的文件没有任何令牌**。一次"旧执行器其实还活着"的事故会是这样：

1. A 持租约在 `worktrees/task-x` 里改了文件；
2. A 心跳中断（休眠/网络/被暂停），租约过期；
3. B 恢复租约（epoch+1），继续在**同一路径**工作；
4. A 醒来继续写同一批文件；
5. 产物 diff 由谁收集、提交、发布——取决于时间点，**这就是不可控重复执行**。

数据库层会拒绝 A 的 checkpoints，但**文件内容已经被 A 改过**，B 的产物里混进了 A 的写入。

## 2. 设计

在 worktree 根写入一个令牌文件 `.nerelan-lease.json`：

```json
{"version": 1, "run_id": "run-task-x-ab12", "owner": "coordinator-1a2b", "epoch": 3}
```

规则：

| 场景 | 行为 |
|---|---|
| 令牌缺失（旧工作区 / 首次） | **认领**：写当前令牌（`adopt_missing=True`） |
| 令牌匹配 | 放行 |
| 令牌不匹配，调用方 epoch **更大** | **合法接管**（只有 DB 级恢复能产生更大 epoch），覆盖令牌 |
| 令牌不匹配，调用方 epoch 更小/相等 | 抛 `WorkspaceFenced`，**绝不认领** |
| 令牌损坏/截断 | 视为"无主"，按缺失处理（写入方向安全） |
| 原子性 | temp + `os.replace`；崩溃不会留下半截文件 |

**它保证什么**：任何后续阶段可以拒绝"令牌已过期"的产物，从而阻止陈旧执行器**发布**。
**它不保证什么**：阻止任意进程写文件。这是 fencing token，不是沙箱——强制点在"检查处"。

## 3. 接线点（已实施）

只有三个位置需要改，全部在 `durable_execution.py`：

| # | 位置 | 调用 | 目的 |
|---|---|---|---|
| W1 | 工作区就绪、首次 checkpoint 之前（`_execute_single_with_lease` 的 `_set_checkpoint_db_path` 之后，约 L1109；sequential 路径约 L1976） | `publish_token(worktree, LeaseToken(run_id, owner, epoch))` | 声明"这个 worktree 归我" |
| W2 | **产物 diff 收集之前**（`_collect_product_diff` 调用点：L1124 / L2015 / L2503 / L2533 / L2563 / L3138 / L3532） | `verify_token(worktree, token, adopt_missing=False)` | 陈旧 owner 在此被拒，产物不被采信 |
| W3 | 恢复租约之后（`_recover_durable_lease` 返回处） | `publish_token(...)` 覆盖为新 epoch | 新 owner 立即接管，旧 owner 下次校验必失败 |

> 为什么选"产物收集前"而不是每个 checkpoint：checkpoint 已有 DB 级 fence；
> 真正的风险是**产物被采信/发布**，那里才是必须校验的点。少而准，好评审。

## 4. 迁移与兼容

- **在建运行**：升级时可能有 run 正在跑，其 worktree 没有令牌 → `adopt_missing=True` 让当前 owner 认领，
  不会误杀；下一次 recover 会覆盖为新 epoch。
- **历史 worktree**：无令牌 → 首次访问时认领。旧数据不需要批量迁移。
- **只读路径**（如 `review` 独立运行目录）：不写令牌，保持原样。

## 5. 上线与回滚

- 开关：`REVERSE_AGENT_WORKSPACE_FENCE=1`，默认关闭 → 默认行为与今天**逐字节一致**。
- 打开顺序：先只开 W1（发布令牌，不校验，观察无副作用）→ 再开 W2/W3。
- 回滚：关开关即可；已写入的令牌文件对未开启的功能无影响（不被读取）。
- 观测：`WorkspaceFenced` 带 `run_id/owner/epoch`，可直接定位是哪次恢复产生的竞争。

## 6. 验收

| 编号 | 标准 | 现状 |
|---|---|---|
| WF1 | 令牌原子写入、可读回、无 `.tmp` 残留 | ✅ `test_workspace_token_is_published_atomically_and_read_back` |
| WF2 | 陈旧 owner 校验被拒，错误信息含双方 owner/epoch | ✅ `test_a_superseded_writer_is_refused_by_the_workspace_token` |
| WF3 | 缺失令牌被认领；`adopt_missing=False` 时拒绝 | ✅ `test_current_owner_verifies_and_missing_tokens_are_adopted` |
| WF4 | 损坏令牌按无主处理，不被信任 | ✅ `test_a_corrupt_token_is_treated_as_unowned_not_trusted` |
| WF5 | 开关默认关闭 | ✅ `test_the_fence_is_off_unless_explicitly_enabled` |
| WF6 | `durable_execution` 真的发布并校验令牌（W1/W2/W3） | ✅ `test_execution_path_publishes_and_checks_the_workspace_token` |
| WF7 | 关闭开关时**不写任何文件**，行为逐字节不变 | ✅ `test_fencing_is_a_no_op_when_disabled` |
| WF8 | 接管只允许"更大 epoch"，否则拒绝 | ✅ `test_a_superseded_writer_is_refused_by_the_workspace_token`（反向）+ WF6（正向接管） |

**仍未验证（需要真实进程）**：`kill -9` 后由新 owner 恢复、旧 owner 醒来续跑的端到端场景。
单测证明的是"令牌与判定逻辑正确"，不是"整条恢复链在真实崩溃下正确"。这条留给 C3 §5 的注入矩阵。

**上线顺序**（重要）：
1. 先只开 W1（`publish` 不校验）：观察 `.nerelan-lease.json` 正常写入、无异常；
2. 再开 W2/W3（校验 + 接管）：此时若有误判，会以 `workspace_fenced` 显式失败而不是静默；
3. 任一阶段异常 → 关开关即回滚，令牌文件对未开启功能无副作用。

## 7. 与外部副作用幂等（F6）的关系

令牌解决"谁的产物算数"；**重复触发外部动作**是另一个问题（PR/评论重复创建），
由 `idempotency_key` 与 publication 记录覆盖，验收见 C3 §5 F6。
两者不可互相替代：令牌不阻止重复调用，幂等键也不阻止陈旧产物被采信。
