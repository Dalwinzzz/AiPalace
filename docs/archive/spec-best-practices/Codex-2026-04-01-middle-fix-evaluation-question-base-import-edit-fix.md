# Spec: 考核题库导入与编辑缺陷修复

## Summary
- 目标工具: Codex
- 变更类型: Bug 修复
- 仓库: `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity`
- 扫描级别: 重度
- Spec 落盘路径: `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity/docs/spec-evaluation-question-base-import-edit-fix.md`
- 备注: Spec 已落盘到仓库 `docs/` 目录
- 当前状态: 方案已确认，已进入实现与验证阶段

本次修复覆盖两个入口：
- `POST /evaluation/importEvaluationQuestionBaseQuestion`
- `POST /evaluation/editEvaluationQuestionBase`

本次必须一起解决四类问题：
- 导入时选项/答案字符串解析脆弱，导致报错、空白选项、误判答案
- 导入与编辑都把“重复题”错误定义为 `type + title`
- 导入时题目与选项 `serialNumber` 写错，详情回填顺序也不稳定
- 导入完成后 `question_num` 口径可能失真

## 1. 业务规则与边界

### 1.1 已确认业务规则
- 同题干但选项不同: 允许共存
- 同题干、同选项、同答案、同分值: 视为同题，导入时替换旧题
- 同题干、同选项，但答案或分值不同: 也视为同题更新版本，导入时替换旧题
- 选项顺序不同: 视为不同题目
- 同一批 Excel 内如果出现相同题目键两次: 视为模板内重复，按失败行处理，不在单次导入内自动覆盖

### 1.2 范围内
- 修复导入接口的选项解析、答案解析、重复题判定、替换逻辑、数量更新
- 修复编辑接口的重复题判定
- 校验并补齐详情回填链路，保证导入后编辑页回显稳定
- 保持接口协议、返回结构、数据库表结构不变

### 1.3 范围外
- 不新增填空题导入
- 不改 controller 路径和请求字段
- 不扩展到发布、答题、统计模块

## 2. 勘察结论

### 2.1 已确认的关键文件
| 类型 | 路径 | 当前职责 | 本次动作 |
|------|------|----------|----------|
| `controller` | [AdminEvaluationController.java](/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity/skc-activity/src/main/java/com/iktapp/skc/activity/controller/AdminEvaluationController.java) | 导入/编辑入口 | 不改协议，只作为回归入口 |
| `service` | [EvaluationServiceImpl.java](/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity/skc-evaluation/src/main/java/com/iktapp/skc/evaluation/service/impl/EvaluationServiceImpl.java) | 导入、编辑、详情回填、题库存储 | 核心修复点 |
| `dto` | [EvaluationQuestionBaseExcel.java](/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity/skc-evaluation/src/main/java/com/iktapp/skc/evaluation/pojo/EvaluationQuestionBaseExcel.java) | Excel 行对象 | 逐行失败结果回写 |
| `dto` | [SaveEvaluationQuestionBaseDTO.java](/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity/skc-evaluation/src/main/java/com/iktapp/skc/evaluation/pojo/SaveEvaluationQuestionBaseDTO.java) | 编辑保存 DTO | 重复判定入口 |
| `dao xml` | [EvaluationDao.xml](/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity/skc-evaluation/src/main/resources/mapper/evaluation/EvaluationDao.xml) | 完整性校验、题库列表 | 回归校验关键下游 |

### 2.2 已确认的业务表
| 表 | 关键字段 | 当前用途 | 本次动作 |
|----|----------|----------|----------|
| `evaluation_question_base` | `id`, `question_base_name`, `question_num` | 题库主表 | 修正导入后数量口径 |
| `evaluation_question_base_question` | `id`, `question_base_id`, `serial_number`, `type`, `title` | 题目主表 | 重定义唯一性与题目序号 |
| `evaluation_question_base_question_option` | `id`, `question_id`, `serial_number`, `title` | 选项表 | 修复解析与序号 |
| `evaluation_question_base_question_answer` | `id`, `question_id`, `option_id`, `score` | 答案/分值表 | 配合同题覆盖语义重建 |

