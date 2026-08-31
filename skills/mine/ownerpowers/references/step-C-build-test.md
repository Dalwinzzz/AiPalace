# step-C · 专属 Maven 构建自测

> **触发条件**：有代码改动需要本地编译/自测时。

## 硬约束：绝不使用 `~/.m2`

本地 Maven 仓库**不在** `~/.m2`。执行任何 `mvn` 命令必须附加专属参数：

```bash
mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml \
    -Dmaven.repo.local=/Users/dalwin/Library/Repository <goal>
```

常用 goal：`compile`（编译）、`test`（跑测）、`-pl <module> -am`（指定模块）。

## 查找 / 解压依赖 jar

同样走专属仓库，**不用 `~/.m2`**：

- 查找：`find /Users/dalwin/Library/Repository -name "*.jar" ...`
- 解压：`jar tf|xf /Users/dalwin/Library/Repository/...`

## 自测策略

- 优先跑改动相关的最小测试集（按模块/测试类），不必全量。
- 编译失败或测试失败 → 回到实现步骤修复，不要带病提交。
- 自测"通过"必须有**本轮新鲜跑出来的证据**——走 [`../disciplines.md`](../disciplines.md)（T1/T2 必走）。

## 🌿 worktree 探针（进入编码前判）

- **T2 需求开发线**（需隔离的复杂 / 多步功能），或**并行处理多个互不依赖任务** → 进编码前按 [`../policies.md`](../policies.md) **自动起 worktree**，分支名按规范 `<工具>/<类型-taskName>/<日期_版本号>` 生成。
- T0 / T1 在当前工作区直做，不起 worktree。
- ⚠️ worktree 自动只是动作壳；worktree 内代码改动仍走决策点①②。
