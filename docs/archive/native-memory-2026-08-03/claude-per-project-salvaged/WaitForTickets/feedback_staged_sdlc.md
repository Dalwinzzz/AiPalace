在 WaitForTickets 项目上，用户偏好正式的分阶段 SDLC：产品经理（PRD）→ 架构师（架构文档）→ 技术负责人（实施计划）→ 前后端开发（代码）→ QA / 集成（联调）→ DevOps（部署）。每阶段切换对应角色身份，以"文档审阅 + 用户批准"为硬 gate，未批准不穿透下一阶段。

**Why:** 2026-04-21 用户表达"没有完整项目流程"是之前联调失败的根因之一，明确希望"切换不同项目角色"走一遍完整流程。

**How to apply:** 在 WaitForTickets 上工作时：
- 每阶段结束停下等用户批准，不要连续跨多个阶段
- 产出物放在约定路径：`docs/superpowers/specs/v3/01-prd.md`、`02-architecture.md`、`05-integration-checklist.md`、`06-deployment.md`；实施计划在 `docs/superpowers/plans/v3-implementation-plan.md`
- 每阶段开始时明确"我现在以 XX 身份工作"
- 这是本项目的偏好，不要自动推广到其他项目
