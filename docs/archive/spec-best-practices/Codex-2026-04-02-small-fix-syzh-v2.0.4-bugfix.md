---
generated: 2026-04-02
source_materials: text+screenshots+codebase
workspace: "/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity"
skill_version: req-to-ai-spec v1
---

# SYZH：按 `courseType` 区分活动配置与 App 多课型预约查询

## 概述

当前杭州活动链路已经在 `course_offline` 上接入 `courseType=4` 的营养厨房，但“签到时间设置”和“养育活动预约限制”两组配置仍然只有一份全局数据，`/app/courseOffline/appoint/list` 也只支持单个 `courseType` 过滤。  
本次需求要把这三条链路补齐为按 `courseType` 分流：后台配置保存和读取都要按业务点返回对应配置，App 预约记录列表支持一次查询多个课型。  
实现目标是在继续复用现有 `course_offline` 活动链路的前提下，让养育照护活动与营养厨房能够拥有独立配置和独立数据过滤口径，同时保持老前端不传新参数时行为不变。

## 术语表

| 术语 | 含义 |
|------|------|
| 业务点标识 | 本次确认复用 `courseType` 作为业务点标识；养育照护活动=`1`，营养厨房=`4` |
| 默认项目名 | 当前运行项目原本使用的 `projectName`，用于现有养育活动配置 |
| 厨房配置项目名 | 仅当 `courseType=4` 时使用硬编码 `projectName="cook"`，用于读写营养厨房签到时间配置 |
| 签到时间配置 | `/courseOffline/editSignTimeDeadline` 与 `/courseOffline/getSignTimeDeadline` 对应的活动结束后可签到时间配置 |
| 预约限制配置 | `/courseOffline/appointLimit/save` 与 `/courseOffline/appointLimit/detail` 对应的预约限制配置 |
| 多课型过滤 | `/app/courseOffline/appoint/list` 允许前端传入多个 `courseType` 共同过滤预约记录 |

## 全局约束

- 本次业务点分流统一复用 `courseType`，不新增独立 `bizPoint`、`configType` 参数。
- 配置接口必须做兼容改造：前端不传 `courseType` 时，保持当前业务行为不变；前端传入时，再按本次需求执行额外分流逻辑。
- 签到时间配置不新增数据库字段，不调整 `course_offline_sign_time_conf` 表结构。
- `courseType=4` 的签到时间配置通过硬编码 `projectName="cook"` 与原养育活动配置隔离；其余场景继续使用当前项目原本的 `projectName`。
- 预约限制配置继续存 Redis，不需要数据库变更；本次按 `courseType` 分 key 存储。
- 杭州项目是主生效场景；非杭州项目继续兼容原有单配置/单课型逻辑，除非现有代码已天然兼容多值输入。[推断]
- 保持现有返回结构风格，优先做向后兼容扩展，避免前端未改动场景被破坏。

## 实现顺序

1. **Task 1** -- 先定义按 `courseType` 分流的配置读写规则，后续运行时签到/预约限制才能读取到正确配置。
2. **Task 2** -- 再改配置消费链路，让保存下来的分课型配置真正参与签到和预约限制判断。
3. **Task 3** -- 最后扩展 App 预约记录列表为多课型过滤，避免与配置链路耦合修改互相干扰。

## Task 1: 扩展按 `courseType` 分流的配置读写接口

**目标**：让签到时间设置和预约限制配置都能按 `courseType` 保存和读取各自业务点的数据。

**前置条件**：
- `CourseOfflineController` 当前已有：
    - `POST /courseOffline/editSignTimeDeadline`
    - `POST /courseOffline/getSignTimeDeadline`
    - `POST /courseOffline/appointLimit/save`
    - `GET /courseOffline/appointLimit/detail`
- 当前签到时间配置持久化在 `course_offline_sign_time_conf`，仅按 `project_name` 取一条。
- 当前预约限制配置存于 Redis，key 为 `course:offline:appoint:limit2`，仅一份全局配置。

**核心规则**：
1. `POST /courseOffline/editSignTimeDeadline` 入参新增可选字段 `courseType`。
2. `POST /courseOffline/getSignTimeDeadline` 新增可选参数 `courseType`。
3. `POST /courseOffline/appointLimit/save` 入参新增可选字段 `courseType`。
4. `GET /courseOffline/appointLimit/detail` 新增可选参数 `courseType`。
5. 当前端不传 `courseType` 时，四个接口都保持现有逻辑不变：
    - 签到时间配置继续使用当前项目原本的 `projectName`
    - 预约限制配置继续使用当前默认 Redis key
6. 当前端传入 `courseType=4` 时，签到时间配置读写统一改用硬编码 `projectName="cook"`。
7. 当前端传入 `courseType=4` 时，预约限制配置读写统一改用营养厨房独立 Redis key。
8. 当前端传入其他 `courseType` 值时，不做强校验，不报错，继续兼容走当前默认业务行为：
    - 签到时间配置仍使用当前项目原本 `projectName`
    - 预约限制配置仍使用当前默认 Redis key
