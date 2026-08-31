做一个跨多次迭代的大需求时，若其中某个子功能（如校验）产品方急着先上线，用户的交付方式是：从 develop 新建本需求的 feature 分支 → 把该子功能**单独一个 commit** 提交在 feature 分支 → 再 **cherry-pick 到 develop** 单独先上线，feature 分支保留继续做需求其余部分。

**Why:** 既能让紧急部分尽快上 develop/上线，又不污染 feature 分支的整体节奏，后续其余部分仍在同一 feature 分支推进。

**How to apply:** 遇到"先上线一部分"的诉求时，主动按"feature 分支单独 commit → cherry-pick develop"组织，而不是直接把半成品全压到 develop。push 到共享分支 develop 前务必显式确认（不可逆、可能触发 CI/上线）。本需求 feature 分支：`feature/nj/inclusiveReverseNursery_v1.0.6`。
