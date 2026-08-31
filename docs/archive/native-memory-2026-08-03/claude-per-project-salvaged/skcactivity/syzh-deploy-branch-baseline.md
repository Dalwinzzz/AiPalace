skcactivity 仓库新建 worktree 的**默认基线是 `origin/master`**（claude/* 会话分支默认 track origin/master）。但 **syzh（善育在杭，杭州/萧山，走 Kingbase）的线上活属于部署分支 `release/syzh260110`**，该本地分支 track `origin/syzh260110`（远程分支名是 `syzh260110`，不是 `release/syzh260110`）。

**How to apply：** 接到 syzh 部署分支的需求/工单，开工前先确认基线——不要在默认的 master 基线上改。正确做法：`git reset --hard origin/syzh260110`（或直接基于它建分支）。改完后若误提交到了 master 基线的会话分支，因 `release/syzh260110` 仍停在远程同一提交，通常可直接 `git branch -f release/syzh260110 <commit>` 干净快进，再把会话分支 detach + 删除。推到远端用显式 refspec：`git push origin release/syzh260110:syzh260110`（本地名≠远程名）。

**Why：** 曾因 worktree 默认 track origin/master，把善育在杭的修复 commit 落到了 master 基线的会话分支上，需事后快进搬运到 release/syzh260110。相关构建规则见 [[skcactivity-build]]。
