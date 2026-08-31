查余姚正式环境数据用 `dbq 余姚正式`，业务库是 **skcproddb**（另有 yyytjdb 数据统计库）。

坑：直接 `dbq 余姚正式 "SELECT ..."` 会报 `ERROR 1046 No database selected` —— dbq 连接不带默认库，SQL 里必须用库名限定表名，如 `SELECT ... FROM skcproddb.staff_checkup WHERE ...`。

与 [[dbq-eerduosi-query-skcproddb-skcity]] 同类：都是 skcproddb 库，但余姚是 MySQL（库名限定即可），鄂尔多斯是 Kingbase（还要选 skcity 模式）。
