feature 分支开发完成、最终合并回 `develop` 时，要把该 feature 的**所有 commit 整合（squash）成单个提交**再进 develop——develop 上每个需求只留一条提交记录。

**Why:** 用户希望 develop 历史按"需求/功能"粒度保持干净线性，而非保留 feature 内部的中间过程提交。

**How to apply:** feature 分支内可正常多次提交（含 TDD 的 RED/GREEN 小步）；合并前用 squash（如 `git merge --squash` 或交互式 rebase 压缩）整合为一条，再合入 develop。与 [[urgent-piece-cherrypick-to-develop]]（急件子功能单独 cherry-pick）是两种不同交付路径，按场景选用。