### 2.3 已确认的高风险链路
| 场景 | 关键调用链 | 风险点 |
|------|------------|--------|
| 导入 | controller -> `importEvaluationQuestionBaseQuestion` -> 三表写入 -> 更新 `question_num` | 解析脆弱、重复定义错误、数量失真 |
| 编辑 | `editEvaluationQuestion` -> `checkSaveEvaluationQuestionBaseDTO` -> 逻删旧题 -> `saveEvaluationQuestionBaseQuestion` | 重复判定错误、重建副作用 |
| 回填 | `getEvaluationQuestionBaseDetail` -> question/option/answer 查询 -> DTO 组装 | 顺序不稳定 |
| 完整性校验 | `judgeQuestionContentIntegrity(baseId)` | 选择题必须有 option，计分题必须有 answer |

## 3. 统一设计

### 3.1 统一“题目键”定义
导入和编辑共用同一套题目键：
- `questionKey = type + normalizedTitle + orderedNormalizedOptionList`

规则：
- `normalizedTitle`: `trim`，压缩多余空白
- `orderedNormalizedOptionList`: 必须包含选项顺序、选项标记、标准化后的选项正文
- 不把答案和分值放进“是否同题”的判断键中
- 但答案和分值参与“覆盖旧题”的新数据写入

### 3.2 选项字符串解析增强
替代当前 `split(",\\n")` 和 `split(" ")[1]` 的实现，采用“先标准化，再按行首标签切块”的解析器。

#### 输入标准化
对原始 `option` 字符串先做：
- `\r\n`、`\r` 统一成 `\n`
- `\t`、全角空格、NBSP 统一成普通空格
- 去掉整串首尾空白
- 压缩连续空白行
- 不对正文中的中英文逗号做全局替换，避免破坏文本

#### 选项边界识别
只识别以下位置的标签：
- 字符串开头
- 换行后的行首

支持的标签形式：
- `A内容`
- `A 内容`
- `A    内容`
- `A、内容`
- `A.内容`
- `A：内容`
- `A)内容`
- 同理支持 `B-Z`

约束：
- 只把“行首标签”识别为新选项
- 正文中出现 `维生素D`、`G-6-PD`、`DNA`、`ABCD` 等文本时，不能触发切分

#### 选项正文标准化
对每个选项块：
- 去掉标签与标签后连接符
- 去掉正文首尾空白
- 保留正文中的合法中英文标点、数字、连字符
- 比较键中忽略尾部模板性分隔符影响，如结尾 `,` / `，` / `；` / `;` / `、`
- 落库存储以稳定展示为优先，不做激进正文清洗

### 3.3 答案字符串解析增强
对 `answer` 独立标准化：
- 把 `，`、`、`、`;`、`；` 统一视为分隔符
- 去掉整体与分隔项首尾空白
- 转成大写标签列表
- 单选题答案数必须为 1
- 多选题答案数至少为 1
- 每个答案都必须存在于解析后的选项标签中

### 3.4 导入替换与数量口径
- Excel 内重复判定改为新 `questionKey`
- 题库内旧题匹配改为新 `questionKey`
- 命中旧题时:
  - 新题写入成功后，再逻辑删除旧题
- `question_num` 不再只加 `newQuestionNum`
- 导入完成后按 `evaluation_question_base_question` 当前有效题目数重算并回写

### 3.5 顺序稳定性
- 导入写入：
  - 题目 `serialNumber` 按导入有效题顺序递增
  - 选项 `serialNumber` 按解析后的选项顺序递增
- 详情查询：
  - 题目按 `serial_number asc, id asc`
  - 选项按 `serial_number asc, id asc`

