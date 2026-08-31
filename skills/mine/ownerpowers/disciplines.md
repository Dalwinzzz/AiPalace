# 三条纪律 · 项目落地细则

> ownerpowers 的三条纪律（test-first / 根因优先 / 完成前验证）本身是现代模型的默认工作方式，
> 本文件**不复述方法论**，只记录三件在本地环境里"不查就会做错"的事：跑测试的命令、栈相关的根因入口、以及三条铁律的边界。

## 铁律（一句话版）

1. **test-first**：T2 实现强制、T1 写新功能单元建议——先有失败的测试，再写生产代码。一次性原型 / 生成代码 / 纯配置例外。
2. **根因优先**：T2 排查强制、T1 非平凡 bug 按需——没做根因调查不提修复方案。同一 bug 修 ≥3 次仍不好 → 停手，和用户讨论是不是架构错了，别打第 4 个补丁。
3. **完成前验证**：T1/T2 必走——没在**本条消息里**跑过验证命令，就不说"通过 / 完成 / 修好"。子 agent 报告"成功"不算证据，看 diff 才算。

## 跑测试 / 构建的本地命令（关键：本地 settings.xml + 独立仓库路径）

**Java / Spring（syzh 等，JDK8）**

```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)   # 老项目先切
mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml \
    -Dmaven.repo.local=/Users/dalwin/Library/Repository \
    -Dtest=类名#方法名 test        # 单测；去掉 -Dtest 即全量
```

栈：JUnit5 + AssertJ + Mockito（仅边界依赖）。
**切片 vs 单元**：纯业务逻辑 / 算法走纯单元测试（不起 Spring，最快）；只有要校验注入 / 事务 / MyBatis 映射时才 `@SpringBootTest` 或 `@MybatisPlusTest`，别动辄全量起容器。

**Go**：`go build ./... && go test ./... -race`；单测 `go test ./pkg/... -run TestName -v`。表驱动测试是默认形态。

**前端**：读 `package.json` 里项目实际的 build / test 脚本，别假设。

## 栈相关的根因入口（先看这几处，通常在这里）

- **Spring**：NPE 往上游追注入是否生效 / 事务边界（`@Transactional` 自调用失效）/ MyBatis 映射列名 / 配置未生效（profile、`@Value` 占位）/ 分布式调用超时与序列化。
- **Go**：data race（先跑 `-race`）/ goroutine 泄漏 / `context` 未取消 / nil map 写 / channel 死锁 / interface nil 判断陷阱。
- **多组件链路**（CI→build→sign，API→service→DB）：先在**每个边界**打日志跑一次，定位"在哪一层断"，再钻那一层——别一上来就猜某层。

## 与决策点②的叠加

决策点② = 提交前摊"改了哪些文件 + diff + 提交计划"等拍板；纪律三要求其中"自测通过"这句必须有**本轮新鲜跑出来的证据**，不能口头带过。
