# AiPalace

> 个人本地 AI harness 项目：统一管理 Claude Code + Codex 双工具的 skill 体系、
> 个人上下文层、工作流演化史与架构决策记录。

核心方法论：**来源 → 分类 → skill** 三级组织 + 单一 `registry.yaml` 声明式管理 +
`tier` 分级控制 token 预算 + `sync`/`doctor` 防腐化校验，落地形态为 **symlink（软链派生）**，
详见 [ADR-0005](adr/0005-skill派生回归symlink.md)。

## 目录结构

```
AiPalace/
├─ README.md                  ← 本文件
├─ registry.yaml              ← 单一事实源：每个 skill 的 {source, category, tier}
├─ skills/                    ← 来源 → 分类 → skill 三级
│  ├─ mine/                   ← 原创 skill 源码 SOT（biz-workflow / spec-architect / git-merge-conductor）
│  └─ community/              ← 第三方开源（备份，保留溯源）
│     ├─ garveyhu/            ← 三级保真上游（21 skill，含并入的 deep-research）
│     └─ github-skills/       ← 从各开源项目节选的好用 skill，按来源性质分子目录
│        ├─ anthropic-official/  ← docx…
│        ├─ third-party/         ← skill-security-audit(SlowMist) / app-icon…
│        ├─ misc/                ← 未精确溯源的社区 skill（每个含 _SOURCE.md 线索）
│        └─ grill-me / grill-with-docs  ← mattpocock/skills 选装
├─ plugins/                   ← 本地 AI 插件 SOT（双工具版本，见 plugins/README.md）
│  ├─ claude/                 ← Claude 版（源：claude-plugins）marketplace + sql-expert-dba
│  └─ codex/                  ← Codex 版（源：~/.agents/plugins）marketplace + sql-expert-dba
├─ context/                   ← 个人全局上下文层
│  ├─ CLAUDE.md               ← 热缓存工作记忆
│  ├─ java-spring.md          ← Java/Maven 规则（path-scoped 自动注入）
│  ├─ frontend-web.md         ← Web 前端美学规约（path-scoped 自动注入）
│  └─ memory/                 ← 深度记忆（glossary / ai-workflow / projects）
├─ docs/                      ← 文档管理区（README 为统一规范，archive/knowledge/skill活跃区三分）
│  ├─ README.md               ← 文档管理规范 SOT（archive/knowledge/活跃区 划分与归档规则）
│  ├─ knowledge/              ← 无时效知识（harness-learning 系列 / palace 知识架构记录）
│  ├─ superpowers/            ← skill 活跃区（git-merge-conductor-v2、sql-expert-dba 双版本、verification）
│  ├─ problem/                ← 排查记录与问题复盘
│  └─ archive/                ← 历史归档
├─ creations/                 ← 创作产物
│  └─ mon3tr-codex/           ← codex 桌宠 mon3tr sprite（v1-v4）
├─ adr/                       ← 架构决策记录（AiPalace 自身演进）
└─ tools/
   └─ skillctl.py             ← skill 中央管理工具（stats/sync/doctor/fix，symlink 软链版）
```

## 三层加载策略（tier）

| tier | sync 时软链派生进 `~/.claude/skills` + `~/.codex/skills` | 用途 |
|------|:--:|------|
| `core`   | ✅ | 广泛常用 |
| `extra`  | ✅ | 按需，但仍挂载 |
| `parked` | ❌ | 仅备份留存，不挂载 |

## 日常用法

```bash
python3 tools/skillctl.py            # stats：一眼看生态分布 + 挂载健康
python3 tools/skillctl.py sync --dry # 预览将对 ~/.claude、~/.codex 做什么（不落盘）
python3 tools/skillctl.py sync       # 据 registry 把 core+extra 软链派生进两个 agent 目录
python3 tools/skillctl.py doctor     # 体检：缺 SKILL.md / category 越界 / 悬挂软链 / 孤儿
python3 tools/skillctl.py fix        # 清悬挂受管软链（dry-run；加 --apply 真正删除）
```

工作流：**只改 `registry.yaml` → `sync --dry` 预览 → `sync` → `doctor` 验收**。

## ⚠️ 关于 sync 的安全保证

`skillctl.py sync` 用「受管判定 `is_managed()`」隔离：软链指向仓库 `skills/` 内的条目
视为受管；旧 copytree 残留含 `.aipalace-managed` 标记的目录亦向后兼容。
- **只覆盖/回收受管条目**（软链指向仓库真身，或旧拷贝残留带标记）；
- 遇到你手建的软链或真实 skill 一律 **保护性跳过**，绝不误删。

所以即使现在 `~/.claude/skills` 里已有旧条目，跑 `sync` 也只会**补齐/更新受管的**、不动既有非受管的。
悬挂的受管软链（真身已被删）可用 `fix --apply` 清理。
