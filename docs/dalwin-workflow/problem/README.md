# 问题追踪看板

## 状态约定

| 文件名后缀 | 含义 | 负责人 |
|---|---|---|
| 无后缀 | 待修复（新进问题） | — |
| `-已修复待验证` | 已实施修复，待实际使用确认 | Claude 完成修复后加 |
| `-已解决` | 已通过实际使用验证，问题关闭 | 用户确认后改名 |

**新问题进来**：截图直接放本目录，文件名简述问题即可，无需加后缀。
**修复完成**：Claude 在修复任务结束时在文件名追加 `-已修复待验证`。
**确认解决**：用户实际验证无误后，手动将 `-已修复待验证` 改为 `-已解决`（用户保留动作）。

---

## 当前问题登记

### ⏳ 已修复待验证

| 文件 | 问题描述 | 关联修复 | 修复日期 |
|---|---|---|---|
| `memory没起效-已修复待验证.png` | Claude 执行 `jar xf ~/.m2/...`，违反 Maven 本地仓库规则 | 个人全局上下文层 java-spring.md (path-scoped rule) | 2026-06-02 |
| `memory没起效问题1-已修复待验证.png` | Maven 规则存于全局 memory 但换项目后未注入（git-root 隔离导致） | 同上；根因 + 机制文档见 `docs/superpowers/specs/2026-06-01-personal-context-layer-design.md` | 2026-06-02 |

### ✅ 已解决

| 文件 | 问题描述 | 关联修复 | 解决日期 |
|---|---|---|---|
| `cc工具调用解析失败与卡死-已解决/` | 工具调用解析失败/参数无效/socket 断连/卡死（5 张 StateOpen 截图）。**复现实测定根 = Opus 4.8 工具调用序列化 bug**（与上下文大小/输出长度无关，retry 无效）；初判"上下文撑爆"已被证伪 | 同目录 `修复说明.md`。处置：**CLI 少用 Opus 4.8 + max**，默认 effort 降 high、切 stable 通道、node 降 v20 LTS。biz-workflow 任务回归无数据损失 | 2026-06-10 |

### 🔴 待修复

_（暂无）_

---

## 修复参考

- 个人全局上下文层 spec：`docs/superpowers/specs/2026-06-01-personal-context-layer-design.md`
- 实施日志：`docs/superpowers/plans/logs/2026-06-01-personal-context-layer.md`
- 规则实体：`context/java-spring.md`