## 4. 覆盖矩阵

### 4.1 接口/入口覆盖矩阵
| 接口 | 当前实现 | 关联表 | 变更动作 | 验证方式 |
|------|----------|--------|----------|----------|
| `POST /evaluation/importEvaluationQuestionBaseQuestion` | `AdminEvaluationController -> EvaluationServiceImpl.importEvaluationQuestionBaseQuestion` | 主表/题目/选项/答案 | 重写解析、重复键、替换逻辑、数量更新 | 两份样本 Excel + 手工构造冲突样本 |
| `POST /evaluation/editEvaluationQuestionBase` | `AdminEvaluationController -> EvaluationServiceImpl.editEvaluationQuestion` | 题目/选项/答案 | 重写 DTO 内重复判定 | 同题干不同选项编辑保存 |
| `GET /evaluation/getEvaluationQuestionBaseDetail` | `EvaluationServiceImpl.getEvaluationQuestionBaseDetail` | 题目/选项/答案 | 不改协议，补排序稳定性 | 导入后打开编辑页回显 |

### 4.2 业务表/字段影响矩阵
| 表/字段 | 读取链路 | 写入链路 | 变更动作 | 风险 |
|---------|----------|----------|----------|------|
| `evaluation_question_base.question_num` | 题库列表 | 导入、编辑 | 导入后准确重算 | 数量展示错误 |
| `evaluation_question_base_question.serial_number` | 详情回填 | 导入、编辑 | 导入时修正 | 题目顺序不稳 |
| `evaluation_question_base_question_option.serial_number` | 详情回填 | 导入、编辑 | 导入时修正 | 选项顺序不稳 |
| `evaluation_question_base_question.title` | 导入/编辑判重 | 导入、编辑 | 不再单独作为唯一性标准 | 同题干不同选项被误杀 |
| `evaluation_question_base_question_option.title` | 详情展示 | 导入、编辑 | 解析增强后完整保留 | 空白选项 |
| `evaluation_question_base_question_answer.score` | 详情回填 | 导入、编辑 | 纳入同题覆盖写入 | 替换语义变化 |

### 4.3 调用链覆盖矩阵
| 入口 | 关键调用链 | 副作用/校验 | 变更点 | 验证方式 |
|------|------------|-------------|--------|----------|
| 导入 | controller -> `importEvaluationQuestionBaseQuestion` -> `getEvaluationQuestionBaseByName` / `getEvaluationQuestionBaseQuestionList` -> 三表插入/逻删 -> 更新 `question_num` | 题型校验、选项校验、答案合法性、同题替换 | 抽出统一标准化与解析私有方法 | 样本导入后查库与前端回显 |
| 编辑 | `editEvaluationQuestion` -> `checkSaveEvaluationQuestionBaseDTO` -> 逻删旧题 -> `saveEvaluationQuestionBaseQuestion` | DTO 内重复校验、完整性校验 | 统一使用 `questionKey` | 编辑保存与详情回填 |
| 回填 | `getEvaluationQuestionBaseDetail` -> `getEvaluationQuestionBaseQuestionList` / `OptionList` / `AnswerList` | 顺序、答案映射 | 补 `orderByClause` | 导入后页面顺序稳定 |

## 5. 实施顺序

### Step 0: 落盘 Spec
- 目标: 在正式编码前把本 spec 写入仓库
- 动作:
  - 新建 `/Users/dalwin/Library/IdeaProject/ZhiJin/SunkidCloud/skcservers/skcactivity/docs/`
  - 写入 `spec-evaluation-question-base-import-edit-fix.md`
- 验证:
  - 文件已存在
  - 内容与当前 spec 一致

### Step 1: 实现统一标准化与解析能力
- 目标: 在 `EvaluationServiceImpl` 中沉淀可复用私有方法
- 产出:
  - 原始字符串标准化
  - 选项块解析
  - 答案标准化
  - `questionKey` 生成
