AI 生成的技术设计方案/spec 类文档，放在项目根下的 `spec-architect/` 目录，该目录被全局 gitignore（`~/.config/git/ignore-ideaproject` 的 `**/spec-architect/` 条目，同文件还 ignore 了 `**/docs/commit-review/`、`**/*Test.java` 等个人 AI 产物）。

**Why:** 非紧急需求的设计稿若放进 docs/ 等 git 追踪目录，会以 untracked 文件形式污染 git status，干扰其他任务的 git 探察。用户会后续抽空 review 再继续完善，不需要进版本库。

**How to apply:** 出设计文档时直接写到 `<项目根>/spec-architect/<主题>-design.md`；除非用户明确要求进 docs/ 或提交。当前已有：`spec-architect/coupon-seckill-design.md`（托育券秒杀方案，2026-07-08 初稿待用户 review）。
