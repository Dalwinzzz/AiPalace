skcactivity 里对接外部系统（政务专网 / HIS / 第三方平台等）的代码，统一收纳到 `com.iktapp.skc.activity.third.<对接方>` 子包（`third` = 第三方对接），包内再分 controller / config / client / service / support / dto；不要散落到顶层 controller/service/config/dto 各目录。

**Why:** 用户在 2026-06 做南京省妇幼「儿童身高体重评价」SOAP 对接时明确要求——第三方对接自成一块、与本地业务解耦，后续其他对接各起 `third/<x>` 互不干扰，便于统一管理与查找。

**How to apply:** 新第三方对接开工时先建 `third/<name>/` 包（如 `third/njsfy/` 南京省妇幼）。传输层抽象成可替换 client 接口 + impl；配置走 nacos 独立前缀（如 `njsfy.mchis.*`，最小必填项尽量少，密钥类缺省可降级）；给前端的正式接口与仅自测用的内部接口分开——Apifox 里测试接口放 INTERNAL 目录、不公开发布，只发布业务接口。参见 [[skcactivity-build]]。
