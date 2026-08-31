余姚正式 2026-07-07 报的 `/staffCheckup/seal` 盖章 NPE（日志只有裸 NPE 无堆栈）。

**根因（高置信推断，待运维查 nacos 确证）**：feign 服务间调用收到 gzip 压缩响应却按明文 JSON 解析。`DrawUtils.imgOnPdf` 里 `remoteFileService.getFile(pdfPath).getData()`——getFile 的 feign 调用解析失败走 `RemoteFileFallbackFactory` 返回 `R.fail`（data=null）→ `new PdfReader((byte[])null)` → 裸 NPE。

**判定证据链**：
- seal 最后一次成功停在 2026-07-03 09:14，之后 `is_seal=1` 记录为 0（100% 失败）；DrawUtils/Service 业务代码近期未改 → 环境/配置问题非代码逻辑。
- 同请求下一秒 RemoteLogService(feign) 报 `Illegal character (CTRL-CHAR, code 31)`——**code 31=0x1F 是 gzip 首字节**。
- 关键对比：同记录 **upload 成功（浏览器直连自动解压 gzip）但 getFile 失败（feign 不解压）** → 排除 file 服务宕机，锁定压缩问题。
- 无堆栈是 JVM 默认 `OmitStackTraceInFastThrow`（热点 NPE 省略堆栈），非日志写法问题（GlobalExceptionHandler 本有传 e）。

**最可能诱因**：nacos 里开了 `feign.compression.response.enabled=true` 但缺 `useGzipDecoder=true`。修复：关掉该压缩（推荐，内部调用压缩收益低）或补 useGzipDecoder。影响面不止盖章，所有依赖 feign 返回值的功能都中招。

**已做的代码加固（治标，工作区改动待用户提交）**：imgOnPdf 4 个 feign 点（getFile×2/upload/uploadImage）加判空——技术细节（path/code/msg）走 log.error 进日志，对外只抛纯业务语义 ServiceException（如"盖章失败：健康证文件读取失败，请稍后重试"），替代会传到前端的裸 NPE。DrawUtils 用 @Slf4j。根因仍需 nacos 修。

**同批修的另一个 bug**：`saveStaffCheckupDetail` 漏 `setDepartment` 致从业人员"单位"改了不保存回显丢失——已补 setDepartment。
