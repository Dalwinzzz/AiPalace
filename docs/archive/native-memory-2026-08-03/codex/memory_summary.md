v1

## User Profile

用户维护多套 Java 业务仓库（SunkidCloud、SunKidServer、WaveFlow）和 AiPalace 工作流资产。常见工作是生产只读证据链、双数据库 Liquibase、Apifox 契约、代码审查及经验证的 Git 交付。偏好从真实代码、配置、部署分支和数据收敛结论，要求说明边界与未完成风险。命中 `~/Documents/AI/` 时按个人 AI 工作流资产域处理，先读 `docs/README.md`。[ad-hoc note]

## User preferences

- 先按真实路径、代码、配置与只读结果查证；修复或结论要验证实际症状/远端状态，不能用命令成功输出替代。
- 生产数据默认“代码 cross-check + 线上只读核验 + 可执行 SQL handoff”；agent 不直写生产库。
- 复杂修复先 RCA 与可验证方案，用户确认后编码；明确“直接提交推送”即完成测试、`git diff --check`、远端基线核对后直接非强制 push。
- 提交范围严格服从指示：只暂存请求文件；被 ignore 的指定测试可精确 `git add -f`，不扩大范围。
- 代码审查需批判、风险排序、文件行号、下游契约和边界测试证据；第二轮复审以旧问题为验收基线并重查新风险。
- Apifox SaaS 写入先获确认，确认项目/目录后写入并 `getHttpEndpoint` 回读；必要时再清理本地 MD。
- 现场排查不仅给结论：指定报告要同步写入接口、参数、日志/数据库证据、直接原因、根因分类与正确调用方式。

## General Tips

- Java Maven 常用专用 settings/repository：`mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository ...`；WaveFlow 验证另需 JDK 8。
- 涉及生产 schema 字段时先查实际表结构；SQL 类型不兼容时拆成 `SELECT`/`EXISTS`，不要以脱敏异常输出推断业务。
- 双数据库 Liquibase 先从模块 `master.xml` 定根；SQL 与 changelog 精确暂存，path-scoped `git diff --check` 避开无关脏改。
- Apifox 同名目录先 `getStructureInfo`；JSON/form-data 示例使用字符串化 JSON，创建或更新后必回读。
- 命中 AiPalace heartbeat / `upstream_sync.py` 先读 `skills/aipalace-upstream-sync/SKILL.md`。

## What's in Memory

### /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcnursery/skc-nursery

#### 2026-07-31

- 善于在杭托育券“无权查询/出生日期为空”: getInfantOwnInfo, infantIdCard, guardianIdCard, dr-family-cache, user_child, dbq
  - desc: 排查家庭关系空缓存误判与前端儿童证件号错传，并更新指定报告。
  - learnings: `cacheHit=true, result=[]` 不等于真实无权；先只读核验关系，清缓存重试并区分错传 `infantIdCard`。

### /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcadminframework

#### 2026-07-30

- skc-system 双数据库 Liquibase 与 develop 交付: physical_lab_report, changelog-202607.xml, MySQL, Kingbase, 2e7d9025
  - desc: `skc-modules/skc-system` 的双库建表、严格暂存、Maven 验证与推送。
  - learnings: `master.xml` 在模块内；只提交指定 SQL/changelog，未确认 backfill 不入 migration。

### /Users/dalwin/Library/IdeaProject/WaveFlow/wavetrans

#### 2026-07-30

- 嘉善检验报告同步二轮代码审查: d82aafec, JiaShanLabReportSyncService, candidate-days:30, filterRowsOwnedByCandidate, 不可合入
  - desc: `2d0e722` 与修复提交的跨 MySQL/Oracle/Kafka review，含原始风险和二轮遗留问题。
  - learnings: 空 `deptIds` fail-open 已关闭，但报告归属候选集不稳定、30 天迟到漏数、重复投递和测试缺口仍使修复不可合入。

### /Users/dalwin/Library/IdeaProject/ZhiJin/SunKidServer

#### 2026-07-28

- 高德公网直连与信创活动二维码路由: GaoDeServiceImpl, qrcode_register_url, sknurseryserver-prod, Nacos
  - desc: shared basic 高德实现与二维码实际配置生产者定位。
  - learnings: 先追 `@Value` 消费者到真实 Data ID；改 shared basic 后先 install 再编译调用端。

### Older Memory Topics

#### /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity

- 南京预约 `peType` 隔离与直录 Apifox: appointTimeId, physical_examination.type, PeResultDirectSaveVO, 475638055
  - desc: cwd=skcactivity；旧 `physicalexamination` 按预约配置类型隔离，含 Apifox 契约和 develop 推送。
- `physical-exam` dept_id 与医院配置: HospitalController, orgDeptId, Apifox
  - desc: cwd=skcactivity；新模块服务端权限锚点与医院接口。
- 南京从业人员体检导入同步: getStructureInfo, form-data, 488219523
  - desc: cwd=skcactivity；Apifox 目录确认、回读和本地 MD 删除。

#### /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skciotdevice

- 量子床垫离床零生命体征告警互斥: QuantumRealtimeRecordProcessorImpl, warnValue=0, 0a7ad078
  - desc: cwd=skciotdevice；双 0 仅跳过生命体征告警，保留离床告警与定向/全量回归。

#### /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcdatasum

- 南京建邺动态指标事务隔离: TransactionTemplate, PROPAGATION_REQUIRES_NEW, query timeout
  - desc: cwd=skcdatasum；按 key 独立事务，失败继续后续指标。

#### /Users/dalwin/Library/CodeRepo/AI

- AiPalace 上游定时同步: upstream_sync.py, heartbeat, EXCLUDED_TARGETS, skill-management
  - desc: cwd=/Users/dalwin/Library/CodeRepo/AI；硬拷贝同步、仓库日志和本地例外保护。

#### /Users/dalwin/.codex/worktrees/6308/skcnursery/skc-nursery

- 鄂尔多斯总托位为 0: NurseryClassDisplaySupport, 111824, Kingbase
  - desc: cwd=该 worktree；只读核验后生成 guarded backfill SQL。

#### /Users/dalwin/Library/IdeaProject/ZhiJin/gongshu/gsskservers

- 已删除 course_offline 残留预约: course_offline_appointment, SELECT FOR UPDATE
  - desc: cwd=gsskservers；生产修复 SQL 的预检、执行、复核边界。

#### /Users/dalwin/.codex/worktrees/36a8/skcactivity

- courseOffline 复制活动年龄异常: 63761, ageString, alterPosterImg
  - desc: cwd=该 worktree；develop 隔离工作树与前端复制状态/海报组装证据链。

#### /Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcinfant

- 儿童体检详情码值转换: ExamCodeDict, ChildHealthPortraitServiceImpl, git add -f
  - desc: cwd=skcinfant；多选字典展示与仅提交业务源文件。

#### /Users/dalwin/Library/CodeRepo/AI/Codex-Dream-Skin

- 本机主题、签名与重装备份: Lady Maria, codesign, ditto, SHA256SUMS
  - desc: cwd=Codex-Dream-Skin；不绕过签名，敏感 Codex 数据复制须重新授权。

#### /Users/dalwin/Documents/AI

- 个人 AI 工作流域约定: docs/README.md, archive, knowledge, skill [ad-hoc note]
  - desc: cwd=~/Documents/AI；先读 docs 入口并按工作流资产处理。[ad-hoc note]