- 验证:
  - 针对 `A内容`、`A 内容`、`A    内容`、`A、内容`、`维生素D`、`G-6-PD`、中英文逗号答案 做方法级验证

### Step 2: 修复导入链路
- 目标: 用新解析器替换旧的 split 逻辑
- 产出:
  - 不再出现 `ArrayIndexOutOfBoundsException`
  - 不再出现空白选项
  - 同题替换与新增逻辑正确
  - `question_num` 正确
- 验证:
  - `多选6题.xlsx` 导入成功
  - `单选200+多选100（格式转换结果）.xlsx` 导入后无空白选项

### Step 3: 修复编辑重复判定
- 目标: 让编辑与导入口径一致
- 产出:
  - `checkSaveEvaluationQuestionBaseDTO` 改为使用 `questionKey`
- 验证:
  - 图片 4 场景可保存
  - 同键重复题仍被拦截

### Step 4: 稳定回填顺序
- 目标: 让详情页回显稳定
- 产出:
  - 题目和选项查询增加显式排序
- 验证:
  - 导入后打开编辑页，题目与选项顺序稳定且与 Excel 一致

### Step 5: 集成验证
- 目标: 形成闭环
- 验证:
  - 编译通过
  - 两份样本 Excel 回归通过
  - 导入新题库/导入已有题库/编辑已有题库/详情回填/题库列表数量都正确

## 6. Subagent 执行策略
执行阶段按 3 路并行，减少串行等待：

- Worker 1: Spec 落盘 + 导入解析器实现
  - 负责创建 `docs/` 与 spec 文件
  - 负责 `importEvaluationQuestionBaseQuestion` 的标准化、选项解析、答案解析、导入写入逻辑
  - 写入范围: spec 文档 + `EvaluationServiceImpl` 中导入相关代码

- Worker 2: 编辑判重 + 回填排序
  - 负责 `checkSaveEvaluationQuestionBaseDTO`
  - 负责 `getEvaluationQuestionBaseQuestionList` / `getEvaluationQuestionBaseQuestionOptionList` 排序稳定性
  - 必须复用 Worker 1 定义的 `questionKey` 规则，不自行发明第二套判重逻辑

- Worker 3: 验证与回归
  - 在前两路代码成型后负责编译、样本 Excel 导入验证、关键场景回归
  - 输出失败用例、日志与剩余风险
  - 不修改业务逻辑，只做验证和必要的最小反馈

主代理职责：
- 统一 `questionKey` 和解析规则定义
- 集成 Worker 1/2 的实现
- 处理交叉冲突
- 最终跑一轮完整验证并给出结果

## 7. Test Plan

### 7.1 样本回归
- `多选6题.xlsx`
  - 预期: 不报错，全部题目可导入
- `单选200+多选100（格式转换结果）.xlsx`
  - 预期: 不出现空白 B/C/D/E 选项，答案标记正确

### 7.2 解析鲁棒性用例
- 选项正文包含 `维生素D`
- 选项正文包含 `G-6-PD`
- 选项使用中文标点、英文标点、混合标点
- 选项带多空格、异常换行、空白行
- 答案使用中文逗号、英文逗号、顿号、首尾空格

### 7.3 重复与覆盖用例
- 同题干不同选项 -> 允许共存
- 同题干同选项同答案同分值 -> 替换旧题
- 同题干同选项但答案不同 -> 替换旧题
- 同题干同选项但分值不同 -> 替换旧题
- 同一批 Excel 内相同 `questionKey` 出现两次 -> 标记失败，不自动覆盖

## 8. Assumptions
- 选项标签范围按 `A-Z` 处理，当前样本已覆盖到 `E`
- 不新增数据库唯一索引，唯一性继续在业务层控制
- 导入结果 VO 结构不变
- 旧题 option/answer 的孤儿数据清理不作为本轮主修目标，除非实现时发现会影响当前功能