9. 历史养育活动配置无需迁移，继续存放在原 `projectName` / 原 Redis key 下。
10. 营养厨房首次配置时，如果 `project_name="cook"` 对应签到时间记录不存在，则新增；存在则更新。
11. 对于未配置过的业务点，读取接口仍返回 DTO 结构，但字段值为空或默认空配置，不报错。

**边界与异常**：
- 老前端完全不传 `courseType` 时，页面行为、接口行为、存储位置都必须与当前版本一致。
- 仅当明确传入 `courseType=4` 时，才进入营养厨房业务点分流。
- `project_name="cook"` 仅作为营养厨房配置隔离键使用，不代表真实系统项目切换。[推断]

**验收标准**：
- [ ] 老前端不传 `courseType` 时，签到时间配置与预约限制配置行为与当前版本一致。
- [ ] 前端传 `courseType=4` 保存签到时间配置后，读取命中 `project_name="cook"` 对应数据。
- [ ] 前端传 `courseType=4` 保存预约限制配置后，读取命中营养厨房独立 Redis key。
- [ ] 营养厨房配置不会覆盖默认养育活动配置，反之亦然。

**依赖**：无

## Task 2: 让签到与预约限制实际按 `courseType` 生效

**目标**：让新保存的分课型配置真正影响签到校验和预约限制校验，而不是只改后台读写接口。

**前置条件**：
- Task 1 已完成，配置接口与存储能够按 `courseType` 正确读写。
- 当前运行时消费点包括：
    - `CourseOfflineService.canSign`
    - `CourseOfflineService.sign` 内部签到校验
    - `CourseOfflineAppointService.checkSignStatus`
    - `CourseOfflineService.appoint`
    - `CourseOfflineAppointService.judgeIsLimitAppoint`

**核心规则**：
1. 所有签到时间配置消费点都必须改为根据当前活动的 `courseType` 读取对应配置。
2. 运行时读取签到时间配置时，映射规则与 Task 1 完全一致：
    - `courseType=4` -> `projectName="cook"`
    - 其余情况 -> 当前项目原本 `projectName`
3. `canSign(courseId, signType)` 在查询到活动后，必须按该活动的 `courseType` 取签到时间配置。
4. 人工录入签到、未预约签到等路径，只要最终进入 `checkSignStatus`，都必须使用活动自身 `courseType` 对应的签到截止配置。
5. 预约限制校验必须从“按儿童证件号 + 单全局配置”升级为“按活动 `courseType` + 儿童证件号 + 对应配置”执行。
6. `CourseOfflineService.appoint` 在拿到 `courseOffline` 后，必须把 `courseOffline.getCourseType()` 传入预约限制校验。
7. `courseType=4` 的预约限制只读取营养厨房独立 Redis 配置；其余场景继续读取默认 Redis 配置。
8. 不在本次业务点范围内的其他课型继续沿用现有逻辑，不能被新的活动配置误伤。[推断]
9. 如果某个业务点没有配置限制数据或配置未开启限制，运行时校验应降级为“不限制”，与当前空配置行为一致。
10. 如果某个业务点没有配置签到时间，运行时校验应降级为当前“无限制可签到”的行为。

**边界与异常**：
- `judgeIsLimitAppoint` 当前仅传 `idCard`，本次需要扩展签名以接收 `courseType`；所有调用方必须同步更新。
- `checkSignStatus` 当前接收的是配置 DTO，本次不强制改静态方法签名，但调用前必须保证传入的是该活动 `courseType` 对应的 DTO。
- 如果活动记录本身 `courseType` 为空，应按默认业务点处理，继续走当前默认配置。[推断]

**验收标准**：
- [ ] 当默认业务点和 `courseType=4` 配置了不同签到截止时间时，两类活动在相同时间点的 `canSign` 结果可不同。
- [ ] 当默认业务点和 `courseType=4` 配置了不同预约限制时，同一儿童预约两类活动时命中的限制规则可不同。
- [ ] 营养厨房签到校验读取 `project_name="cook"` 配置，不读取默认项目配置。
- [ ] 未配置业务点时，运行时行为与当前空配置表现一致，不抛空指针或配置缺失异常。

**依赖**：Task 1

## Task 3: 扩展 `/app/courseOffline/appoint/list` 为多 `courseType` 过滤

**目标**：让 App 预约记录列表支持一次查询多个 `courseType`，替代当前单选过滤。

**前置条件**：
- 当前接口为 `GET /app/courseOffline/appoint/list`
- 当前 controller 只接收单个 `Integer courseType`
- 当前 service `CourseOfflineAppointService.getMyAppointRecord(...)` 和 DAO `CourseOfflineDao.getMyAppointRecord(...)` 也只支持单值过滤
- 当前 SQL 条件是 `and co.course_type = #{courseType}`

