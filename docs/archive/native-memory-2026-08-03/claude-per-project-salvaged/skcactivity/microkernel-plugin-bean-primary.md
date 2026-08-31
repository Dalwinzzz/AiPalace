skcactivity 的 `refactor/micro-core-dev` 分支引入了微内核插件架构：区域定制业务逻辑收纳进独立模块 `activity-plugin-<region>`（如 `activity-plugin-jiashan`），覆写 core 包（`activity-core`）里的 XxxServiceImpl。**微内核底层依赖包（framework 层）已保证 plugin 模块里的同接口实现相对 core 包默认优先加载为 primary bean**——插件类不需要、也不应该手动标注 `@Primary`。

**Why:** 2026-07-10 审查 `25485e40`/`5f000f6c`（嘉善证书插件化）时，把 `JiaShanCourseOfflineServiceImpl` 新增的 `@Primary` 当作"与提交意图无关的可疑夹带，需确认"标了 🟡；用户纠正：这是微内核框架的内置能力，手动加 `@Primary` 是多余的，应明确要求去掉而非停留在"确认"。

**How to apply:** 审查或编写 `activity-plugin-*` 模块代码时，见到插件 ServiceImpl 上手动加的 `@Primary` 应视为应删除的冗余标注（除非有明确的多接口装配歧义证据支撑）。这与 [[third-party-integration-package]]（对接外部系统的 third 包）是两套不同机制：third 包管外部系统对接，plugin 模块是微内核区域业务定制，两者不要混为一谈。
