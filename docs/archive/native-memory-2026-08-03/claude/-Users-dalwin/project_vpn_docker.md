---
name: project-vpn-docker
description: ~/Library/CodeRepo/vpn-docker — EasyConnect/aTrust 容器化隔离代理（Mac），架构选择结论与遗留事项
metadata: 
  node_type: memory
  type: project
  originSessionId: b1fc3f81-fcb2-40ff-9292-3598a623bd62
---

`~/Library/CodeRepo/vpn-docker/` 是 EasyConnect/aTrust 容器化隔离代理项目（2026-06-13 建成并验证，基于 hagb/docker-easyconnect 上游镜像，compose + start.sh/stop.sh + README）。

关键实测结论（Apple Silicon，勿改 compose 的 platform）：
- EasyConnect 必须 `linux/amd64` + Rosetta（arm64 镜像是低版本 UOS 客户端，TLS 被服务端拒）；
- aTrust 必须 `linux/arm64` 原生——amd64 在 Rosetta 下 aTrustAgent 的 thrift rpc 线程因 EINTR 异常自杀，54631 起不来；两架构客户端版本一致 2.5.16.20；
- EC 镜像的 tinyproxy(8888) 在 Rosetta 下偶发启动失败，start.sh 已内置补拉起（注意：直接 docker compose up 不走 start.sh 时 tinyproxy 仍可能挂，需手动补）。

第二轮增强（2026-06-13）：
- 中文账号输入：CEF 登录框装 fcitx 兼容性差，最初改用剪贴板机制（`paste.sh` 写 xclip + VNC Ctrl+V）——**此方案对真实 VNC Ctrl+V 是失败的，见第五轮**（当时"实测双向通"只验了 xclip→xclip，未走真实 VNC 客户端）。
- 保活：镜像内置 `while sleep $PING_INTERVAL; do ping/wget` 循环，靠 PING_ADDR/PING_ADDR_URL 启用。已接入 compose+.env，PING_INTERVAL 默认 60，地址留空待用户登录后填内网地址。已用网关地址实测周期发包成立。
- tgfw（TGFW SecNode）调研定案见 `docs/tgfw-容器化方案.md`：拆包实测本质=Java GUI 外壳+改名 OpenVPN(et.exe, tap-windows6)。容器化高度可行（OpenVPN Linux 原生），但 .ovpn 由服务端登录后动态下发，需用户先抓配置。用户已选「只出文档暂不封装」。

第三轮（2026-06-13）：
- 排查「原生 EasyConnect 登录转圈」：实测确认容器映射端口(1080/1081/5901/5902/8888/8889/54631)与原生 EC 端口零重叠，非端口冲突；真因是 Clash Verge TUN 模式(utun1024/198.18.0.1)接管全局路由与原生 EC 抢路由。用户确认 TUN 开着，关掉后能登录，决定不动其他东西。结论：原生客户端+Clash TUN 必冲突，彻底改用容器方案+卸载原生才根治。
- Notion 双版本笔记：本会话 Claude Code 未挂载 Notion MCP（claude mcp list 只有 context7/apifox），Chrome 扩展也未连。用户在 claude.ai 网页 Connectors 授权了 Notion，同步出现 `claude.ai Notion` server(✔Connected)，但 MCP 工具仅会话启动时注册，本会话仍调不到（+notion 搜索为空），需重启 Claude Code 会话才加载。已删除我误加的冗余 `notion` server。
- 已把 win/mac 双版本完整方案写成 `docs/Notion-双版本容器化VPN方案.md`，供重启后读它推 Notion Palace，或用户手动粘贴。原笔记在「工作/智慧托育管理系统(Saas)」资料库，新笔记目标位置 Palace。

第四轮（2026-06-13，重启会话后）：Notion 双版本笔记已完成。`claude.ai Notion` MCP 工具重启后可用。新笔记《国产 VPN 容器化隔离方案（Win/Mac 双版本）+ Clash 分流内网》已发布到 Palace「全局知识引擎」database（page id 37e0c9cd-20f4-815e-8678-f3cddd31a7a0），属性：领域=工作/内容类型=方法论/来源类型=自写/阶段=已输出/标签=Docker+VPN（标签库新增了 Docker、VPN 两个 multi_select 选项）。十节齐全（含 win cli/VNC 双模式、mac 双架构、中文剪贴板、保活、Clash 分流、tgfw 结论）。
踩坑记录：① Palace multi_select 新选项必须先 update-data-source 加，不能创建页面时自动建；② Notion MCP 写入偶发 Cloudflare WAF 拦截——`printf | docker exec | sh -c 'xclip'` 这种「管道+sh -c+重定向」命令行稳定触发 WAF，改成文字描述即过；分段 insert_content 可规避大 payload。

第五轮（2026-06-16，中文输入 ????  根因修复）：
- 现象：VNC 里 Ctrl+V 中文账号全变 `????`（截图实证 `????02`）。
- 根因（系统化调试取证定案）：VNC 服务器是 **Xtigervnc**；CEF 登录框读 X11 剪贴板，但 RealVNC Viewer 的 Ctrl+V 走 **RFB 协议剪贴板同步，RFB 传统 ServerCutText/ClientCutText 只支持 Latin-1**，中文→`0x3f`(字面量?)；且 TigerVNC 会用 Latin-1 值反复覆盖容器内 X 剪贴板（`xclip -o` 实测就是 `3f 3f 3f 3f 30 32`）。所以旧的"xclip 写 UTF8_STRING + Ctrl+V"改错了层，对真实 VNC 必失败。
- 修复：`paste.sh` 改用 **`xdotool type` 把文本作为 Unicode 按键事件直接注入当前聚焦窗口**，绕开 X 剪贴板与 VNC 剪贴板，无 Latin-1 转换。实现走 `docker exec -e DISPLAY=:1 -e LC_ALL=C.utf8 <ctn> xdotool type --clearmodifiers --delay 80 -- "$TEXT"`（argv 直传，零嵌套 shell 引号）。xdotool 上游镜像不带，脚本首次 `apt` 自动装（容器重建后再装，容器走 Clash fake-ip 出网 apt 实测可达）。
- 验证（决定性，非自欺）：① xdotool type 进 xterm 跑 `cat>文件`，读字节 = `测试2021张三@公司` 一字不差；② `docker exec -e ... printf` 验 argv UTF-8 直传字节正确。注意 CEF+XTEST **合成点击/Ctrl 组合键不可靠**（focus 切不动、flwm 无 _NET_ACTIVE_WINDOW），但真实鼠标点框 CEF 正常——故新流程要求：用户先在 VNC 用真鼠标点输入框，再跑脚本。新增 `PASTE_DELAY` 可调慢。README 已同步改写。
- 待用户实测：真实账号在真实点框后跑 `paste.sh` 是否把中文打进可见的用户名框（我无法自测 CEF 真实点击聚焦）。Notion Palace 笔记的中文输入节仍是旧剪贴板描述，待同步。

遗留：① 用户尚未用真实账号做 VPN 登录实测，保活内网地址待登录后填；② 本机仍装着原生 EasyConnect.app（与 Clash TUN 抢路由致登录转圈），建议卸载；③ tgfw 待用户抓到 .ovpn 后按路线 A 封装 OpenVPN 容器；④ Notion Palace 笔记(page 37e0c9cd-20f4-815e-8678-f3cddd31a7a0)中文输入节待从"剪贴板 Ctrl+V"改为"xdotool 直接打字"。
