# step-E · git 提交（git-commit-convention）

> **触发条件**：有代码改动且已通过决策点②。

## 提交规范

格式：`<type>(<scope>): <subject>`（冒号后有空格，subject 用中文简短描述）。

type：feat / fix / docs / style / refactor / perf / test / chore / revert / build
scope（选填）：作用范围或目录名。

示例：
- `feat(order): 增加订单导出分页参数`
- `fix(auth): 修复登录空指针`

## 流程

1. 在决策点②已向用户摊出 diff 概要与提交计划并获确认。
2. `git add <相关文件>`（只 add 本次改动文件，不裹挟无关变更）。
3. `git commit -m "<规范 message>"`。
4. **不自动 push**——push 属不可逆操作，需用户额外确认后才执行。
5. pre-commit hook 报错时：向用户报告并停止，不加 `--no-verify` 跳钩。
