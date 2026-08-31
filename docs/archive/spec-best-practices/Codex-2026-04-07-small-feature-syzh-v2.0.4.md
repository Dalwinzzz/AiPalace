---
generated: 2026-04-07
source_materials: text+screenshots+codebase
workspace: "/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity"
skill_version: req-to-ai-spec v1
---

# SYZH：营养厨房迭代三期 - 下级机构数据权限与 App 活动时间排序

## 概述

当前杭州营养厨房相关链路已经完成前两轮改造，但产品测试后发现管理端下级机构菜单的数据权限方向仍然错误，App 端活动筛选也缺少“时间由近及远”的排序能力。  
本次迭代需要修正 `/courseOffline/list` 在 `isSub=true` 场景下的部门数据范围，并为 `/app/courseOffline/getList` 补充时间排序。  
目标是在不破坏前两版 `courseType=4` 营养厨房改造结果的前提下，补齐列表查询的可用性与口径准确性。

## 术语表

| 术语 | 含义 |
|------|------|
| 下级机构菜单请求 | 管理端调用 `/courseOffline/list` 且请求参数 `isSub=true` 的场景，表示从“下级机构”业务菜单进入的活动列表 |
| 当前部门树 | 当前登录部门自身，以及所有下级部门构成的部门范围 |
| 时间由近及远 | App 活动列表按现有 `runningState` 所表达的业务时间语义排序，优先返回时间上更接近当前可参与状态的活动，再返回更远的活动 |

## 全局约束

- 本次迭代只修正列表查询链路，不调整营养厨房前两版已经落地的 `courseType=4` 配置分流、预约限制、签到配置和多课型查询能力。
- 不新增数据库表和字段，不修改现有接口路径。
- 管理端与 App 端返回结构保持不变，仅修改数据过滤和排序逻辑。
- 代码改动必须同时覆盖 MySQL 和 Kingbase 两套 `CourseOfflineDao.xml` 的同名查询分支。

## Task 1: 修正下级机构菜单的数据权限方向

**目标**：让 `/courseOffline/list` 在 `isSub=true` 时返回“当前登录部门及其下级部门”的活动数据，而不是混入上级部门数据。

**前置条件**：
- 管理端活动列表入口是 `CourseOfflineController#getCourseOfflineList`。
- 业务查询主链是 `CourseOfflineService#getList(QueryCourseOfflineListVO)`。
- 实际 SQL 位于 `CourseOfflineDao#getCourseOfflineList`，并在 `CourseOfflineDao.xml` 中同时存在 MySQL 与 Kingbase 两套实现。
- 当前 `CourseOfflineService#getList` 带有 `@DataScope(deptAlias = "c")`，Mapper 内还存在 `dto.isSub` 的额外 where 片段。

**核心规则**：
1. 仅当请求参数 `isSub=true` 时，才进入本次新的“下级机构菜单”数据权限逻辑；`isSub=false` 或 `isSub=null` 时继续保持现有查询行为。
2. `isSub=true` 时，活动列表的部门范围必须定义为“当前登录部门自身 + 当前登录部门所有下级部门”。
3. `isSub=true` 时，结果中不得包含当前登录部门的任何上级部门数据，也不得包含与当前部门无上下级关系的平级部门数据。
4. 当前 SQL 中 `isSub=true` 分支的 `and c.dept_id != #{dto.deptId}` 不能继续作为最终过滤条件，因为它会把当前部门自身活动排除掉，且无法限制到下级部门树。
5. 如果现有 `@DataScope` 注入条件本身已经满足“当前登录部门及下级部门”的口径，则 `isSub=true` 的修正应优先复用 `@DataScope` 注入结果，不重复构造一套作用相同的 SQL 条件。
6. 若评估后仍需显式补充部门树条件，则该条件必须与现有数据权限条件做交集，不能绕开 `@DataScope` 单独放宽数据范围。
7. 若使用 `sys_dept.ancestors` 实现部门树过滤，需要先确认其与业务口径一致；若一致，可使用“`c.dept_id = 当前部门` 或 当前部门出现在活动所属部门的 `ancestors` 中”的方式补足，但不得与 `@DataScope` 形成重复定义的等价条件。
8. 部门范围修正需要同时适配 MySQL 和 Kingbase 两套 `getCourseOfflineList` SQL 分支，保证两个数据库方言下口径一致。
9. 本次修正只改变部门范围，不改变 `/courseOffline/list` 现有的其他过滤规则，包括 `courseType` 精确匹配、`courseName`、`ownerName`、`audit`、`state`、`streetCode`、`areaCode` 等条件。
10. 返回结果中的 `deptName` 仍然表示活动实际发布单位，不因下级机构菜单筛选而替换成当前登录部门名称。
11. 当当前部门没有任何下级部门时，`isSub=true` 仍应允许返回当前部门自身创建的活动数据，因为需求口径明确包含“当前登录部门及下级部门”。
12. 如果当前登录部门及其下级部门都没有命中数据，应返回空列表，不报错。

