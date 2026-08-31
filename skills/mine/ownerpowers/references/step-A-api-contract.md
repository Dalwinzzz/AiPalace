# step-A · 接口契约对齐（Apifox MCP，条件触发）

> **触发条件**：仅当改动涉及 Controller 接口 / 字段变更。不涉及接口则整段跳过。

## 三个时点

| 时点 | 线 | 动作 |
|------|----|----|
| 前置 | 需求线（进 step-B 前） | 从 Apifox 拉 OpenAPI / 字段 / 用例，当作实现靶子 |
| 提交前 | 需求线（进 step-E 前） | 核对实现与契约是否一致；不一致先对齐再提交 |
| 收尾 | 排查线（step-E 后） | 反向更新 Apifox 文档，防文档腐化 |

## 委托对象

Apifox MCP 工具族 `mcp__apifox-new-mcp__*`，常用：
- `listOpenApiEndpoints` / `getOpenApiDetails` / `getHttpEndpoint` — 拉契约与字段
- `listTestCases` / `getTestCase` — 拉用例
- `updateHttpEndpoint` / `createHttpEndpoint` — 收尾回写文档（属"改文档"，需经决策点②或额外确认）

## 注意

- 回写 Apifox 文档（update/create）属于对外产物变更，须在决策点②已确认或额外确认后再做。
- 若 Apifox MCP 当前不可用，提示用户手动核对，不阻塞主流程。
