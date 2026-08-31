#!/usr/bin/env python3
"""SessionStart hook:把 vault/memory 的 always-on 三件套拼成注入文本。

顺序 = operating-rules.md(共享操作规则,法律在前) → identity.md(精简身份卡)
     → INDEX.md(决策树导航,在后)。ADR-0016 定前两件;identity 于 ADR-0020 并入——
此前 INDEX 声明它"常驻·进会话必读"却未注入,实测模型每会话要多花一次 Read 才拿到,
声明与实现不一致,故改为直注(1.1KB,省一个 round-trip)。
双工具通用:Claude 经 additionalContext、Codex 经 SessionStart hook 输出同一文本。
仓库内准备;实际注册到 ~/.claude/hooks、~/.codex/hooks 属各工具接线。"""
import os, json, sys

def inject_index(context_root, files=("00-RULES/operating-rules.md",
                                      "00-RULES/identity.md",
                                      "INDEX.md")):
    parts = []
    for rel in files:
        p = os.path.join(context_root, rel)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                parts.append(fh.read().strip())
    return "\n\n".join(parts)

def main():
    root = os.environ.get("AIPALACE_CONTEXT") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "vault", "memory")
    text = inject_index(root)
    # Claude SessionStart 约定：additionalContext
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": text}}, ensure_ascii=False))

if __name__ == "__main__":
    main()
