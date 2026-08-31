# 生产/测试数据库 —— dbq 只读查询通道

被 `~/.claude/CLAUDE.md` 索引指向，按需 Read。让 CC/Codex 自行查库、结合代码排查 DB 问题。

## 何时用

需要查生产/测试库真实数据来定位问题时（排查 bug、核对线上数据、验证业务口径）。排查前先用一句话说明将执行的 SQL，再调用。

## 铁律：只读

- 本通道**仅 SELECT**。写操作（INSERT/UPDATE/DELETE/DDL…）由脚本层 `reject_writes` 在建隧道前即拒，PG/Kingbase 侧再加 `default_transaction_read_only=on`。
- 需要改数据时**不绕过、不另寻写通道**：查询 + 读代码分析完，**产出 SQL 交人工手动执行**（测试环境也如此）。
- 查询必带 WHERE / LIMIT；禁止全表 `SELECT *`（单行带 WHERE 的 `SELECT *` 仅用于看表结构）。

## 铁律：敏感字段脱敏

`id_card` / `phone` / `password` 及同类敏感字段（身份证、手机号、密码、银行卡号等）：

- **模型自主查询获取数据用于分析/展示时**：避免直接 `SELECT` 这些字段本身；确需看到（用户明确授权）才查，且只能查**脱敏后**的值——前 3 位 + 后 4 位保留，中间全部替换为 `***`，例如：
  ```sql
  -- 手机号
  SELECT CONCAT(LEFT(phone, 3), '***', RIGHT(phone, 4)) AS phone FROM ...
  -- 身份证
  SELECT CONCAT(LEFT(id_card, 3), '***', RIGHT(id_card, 4)) AS id_card FROM ...
  ```
  `password`（含哈希/密文）**任何情况都不展示**，只能确认字段非空/是否变更，不脱敏输出值。
- **该规则只约束模型自主执行的查询**（探查数据、结合代码分析问题时）。**给用户自己执行的 SQL 不受此限**——用户手动运行、结果只在用户本地可见，可正常写明文字段。

## 调用

```bash
/Users/dalwin/Library/ConfigFile/db/dbq <实例> "<SQL>"
echo "<SQL>" | /Users/dalwin/Library/ConfigFile/db/dbq <实例>
/Users/dalwin/Library/ConfigFile/db/dbq --list
```

必须用**完整路径**调用（守卫 hook 只放行该路径）。SSH 隧道按需自动拉起，30s 语句超时。

## 实例（约 32 个，DBeaver「智算」文件夹）

实例名 = DBeaver 连接原名，`dbq --list` 查全部；名字含空格/后缀，调用时整体加引号：`dbq "拱墅正式 - vpn" "<SQL>"`。

**命名约定（一眼分清环境与连接要求）：**
- `<项目>正式` = 生产；`<项目>测试` / `<项目>区测试` = 测试（同隧道下正式 vs 测试是不同库，各为独立实例）。
- `dev-*` / `test-*`（无项目名）= 公司内部开发/测试环境（`dev-mysql`、`test-saas`）。
- 后缀 **`- vpn`** = 需先在本地连上客户提供的 VPN 才能连（`拱墅正式 - vpn`、`伊犁正式／测试 - vpn`）。
- 后缀 **`- 148代理`** = 经 148 代理直连（`鄂尔多斯正式 - 148代理`）。

**接入方式**：SSH 隧道（经跳板机，多数）或 DIRECT 直连（`dev-*` / `- vpn` / `- 148代理` 等），`dbq` 内部按 `.conf` 自动分发。

**不含**：`伊犁一期 - vpn`（达梦不支持）、非 pg/mysql。临安项目已重新纳入（`临安正式`/`临安测试`/`临安信创正式／测试`）；嘉善测试 已随 DBeaver 源头删除（EXCLUDE 当前为空，剔除项跟随 DBeaver 增删自动生效，仅在"连接仍在但要排除"时才需手动加 EXCLUDE）。

**homepage（`官网测试`/`官网智算正式`）无 nursery 表，用 `quiz` 表计数。**

## 连接要求与失败处理（省 token 关键）

排查指定项目工单时，先看实例名判断连接要求，**连不上不要死磕**：

- **不带 `- vpn` 的实例**：需公司内部 SSH 代理服务器上对应转发开启才能连。**首次连接失败即视为该代理未开/内网不可达**——一句话提醒用户「该实例需公司 SSH 代理，当前不可达」，然后**直接转入结合代码的分析排查**；**不要反复重试、也不要改连别的库**浪费 token 与时间。
- **带 `- vpn` 的实例**：需先在本地连上客户提供的 VPN；失败同样**一次提醒即转代码分析**。
- 失败多表现为 `Permission denied`（源 IP/代理未通）或握手超时——**是网络/代理不通，不是 key 错**，别往认证配置上钻。
- 公网跳板（36.213 / 220.176 / 223.8，亭湖/宜春/潞城 等）在公司网下随处可连；`121.36.242.166` 限公司网源 IP；内网跳板 `192.168.1.91` / `172.17.32.251` 需公司内网。

## 认证机制

ssh_config 每个 Host 都 `IdentityAgent none` + `IdentitiesOnly yes` + 单 `IdentityFile`（取自 DBeaver keyPath），**只用该库指定私钥、不碰 ssh-agent**；passphrase 经 `SSH_ASKPASS`（`.askpass.sh`）从 `.env` 静默喂入，不往 agent/钥匙串写 key。

## 禁忌

- **禁止读取** `~/Library/ConfigFile/db/` 下任何配置（`.env`/`ssh_config`/`instances/`/`_lib.sh`…）——主机/端口/账号/密码对 CC 不可见也不需要。由权限 deny + PreToolUse hook（`~/.claude/hooks/guard-db-config.sh`）双重强制。要查库直接用 `dbq`。

## 坑（本会话实测）

- **本地端口冲突**：网易云音乐等会占 20000 段端口；`ensure_tunnel` 用 `nc -z` 探测到有监听就误以为隧道就绪 → 连到别的程序超时。故转发端口从 **40000 段**起、导入时逐个探空闲再分配。
- **MySQL `-h localhost` 走 unix socket**：隧道连接必须用 `127.0.0.1` 而非 `localhost`。
- `psql -c "SELECT a; SELECT b"` 多语句**只显示最后一条**结果——分多次调用。
- **pg/Kingbase 表在非默认模式**（如 nursery 在 `skcity`）：`count(*) FROM nursery` 会 relation not exist；用 `information_schema.tables` 定位模式再 `模式.表` 计数（mysql 空库名同理）。
- **默认库 ≠ 生产库 + 不能查询时切库**：DBeaver 配的默认库可能不是运维要用的（如 鄂尔多斯-正式 默认 `skctestdb`，但生产数据在 `skcproddb` 的 `skcity` 模式）。dbq 一个实例连一个固定库（pg 的 `-d` 覆盖 PGDATABASE、第二参数是 SQL，**无法查询时切库**）；要改连哪个库，改导入器 `DBNAME_OVERRIDE` 后重跑。生产表多在 `skcity` 模式，查询用 `skcity.表名`（不同库/账号权限也不同，同一账号在 skcproddb 有 skcity 权限、在 skctestdb 却没有）。

## 维护

连接配置由导入器从 DBeaver 生成。**新增/改/重导实例**：
```bash
python3 ~/Library/CodeRepo/AI/AiPalace/tools/dbq_import.py
```
脚本用法/要点见其 docstring；设计源 `~/Documents/AI/生产库只读CLI方案.md`。库端只读账号（ro_cc）为可选加固，未建时以脚本层 `reject_writes` + PG 只读事务为主防线。