**核心规则**：
1. `/app/courseOffline/appoint/list` 改为支持多个 `courseType` 过滤，接口参数使用 `courseTypes` 集合。
2. 为保持兼容，接口应同时兼容旧的单值 `courseType` 和新的多值 `courseTypes`：
    - 前端传 `courseTypes` 时，按多值过滤
    - 只传旧 `courseType` 时，兼容为单元素集合
3. 当前 controller 中“未传则默认 `courseType=1`”的逻辑，需要升级为“未传任何课型参数则默认 `[1]`”。
4. service 方法签名应同步升级为支持 `List<Integer> courseTypes`，不再只接受单个 `Integer courseType`。
5. DAO/Mapper SQL 应改为：
    - 有多值时使用 `IN (...)`
    - 只有单值兼容参数时也统一走 `IN` 或单值条件，保持语义一致
6. 查询结果排序规则保持不变，仍按 `coa.create_time desc` 返回，避免前端列表顺序回归。
7. 结果集中的每条预约记录原有字段结构不变，不新增前端必填返回字段。
8. 远程引用补充、课程来源回填等后处理逻辑保持现状，仅改变过滤条件。
9. 该接口的多课型过滤必须允许至少同时查询 `1` 和 `4`，满足养育活动与营养厨房联合筛选。

**边界与异常**：
- 如果前端同时传了 `courseType` 和 `courseTypes`，以后者 `courseTypes` 为准。[推断]
- 如果 `courseTypes` 为空数组，应按“未传”处理，默认 `[1]`。
- 如果 `courseTypes` 中出现其他课型值，按传入值参与查询，不做新增强校验；最终结果由数据库过滤自然决定。

**验收标准**：
- [ ] 只传旧参数 `courseType=1` 时，接口结果与当前行为一致。
- [ ] 传 `courseTypes=1,4` 时，接口能同时返回养育活动和营养厨房预约记录。
- [ ] 不传任何课型参数时，默认仍只查 `courseType=1`。
- [ ] 返回列表排序与当前版本一致，不因改成多值过滤发生顺序变化。

**依赖**：无

## 重要接口与类型变更

- `POST /courseOffline/editSignTimeDeadline`
    - 请求体新增可选 `courseType`
- `POST /courseOffline/getSignTimeDeadline`
    - 新增可选请求参数 `courseType`
- `POST /courseOffline/appointLimit/save`
    - 请求体新增可选 `courseType`
- `GET /courseOffline/appointLimit/detail`
    - 新增可选请求参数 `courseType`
- `GET /app/courseOffline/appoint/list`
    - 保留兼容参数 `courseType`，支持传入int数组多选过滤
- `EditSignTimeDeadlineDto`
    - 新增可选 `courseType`
- `CourseOfflineAppointLimitDTO`
    - 新增可选 `courseType`
- `CourseOfflineAppointService.getMyAppointRecord(...)`
    - `courseType` 升级为 `courseTypes`
- `CourseOfflineDao.getMyAppointRecord(...)`
    - SQL 从单值等于过滤升级为多值 `IN` 过滤
- 不新增 `course_offline_sign_time_conf` 表字段；签到时间配置通过 `project_name` 映射实现业务点隔离

## 测试方案

- 配置读写
    - 不传 `courseType` 时，签到时间配置与预约限制配置行为与当前版本一致
    - `courseType=4` 时，签到时间配置命中 `project_name="cook"`
    - `courseType=4` 时，预约限制配置命中独立 Redis key
    - 默认业务点与营养厨房配置互不覆盖
- 运行时生效
    - 默认业务点与 `courseType=4` 配置不同签到时间时，`canSign` 和签到校验结果按业务点分流
    - 默认业务点与 `courseType=4` 配置不同预约限制时，预约限制命中结果按业务点分流
    - 未配置业务点时行为回退到当前空配置逻辑
- App 查询
    - 单值 `courseType=1` 兼容旧行为
    - 多值 `courseTypes=1,4` 返回联合结果
    - 未传参数默认只查 `1`
    - 排序维持 `create_time desc`
- 回归
    - 义诊、照护课堂等非本次业务点范围课型不被误伤
    - 杭州已有营养厨房表单配置、统计、活动 CRUD 不发生行为回退

## 假设与默认值

- 本次“业务点标识”已确认直接复用 `courseType`，不新增独立枚举。
- `courseType=4` 是唯一需要额外分流的新业务点；其余值默认继续走当前业务行为。
- 对签到时间配置，`courseType=4` 固定映射为硬编码 `projectName="cook"`；其他情况使用当前项目原本 `projectName`。
- 对预约限制配置，默认业务点继续使用现有 Redis key，营养厨房使用独立 key 后缀。
- 若前端未传 `courseType/courseTypes`，后台继续默认按养育照护活动旧逻辑处理。
