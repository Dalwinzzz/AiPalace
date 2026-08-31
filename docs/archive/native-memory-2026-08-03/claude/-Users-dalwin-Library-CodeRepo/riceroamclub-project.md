---
name: riceroamclub-project
description: RiceRoamClub 米游社复刻项目 — Kratos 模块化单体 + React Web，进度锚点在 PROJECT_PLAN.md §5，每 2h 定时任务续推
metadata: 
  node_type: memory
  type: project
  originSessionId: f7b98c1a-5b37-4635-b2f0-e02acfd6a7fd
---

项目**已于 2026-07-05 完成**（M0–M12 全部里程碑）：米游社复刻，路径 `~/Library/CodeRepo/RiceRoamClub`。Kratos **v3** 模块化单体 + 事件 worker（Redis Stream），九大业务域约 50 接口；前端 React 19 + Vite 移动端 Web 13 页面；MySQL 8.4（compose 钉死，卷由 8.4 初始化不可降级）+ Redis 7。一键启动 `./scripts/dev-up.sh`（+ seed-demo.sh 演示数据，recalc-counters.sh 计数校准）。压测 feed 3300 QPS/P99 69ms。文档齐备：LEARNING（Java↔Go 学习路线）/INTERVIEW/LOCAL_DEV（含测试账号密码 pass1234 与六大坑）/PERFORMANCE/RETROSPECTIVE。

**Why:** 用户 Java 转 Go 求职（见 [[go-transition]]），与 TreeSkyIsland（go-zero 九微服务）构成框架对比矩阵——面试叙事「单体分层+异步化 vs 微服务拆分+治理」。

**How to apply:** 后续如继续演进，优先做 RETROSPECTIVE「如果重来」清单（事件幂等 ID/推拉结合 feed/biz 层单测回补）；改 proto 记得 `make api` + publicOperations 登记；Node 用 /opt/homebrew/opt/node@22。
