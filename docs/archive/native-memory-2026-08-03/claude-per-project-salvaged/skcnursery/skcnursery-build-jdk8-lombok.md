skcnursery（skc-nursery 模块）是 JDK8 项目。本机 `mvn` 默认走 Homebrew JDK24，lombok 在 JDK24 下完全失效 → 188 个「找不到符号」（所有 @Data/@Slf4j 生成的 getter/setter/log）。

编译/跑测试必须指定 JDK8：
```
JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-1.8.jdk/Contents/Home \
  mvn -f skc-nursery/pom.xml test -Dtest=Xxx -Dsurefire.failIfNoSpecifiedTests=false
```

坑：`/usr/libexec/java_home -v 1.8` 会误选版本号更高的 **JRE**（`/Library/Internet Plug-Ins/JavaAppletPlugin.plugin/...`，无 javac，报「No compiler is provided」），要用上面完整 JDK8 路径。

测试栈：JUnit5 + Mockito + Spring `ReflectionTestUtils`，纯 POJO 单测（不起 Spring）。**测试文件被全局 gitignore（`~/.config/git/ignore-ideaproject` 的 `**/*Test.java`）忽略**，入库需 `git add -f`（现有 8 个测试类都是这么加的）。相关修复见 [[nursery-eerduosi-portrait-scope-zero-bug]]。
