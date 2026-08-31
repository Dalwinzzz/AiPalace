---
paths:
  - "**/pom.xml"
  - "**/*.java"
  - "**/mvnw"
---

# Java / Maven 本地配置（个人全局上下文）

> 本文件是 java/spring 工作域的 **path-scoped 硬规则**。真源在
> `AiPalace/context/rules/java-spring.md`，经 `~/.agents/context/java-spring.md` →
> `~/.claude/rules/java-spring.md` 两跳 symlink 派生；命中 java 信号文件
> （pom.xml / *.java / mvnw）时自动注入，勿手改派生物。

本地 Maven 仓库**不在**默认的 `~/.m2`，**绝不能用 `~/.m2`** 查找或解压依赖 jar。

- 本地 Maven 仓库：`/Users/dalwin/Library/Repository`
- settings.xml：`/Users/dalwin/Library/ConfigFile/maven/saas/settings.xml`

**执行任何 `mvn` 命令时必须附加：**

```
mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository <goal>
```

**JDK 版本（关键，否则编译假性失败）：**

SunkidCloud 等老 SpringCloud 项目用 **Lombok 1.18.22**，只兼容 **JDK 8**。系统默认
`JAVA_HOME` 可能是 Homebrew 的高版本 JDK（如 24），在高版本下 Lombok APT **静默失败**，
表现为大量 `@Data`/`@Getter` 类报"找不到符号 getXxx()/setXxx()"——这是**假错误**，不是代码问题。

编译这类项目前必须先指定 JDK 8：

```
export JAVA_HOME="/Library/Java/JavaVirtualMachines/jdk-1.8.jdk/Contents/Home"
```

本地可用 JDK（`/usr/libexec/java_home -V` 查看）：JDK 8 `jdk-1.8.jdk`、JDK 17 `ms-17.0.15`、JDK 24。
老项目（Lombok ≤1.18.22）一律用 JDK 8。

**不要随意加 `-o`（offline）：** 项目依赖大量 `*-SNAPSHOT`（如 skc-api-evts），每天有新构建，
离线模式会因"最新 SNAPSHOT 未下载"而失败。需联网拉取时去掉 `-o`。验证编译标准命令：

```
export JAVA_HOME="/Library/Java/JavaVirtualMachines/jdk-1.8.jdk/Contents/Home"
mvn -s /Users/dalwin/Library/ConfigFile/maven/saas/settings.xml -Dmaven.repo.local=/Users/dalwin/Library/Repository -q compile
```

**查找 / 解压 Maven 依赖 jar 时：**

- 查找：`find /Users/dalwin/Library/Repository -name "*.jar" ...`，不要用 `find ~/.m2 ...`
- 解压：`jar tf|xf /Users/dalwin/Library/Repository/...`，不要用 `~/.m2/...`

---

## 写 SQL 前先读

要写/改 **mapper XML、业务列表或统计查询**时，先读
`~/Library/CodeRepo/AI/AiPalace/vault/memory/01-PROJECTS/tech/sql-performance.md`
——结构红线（相关子查询 O(N²)、派生表不下推）、索引与覆盖、分页 count、
`explain` 验证纪律，从三轮线上 504 事故提炼。**提交业务 SQL 前过一遍文末速查清单。**
