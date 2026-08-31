新增或修改 REST 接口时，一律只用 `@GetMapping`/`@PostMapping`，不得使用 `@PutMapping`/`@DeleteMapping`。

**Why**：2026-07-28 前端联调「儿童健康体检v1.0.4」[[jianye-child-exam-v104-design]] 时，PUT 请求（`/infant/childExam/{id}/reportUrl`）被网关/安全策略拦截，返回 403 Forbidden（截图证实：请求方法 PUT，状态码 403，POST/GET 的同类接口不受影响）。用户明确说明"项目不允许使用put和delete请求"——这是平台级网关限制，不是本模块的偶发问题。

**How to apply**：
- 写新接口前默认用 GET（查询/无副作用）或 POST（有副作用：新增/编辑/删除/状态变更/文件地址回写等），不要因为语义上"更像 REST 规范的 PUT/DELETE"就用它们。
- "回写某个字段"这类语义上像 PUT 的操作，照样用 `@PostMapping`，参数保持不变（`@PathVariable` + `@RequestParam`/`@RequestBody` 均可，只改 HTTP method 注解本身，不需要额外改参数传递方式）。
- 若发现历史遗留代码里还有 `@PutMapping`/`@DeleteMapping`，联调报错 403 时按此规则直接改成 POST，不必纠结"语义是否合适"。
- 此规则目前只在 skcinfant 项目内验证过；若在其他智金SKC微服务里也发现同样的 403，大概率是同一条网关规则，可以照此规则处理，但没有额外证据前不要断言对其他项目也生效。

**已知实例（2026-07-28 修复）**：`ChildExamController` 的 `/infant/childExam/referral/{id}/fileUrl`、`/infant/childExam/{id}/reportUrl`，以及 `OrgChildExamController` 的 `/org/infant/childExam/{id}/reportUrl`，三处 `@PutMapping` 全部改为 `@PostMapping`，Apifox 对应接口（`492789980`/`492790160`/`492791445`）method 字段同步改为 post。
