在这个 harness 的 Bash 工具里，工作目录在调用间持久。如果一条命令用 `cd backend && <cmd>`，下一条命令的相对路径基准就变成了 backend/，导致 `grep backend/services/...`、`head backend/...` 之类报 "No such file or directory"。在 WaitForTickets（backend/ 子目录跑 uv/pytest）反复踩到。

**Why:** 2026-06-09 Phase 4 开发期间多次因 compound 命令里的 `cd backend` 让紧接的 spec-review grep 命令失败、退出码非零中断。

**How to apply:** 需要在子目录跑命令时（如 `cd backend && uv run pytest`），用**子 shell 包起来**：`(cd backend && uv run pytest ...)`，或每条命令开头先 `cd /Users/dalwin/Library/CodeRepo/WaitForTickets`。验证类命令一律用仓库根绝对路径拼文件路径，不依赖当前 cwd。另：`grep -c` 无匹配返回 exit 1 会中断 `&&` 链，单独跑或用 `|| true`。关联 [[project_v3_restart]]。