**边界与异常**：
- `QueryCourseOfflineListVO.deptId` 继续沿用现有登录态回填逻辑，不要求前端额外传递子部门 id 列表。
- 杭州项目下 `/courseOffline/list` 还会回填 `courseFrom`、质量评分权限等扩展字段，这些后处理逻辑不应受到本次部门范围修正影响。
- 所有复用 `getCourseOfflineList` 且带 `isSub` 语义的管理端入口，都需要共享本次修正后的数据范围逻辑，避免出现列表、分页、导出等结果不一致。

**验收标准**：
- [ ] 当 `/courseOffline/list` 传 `isSub=true` 时，返回数据只包含当前登录部门和其下级部门创建的活动。
- [ ] 当 `/courseOffline/list` 传 `isSub=true` 时，不再出现当前登录部门上级部门创建的活动。
- [ ] 当当前登录部门自身有活动数据时，`isSub=true` 查询结果中仍然能看到这些数据。
- [ ] 当 `/courseOffline/list` 传 `isSub=false` 或不传 `isSub` 时，现有管理端活动列表行为不发生回归。
- [ ] MySQL 与 Kingbase 环境下 `isSub=true` 的数据范围表现一致。

**依赖**：无

## Task 2: 为 App 活动列表增加“时间由近及远”排序

**目标**：让 `/app/courseOffline/getList` 支持按时间由近及远排序，并与现有距离排序并存。

**前置条件**：
- App 活动列表入口是 `AppCourseOfflineController#getList(@RequestBody QueryH5CourseOfflineListDTO dto)`。
- 服务层查询入口是 `CourseOfflineService#getH5CourseOfflineList(dto)`，底层 SQL 是 `CourseOfflineDao#getH5CourseOfflineList`。
- 当前控制器会在查询后计算距离，并在内存中按距离重新排序，再通过 `getPageList(list, dto)` 返回分页结果。
- `QueryH5CourseOfflineListDTO` 当前已有 `orderType` 字段，但现有实现仅用于距离排序方向控制。

**核心规则**：
1. `/app/courseOffline/getList` 需要新增“时间由近及远”的排序能力，并与现有“距离由近及远”排序形成二选一关系。
2. App 列表排序结果必须在最终分页返回前确定，不能出现分页后再局部重排导致跨页顺序错误。
3. 本次继续复用现有请求字段 `orderType` 承载排序方式，不新增新的后端请求字段。
4. `orderType` 当前已有语义必须保持不变：
   - `orderType` 为空：保持当前默认排序行为
   - `orderType=1`：继续保持现有升序逻辑
   - `orderType=2`：继续保持现有降序逻辑
5. 本次“时间由近及远”需要在现有 `orderType` 语义基础上向后追加新的类型值，不能覆盖或改变 `null/1/2` 的既有含义。
6. “时间由近及远”排序必须参考现有 SQL 中 `runningState` 的业务时间语义实现，而不是简单改成按 `startTime` 绝对时间排序。
7. 当选择“时间由近及远”时，不能再叠加现有距离排序逻辑；最终顺序必须只由时间相关排序决定。
8. 当仍然选择距离排序时，保持当前距离计算、空距离值处理和前端既有交互语义不变，避免影响已有客户端。
9. `courseType`、`type`、`areaCode`、`ageList`、`deptType`、`notEnd` 等现有筛选条件保持不变，新增排序不能改变筛选结果集本身。
10. 活动列表返回对象 `CourseOfflineHotListVO` 不新增字段，继续复用现有 `runningState`、`startTime`、`distance` 等字段支撑前端展示与排序。
11. 若多个活动在时间排序主键上相同，则必须保持它们在原始结果集中的相对顺序，避免列表顺序不稳定跳动。
12. 若前端传入未知 `orderType` 值，后台应回退到当前默认排序行为，不报错。[推断]
13. 如果后续选择把时间排序下推到 SQL 层，必须同步保证控制器层不再执行与之冲突的第二次排序，避免最终返回顺序与 SQL 结果不一致。

**边界与异常**：
- 当请求中没有经纬度或某条活动无法计算距离时，时间排序仍应正常工作，因为它不依赖 `distance` 字段。
- 当筛选条件已经把结果集限制为空时，排序逻辑应直接返回空列表，不做额外处理。

**验收标准**：
- [ ] `/app/courseOffline/getList` 支持返回“时间由近及远”排序后的活动列表。
- [ ] 当选择时间排序时，返回列表顺序符合现有 `runningState` 所表达的业务时间先后语义。
- [ ] 当不选择时间排序时，现有“距离由近及远”排序行为保持不变。
- [ ] 同一组筛选条件下，切换“距离由近及远”和“时间由近及远”后，结果集内容相同，仅顺序不同。
- [ ] 分页后的每一页顺序与所选排序方式一致，不出现翻页后顺序错乱。

**依赖**：无
