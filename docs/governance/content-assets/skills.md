# skills.md — 能力资产规范

> 本文档是 AiPalace 能力资产（skills）的规范性说明，定义"是什么"与"怎么遵循"。  
> 最高准绳：[`PHILOSOPHY.md`](../../../PHILOSOPHY.md)（P1–P9）。

---

## 1. 定位

**skills** 是 AiPalace 管理的能力资产——每个 skill 是一段可被 Claude Code / Codex 调用的 AI Agent 能力单元（通常包含触发描述与执行指令）。

skills 是**内容资产**（见 [P7](../../../PHILOSOPHY.md#p7--内容统一源机制分治)）：其内容工具无关，统一存放于本仓库；工具侧挂载点（`~/.claude/skills/`、`~/.codex/skills/`）为派生产物，不作为内容修改入口（见 [P2](../../../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)）。

---

## 2. 三级物理结构

skill 真身存放于仓库内的三级目录结构：

```
skills/
└─ <class>/          # 归属分层（封闭集）
   └─ <source>/      # 来源标识（开放）
      └─ <skill>/    # skill 名称目录
         ├─ SKILL.md
         └─ ...（其他文件）
```

- **`<class>`**：封闭集，仅三个取值：`mine`（本人创建）、`enterprise`（企业/公司内部）、`community`（上游社区）。
- **`<source>`**：开放字段，标识具体来源（如作者 ID、仓库名、组织名）。
- **`<skill>`**：skill 目录名，与 `SKILL.md` 中的 `name` 保持一致。

三级结构体现 [P3](../../../PHILOSOPHY.md#p3--来源优先的归属分层判别方式按资产分化)：归属分层靠证据，不靠猜。

---

## 3. registry 单一源

`registry.yaml` 是 skill 的唯一声明源（体现 [P2](../../../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)）。

**每个 skill 条目必须登记以下字段：**

| 字段 | 含义 | 约束 |
|------|------|------|
| `source` | 三级路径中的 `<class>/<source>/<skill>` | 对应真身目录 |
| `category` | 功能分类 | 封闭集（见第 4 章） |
| `tier` | 挂载等级 | `core` / `extra` / `project` / `parked` |
| `project` | 归属项目名（仅 `tier: project` 时必填；**可多值、逗号分隔无空格**如 `zhijin,zhijin_etl`，见 [ADR-0017](../../../adr/0017-project-tier支持多项目归属.md)） | 每个项目都须在 `projects:` 段声明 |

`registry.yaml` 是**手改的唯一入口**；所有下游派生物（挂载点软链）由 `skillctl sync` 自动生成，禁止手动编辑。

---

## 4. 分类体系

`category` 字段使用**封闭集**，共 9 类：

| 类别 | 说明 |
|------|------|
| `workflow` | 工作流编排、任务管理、流程 SOP |
| `method` | 方法论、思维框架、分析方式 |
| `sql` | SQL 相关能力（查询、优化、诊断） |
| `stack` | 技术栈专用能力（语言/框架/平台） |
| `docs` | 文档生成、整理、规范写作 |
| `design` | 系统设计、架构规范、spec 撰写 |
| `diagram` | 图表生成（流程图、架构图、时序图等） |
| `media` | 媒体类内容（图像、视频、演示） |
| `meta` | 元能力（skill 管理、harness 自维护） |

**封闭集不可自行扩展。** 需要新类别时，必须先修改本规范（走 ADR 流程），再新增 skill。

---

## 5. tier 与挂载

tier 控制 token 预算与 `/` 菜单可见性（体现 [P4](../../../PHILOSOPHY.md#p4--分级控预算tier)）：

| tier | 行为 |
|------|------|
| `core` | 进全局挂载；`/` 菜单可见；优先加载；同时进扁平镜像 |
| `extra` | 进全局挂载；`/` 菜单可见；按需加载 |
| `project` | **移出全局**；仅 opt-in mount 至指定项目 `.claude/skills`；须声明 `project:` 字段 |
| `parked` | **不挂载**；仅在仓库内备份；不占 token 预算 |

**双 mount**：`core`/`extra` 同时软链派生至两个全局挂载点：
- `~/.claude/skills/<skill>/`
- `~/.codex/skills/<skill>/`

**project mount**：`tier: project` 的 skill 不进全局挂载，由 `skillctl mount <项目>` 按需挂至 umbrella + 其下每个 git 仓根的**双发现目录**（两工具项目级发现路径零重叠，见 [ADR-0015](../../../adr/0015-project-skill双发现路径派生补齐Codex侧.md)）：
- `<git根>/.claude/skills/<skill>/`（Claude Code 发现路径）
- `<git根>/.agents/skills/<skill>/`（Codex 发现路径）

挂载点均为派生物，不作为内容修改入口。超出 token 预算前，先降 tier 再新增 skill。

---

## 5a. 挂载名 = SKILL.md `name`（ADR-0006 实测）

`skillctl sync` 派生软链时，挂载目录名取 `registry.yaml` 中的 key **basename**，与 `SKILL.md` 文件头的 `name` 字段保持一致（见 [ADR-0006](../../../adr/0006-同步garveyhu新版四层tier与project挂载.md)）。

- 斜杠菜单按 `name` 字段显示；basename = name 是 `/` 菜单正确显示的前提。
- **key 中含 `/` 时**（如 `garveyhu/style-vault`），取最后一段 `style-vault` 作为挂载名，与 `SKILL.md` 的 `name: style-vault` 对应。

---

## 5b. 扁平镜像（core 默认加载层）

`flat_mirror` 是可选的第三目标目录（在 `registry.yaml` 顶部声明），专供支持"默认加载层"的 agent runtime 使用：

- **仅 `core` tier** 的 skill 被软链至扁平镜像目录，`extra` / `project` / `parked` 均不进入。
- 扁平镜像**不含 `core/` 中间层**，skill 目录直接平铺（`<flat_mirror>/<skill>/`）。
- `registry.yaml` 中 `flat_mirror:` 注释占位，取消注释即激活；本轮机制已就绪，未强制启用。

---

## 6. 派生形态：symlink

所有挂载均采用 **symlink（软链）** 形态，软链回仓库内的真身目录（见 [ADR-0005](../../../adr/0005-实测修正symlink可见性并回归symlink派生.md)，体现 [P5](../../../PHILOSOPHY.md#p5--实证选型不照搬)）。

**symlink 的优势（实测确认）：**
- `/` 菜单即时可见；
- 真身更新即时生效，无需重新 sync；
- 零额外磁盘占用。

**受管标记**：每条由 `skillctl sync` 生成的软链均附带 `.aipalace-managed` 受管标记。prune 时仅清理带标记的软链，对无标记对象保护跳过，零误删（体现 [P6](../../../PHILOSOPHY.md#p6--零破坏演进)）。

**两层区分：**
- 仓库内 `community/` 或 `enterprise/` 目录下的真身是**硬拷贝备份快照**（由 `upstream_sync.py` 维护，不变）。
- `skillctl sync` 派生到挂载点的是 **symlink**，指向上述真身。

---

## 7. 纳入合格标准

以下 6 条为**硬门槛**。`doctor` 不绿不予 `sync`：

| # | 硬门槛 |
|---|--------|
| 1 | 有 `SKILL.md` 且 `name`+`description` 非空（触发语质量为正文最佳实践建议，非硬门槛） |
| 2 | 落在三级路径 `skills/<class>/<source>/<skill>/` |
| 3 | registry 登记 `{source, category, tier}` 三字段齐全 |
| 4 | `category` ∈ 封闭集合 |
| 5a | community 附 `_SOURCE.md`（license/credit/upstream，无法溯源标"待补"不编造） |
| 5b | enterprise 附标注（公司/项目/**可见性边界** + license） |

> license 不单列门槛，作为 5a/5b 标注文件的**必填字段**。

`mine` 类 skill 无需 `_SOURCE.md`（自身即来源），但仍须满足门槛 1–4。

---

## 8. 溯源规范

溯源体现 [P3](../../../PHILOSOPHY.md#p3--来源优先的归属分层判别方式按资产分化)：归属靠证据，不编造。

**community skill 的 `_SOURCE.md` 必须包含：**
- `upstream`：上游仓库 URL 或标识
- `credit`：原作者/组织
- `license`：原始许可证
- 无法确认任一字段时，该字段标 `"待补"`，不编造

**enterprise skill 的标注文件（可嵌入 `SKILL.md` 或单独 `_SOURCE.md`）必须包含：**
- 所属公司/项目
- `visibility`：可见性边界（如 `internal-only`、`team-only`）
- `license`：内部使用条款或授权说明

**mine skill**：`<source>` 字段填作者 ID，无需额外溯源文件。

---

## 9. doctor 校验项

`skillctl doctor` 执行以下校验：

| 校验 | 覆盖 | 行为 |
|------|------|------|
| registry 条目的三级真身存在且含 SKILL.md（name/desc 非空） | 门槛 1/2 | 缺失→报错 |
| registry 三字段齐全、category 在封闭集 | 门槛 3/4 | 违规→报错 |
| community 有 `_SOURCE.md` / enterprise 有标注 | 门槛 5 | 缺失→报错 |
| `tier: project` 须有 `project:` 字段且在 `projects:` 段声明 | project tier 完整性 | 违规→报错 |
| 两挂载点无同名冲突 | 挂载安全 | 冲突→报错 |
| 受管软链悬挂检测（`.aipalace-managed` 软链指向真身仍在） | symlink 健康 | 悬挂→报错 |
| **孤儿检测**：`skills/` 有真身但 registry 未登记 | 防漏登记 | **warning** |

全部报错为零且无阻塞性 warning，`doctor` 才返回绿灯。`sync` 依赖 `doctor` 绿灯方可执行。

---

## 10. `doctor --fix` 安全边界

`--fix` 的操作范围严格限于**受管域**（体现 [P6](../../../PHILOSOPHY.md#p6--零破坏演进)）：

**允许自动修：**
- 清理带 `.aipalace-managed` 标记的**悬挂**软链（真身已不存在）
- 对 registry 已声明、指向真身存在但缺少受管标记的软链，补加 `.aipalace-managed` 标记

**绝对禁止：**
- 给无标记软链补标记（擅自收编用户手建物）
- 删除任何无标记对象
- 孤儿 skill 自动登记 registry（仅 warning，须人工决策）

**执行方式：**
- `--fix` 默认 **dry-run**，仅打印将执行的操作，不落盘
- 加 `--confirm` 才实际落盘执行

---

## 11. 日常工作流

新增或修改 skill 的完整流程（体现 [P2](../../../PHILOSOPHY.md#p2--声明式管理工具派生限内容资产)）：

```
1. 修改 registry.yaml          ← 唯一手改入口
2. skillctl sync --dry          ← 预览将生成/更新的软链，确认无误
3. skillctl sync                ← 实际派生软链到两个挂载点（core+extra）
4. skillctl doctor              ← 校验完整性，全绿才结束
```

**project skill 的额外步骤：**

```
5. skillctl mount <项目>        ← 把 tier:project 的 skill 挂至项目各 git 根 .claude/skills + .agents/skills
6. skillctl unmount <项目>      ← 清除项目挂载（双发现目录，受管软链只清自己的）
```

**禁止：**
- 直接编辑挂载点（`~/.claude/skills/`、`~/.codex/skills/`）下的受管软链或文件
- 跳过 `doctor` 步骤提交变更
- 未经 `sync` 就在挂载点手动创建软链

---

*本规范依据 spec §5（`2026-06-18-aipalace治理与设计哲学-design.md`）成文。*
