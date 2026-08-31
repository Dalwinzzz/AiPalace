skcactivity 仓库**根目录没有聚合 pom**，不是 multi-module reactor。`skc-activity/`、`skc-evaluation/`、`skc-qa/` 各是独立 Maven 工程，parent 是公司父 pom `skc`（SNAPSHOT，需联网）。

因此 `mvn -pl skc-activity` 会报 "Could not find the selected project in the reactor"。正确做法：cd 进子工程目录直接编译。

编译 skc-activity 的标准命令（须 JDK 8，见 [[java-spring]] 工作域规则）：
```
cd skc-activity
export JAVA_HOME="/Library/Java/JavaVirtualMachines/jdk-1.8.jdk/Contents/Home"
mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository -q compile
```
`-q` 模式下 BUILD SUCCESS 无输出。macOS 无 `timeout` 命令，靠 Bash 工具自身超时。

## MyBatis 配置（来自 nacos，开发/测试/生产通用）

本工程 `@MapperScan`/`mapperLocations`/`typeAliasesPackage` 都在 nacos 共享配置，本地仓库没有。已确认实际配置：
```yaml
mybatis:
  typeAliasesPackage: com.iktapp.skc.activity
  mapperLocations: classpath*:mapper/**/*.xml
```
- `mapperLocations` 用 `**` 通配，所以 `resources/mapper/**/任意子目录/*.xml` 都会被加载（新增 mapper xml 放子目录 OK，无需平铺到 mapper/activity 根）。
- `typeAliasesPackage` 覆盖 `com.iktapp.skc.activity` 全包，该包下实体可直接用短类名 alias。
- 新增手写 Mapper 接口建议仍加 `@Mapper` 注解（双保险，不强依赖 nacos 的 MapperScan 包前缀）。
