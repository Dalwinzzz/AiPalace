不要尝试在本地仓库源码目录（`skcservers/` 下的子模块）中查找 framework 或 common 依赖包的源文件（如 `Constants.java`、基类、公共枚举等）。

**Why:** 本项目仓库只含业务微服务的源代码，framework / common 模块作为 Maven 依赖引入，本地没有对应源码目录。直接 `find` 会找不到文件，浪费 tool call。

**How to apply:**
- 需要了解 `Constants`、公共枚举、基类的字段值或方法签名时，改为：
  1. 在业务源码中 `grep` 该常量/类的**使用位置**，从调用侧推断其含义；
  2. 或在本地 Maven 仓库（`/Users/dalwin/Library/Repository`）中查找对应 jar，用 `jar tf` / `javap` 提取 `.class` 反编译；**绝不要用 `~/.m2`，本地仓库不在默认路径。**
  3. 或直接阅读调用方代码上下文，足够理解语义时不必深挖底层源码。
- 绝不要用 `find . -name "Constants.java"` 从项目根目录递归搜索。
