`awesome-skills` 仓库的 `.gitignore` 是 "默认忽略一切 + 白名单 skill 目录" 模式（`*` 后面跟 `!skill-name/**`）。

**Why:** 仓库只跟踪 skill 本体（每个 skill 是独立可分发的资产），开发过程文档（`docs/superpowers/{specs,plans,logs}/`）不进 git 是刻意策略。

**How to apply:**
- 在该仓库内做 spec-architect 等 skill 迭代时，把 design / plan / log 写到 `docs/superpowers/` 即可，不需要 force-add 到 git
- 用户要求 "过程记录文档都有" 时，磁盘上存在即满足需求
- 想跟踪新 skill 目录时，必须更新 `.gitignore` 加 `!new-skill/` 和 `!new-skill/**`
- 这条规则与 spec-architect 自身的 `references/auto-commit.md` 一致："被忽略的文件保留在工作区，不进入提交"
