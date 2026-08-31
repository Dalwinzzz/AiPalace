对 worktree `~/.claude/worktrees/skcnursery-minkernel-refactor` 分支 `claude/refactor-机构管理模块/20260706_v1.0.0`（基线 0a783211）的等价性审查已做三轮：

- **首轮**（2026-07-11，HEAD 1d4a4cd20）：修复后可合入，🔴2/🟡6/🟢9；两 🔴 为 layer-1 fcb12b95a 契约破坏。报告 `docs/commit-review/2026-07/11/`。
- **第二轮**（2026-07-16，批次13 核销）：通过可合入，🔴0/🟡0/🟢3。报告 `docs/commit-review/2026-07/16/`。
- **owner 决议（2026-07-16，已落地）**：①新昌 'xc' 请求触发退役（2f5b3452a，批次14，一律以后端 nacos project.name 为准）；②D11 裁定 staff 域范围外留档（移交材料 `docs/spec-architect/2026-07/16/d11-...`）；③squash 待全部问题完成后 owner 发令。
- **第三轮**（2026-07-21，tip=旁支 `merge/nursery-domain-catchup` @ 49e17af98，区间 62dea5706..49e17af98，17 提交）：**修复后可合入，🔴2/🟡3/🟢3**。含实体瘦身（8b3df10a0：Nursery 804→564 行 DDL 对齐+继承式 NurseryWithExtraDTO/NurseryDetailFormVO 承接，T1 核对反射/契约面无损）+ 11 项 develop 主线业务迭代 replay（T2 核对 10 项忠实、含越权/双库/南京园长普惠/南京备案 4 高危通过）。报告 `docs/commit-review/2026-07/21/62dea5706..49e17af98-round3-review.md`。
  - **首次查出真实功能回归**（非契约/文档）：`d74bb6da6` 鄂尔多斯办托单位名称/是否试点，对 develop `e9bcd6776` 不完整 replay——🔴① NurseryAttributeServiceImpl:130-140 裸对象喂 saveExtraInfo，老机构常态下 careUnitName/nurseryPilot 不落库 + 非选择性 updateByPrimaryKey 清空 isShutDown/kindergarten/cheapDetailType 等既有列（数据损坏）；🔴② 整条鄂尔多斯审核链（applyEerduosiChangedFields 标红/回显/回写/normalize 归一）遗漏，审核 DTO 承接字段悬挂。主审已逐行独立复核证实。
  - 🟡：审核变更比对面收窄丢 districtName 检出（实体瘦身副作用，待 owner 定 districtName 是否审核跟踪字段）；11 项归并零新增测试（@Test 恒 194）+零文档批次登记（漏网成因）。

- **第四轮**（2026-07-22，区间 49e17af98..f516cf8a1，2 提交 171eab70b 修复+f516cf8a1 文档）：**通过可合入，🔴0/🟡0/🟢3**。第三轮 2 个 🔴 已对齐 develop e9bcd6776 忠实补齐——主审逐行独立追踪确认修法与 develop:3046-3078 逐块一致（同门控 isShutDown!=null/同载体/同 mergeEerduosiAttributeInfo/saveExtraInfo 补鄂尔多斯合并支），且超范围补了表单必填校验/详情顶层回显/区级直存；新增 11 例真断言回归护栏（ArgumentCaptor 捕获、断言不清列），本机实跑 96/0/0（鄂 5+6 新测全绿），全仓 209/0/0。🟡 districtName 裁定成立（districtCode 派生名、比对面已覆盖）、批次16 文档补登。报告 `docs/commit-review/2026-07/22/`。
- **develop 直接 merge 难点分析（2026-07-22）**：分支 vs origin/develop = 落后 204 / 领先 39，merge-base=ac470af27（老）。develop 198 个提交动过 skc-nursery、其中 68 个动老 god 类 `service/NurseryService.java`（develop 上已长到 4284 行，本分支已删该文件）→ modify/delete 冲突不可自动解。分支重构面 5111 文件 vs develop 前进面 423 文件。**结论：不宜直接 git merge**；分支只 replay 了 11 项机构管理 REQ、develop 其余 ~184 个 nursery 子域(child/staff/sign 等)迭代未跟进，本质是"月龄快照重构 vs 前进主干"。正解是把重构 rebase/重演到当前 develop 的 nursery 上,或走 refactor/min-kernel 集成分支协调大爆炸落地(分支既定终点本就是 squash 到 origin/refactor/min-kernel,非直连 develop)。

**Why:** 四轮审查全部核销,分支现为净等价+11项主线归并已带,可合入;唯 develop 直接 merge 是硬骨头(月龄重构撞 68 次老god类改动)。
**How to apply:** 被问分支状态答"四轮审查通过、鄂尔多斯回归已修复核销、通过可合入";被问 develop 合并答"不宜直接 merge,应 rebase 重构到当前 develop 或走 refactor/min-kernel 协调"。残留技术债:其余10项replay的develop专项测未迁移(归并即带测,后续批次)。相关：[[urgent-piece-cherrypick-to-develop]]
