# context7 MCP 使用细则

## 两个工具

1. **`resolve-library-id`** —— 传库名（如 `"next.js"`、`"react query"`、`"upstash redis"`），返回 context7 规范库 ID（如 `/vercel/next.js`）。
2. **`get-library-docs`** —— 传库 ID，返回最新文档；`topic` 参数收窄（如 `"app router"`、`"streaming"`、`"middleware"`）。

## 标准流程

1. 用请求里的库名调 `resolve-library-id`。
2. 选最佳匹配（trust score 最高 / 名称最接近）。
3. 用该 ID 调 `get-library-docs`，问题具体时加 `topic` 收窄。
4. 用返回片段写 / 验代码，相关处引用具体 API。
5. `resolve-library-id` 无有用结果 → 回退 WebSearch / WebFetch。

## 边界

- 别因"已知此 API"跳过——版本会变。
- 不用于与具体包无关的通用编程（算法、语言语法、shell 命令等）。
- 不用于本仓库内部 / 私有代码——用 Read / Grep。
