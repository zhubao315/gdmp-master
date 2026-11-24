# 数据库维护运行手册（备份 / 迁移 / 索引）

> GDMP 运维**知识包**流程文档；GDMP 无 AI Agent/Skill 运行时（见 `audit/gdmp-skill-runtime-audit.md`），本包不被 AI 自动加载执行。
> 生产默认只读；备份之外的一切变更须审批（`<审批单号>`）、先 dry-run、**不可逆操作前先备份**；**DB 迁移与应用回滚分开制定**（R7）。证据状态：已验证 / 文档推导 / 待确认 / 不适用。

## 1 适用版本
- 知识包 `gdmp-master 1.0.0`（VERSION/manifest，已验证）。
- 平台：观测 commit `31e1f537…`（2026-09-02）；版本号**待确认**。
- 主库 PostgreSQL 16.16（容器，卷 `gdmp_pg2`/`gdmp_pg3`，驱动 42.7.3）；另有 MongoDB 备份脚本（数据库运维文档，已文档验证）。
- 自动迁移机制（数据库运维文档源码视角，已文档验证）：应用启动时 `GdmpTableMigrate` 扫描 `com.yr` 下 `@Table` 实体，已存在则 `Daos.migration` 幂等 ALTER 补列、缺失则 `dao.create`，日志记 `Synchroning to database table:`。
- 不适用：以 OpenCode 主机资源（128 CPU/499GiB/7×4090）充当 GDMP 容量基线（资源基线已明确否定）。

## 2 适用环境
- 备份脚本（数据库运维文档已验证）：`/app/scripts/sqlbak.sh`、`/app/scripts/backup_pg.sh`、`/app/scripts/backup_pg_dev_8081.sh`；备份根 `/data/backup`；保留 5 天（`find -mtime +5` 清理）。
- crontab（已验证示例）：`50 1 * * * sh /app/scripts/backup_pg.sh >> /data/backup/backup.log 2>&1`、`0 2 * * * find /data/backup/* -mtime +5 ... | xargs rm -rf`。
- 备份脚本变量：`dbname="gdmp"`、`pguser="gdmp"`、`backpath="/data/backup"`、`pdumpath="/usr/pgsql-14/bin/"`（**注意：示例路径是 pg14，现场为 pg16，须按台账确认→待确认**）、`export PGPASSWORD=<密码>`；`pg_dump -h 127.0.0.1 -U gdmp -d gdmp`。
- 平台迁移（pkg/data）：`DataModelUtils.exportCIData` / `importCIData`；**pkg 只建默认索引，手工索引不导出**（已验证）。
- 常用表：`t_sys_config`（`app_to_logon_pic` 128→4000）、`t_icon`、`t_icon_data`。

## 3 风险分级
- **高（R7）**：DB 迁移与应用回滚不可默认互逆；`importCIData` 非幂等，导入前必须有 `.data` 备份。
- **高**：`GdmpTableMigrate` 在中间态库误判 → `relation already exists` → `exit 255`（troubleshooting 源码视角，已验证）。
- **中**：手工表结构改动可能被自动迁移对齐或报错；手工索引不在 pkg 中，迁移后需重建。
- **中**：备份脚本硬编码 pg14 路径与明文密码变量，现场 pg16 需核对，凭据不得落盘。
- **中**：MongoDB 备份脚本（如使用）产出大文件，需归档与清理策略。
- 所有 DDL/DML 与迁移须审批、备份、dry-run。

## 4 前置条件
- 审批 `<审批单号>`、`<变更窗口>`；台账 `<现场台账路径>`：`<宿主机IP>`、`<DB_PORT>`、`<DB_USER>`、`<DB_PASSWORD>`、卷名、库/schema（`gdmp`）、脚本实际路径。
- 确认备份可用：`pg_dump` 产物存在且可读取；保留策略（5 天）不会误删所需备份。
- 记录迁移前表结构/索引快照（`pg_indexes`）、配置快照、当前 commit（`31e1f537…`）。
- 凭据从环境变量/交付文档读取、不落盘（`<DB_PASSWORD>`）。
- 明确区分：本次是“备份”“索引维护”“pkg/data 迁移”还是“版本升级引发的迁移”，分别制定方案。

## 5 诊断步骤（只读先行）
```bash
docker exec <容器名-db> pg_isready -U postgres                       # 连通（技能已验证）
docker exec <容器名-db> psql -U <DB_USER> -d gdmp -c "select * from pg_indexes where tablename='<表名>';"
ls -l /data/backup/                                                  # 备份产物与保留情况
grep -E "Synchroning to database table|relation already exists|Caused by" \
  /usr/local/tomcat/logs/catalina.$(date +%Y-%m-%d).log
```
- 核对备份脚本里的 `pdumpath`（示例 `/usr/pgsql-14/bin/`，现场 pg16 → 待确认）与 `PGPASSWORD` 来源。
- 核对 `t_sys_config.app_to_logon_pic` 长度是否 4000；不足则在迁移前规划扩容（运维参考）。

## 6 操作命令（来自数据库运维文档，逐条干跑，执行前审批+备份）
```bash
# 1) PG 备份（crontab 已验证示例，脚本内 pg_dump）
pg_dump -h 127.0.0.1 -U <DB_USER> -d gdmp > /data/backup/<日期>.bak
# 2) 平台数据导出/导入（Groovy 平台脚本，数据库运维文档已验证；容器环境用 upload 路径）
# println DataModelUtils.exportCIData('/tmp/202203281.data')
# println DataModelUtils.importCIData('/usr/local/tomcat/upload/20230522.data')
# 3) 索引创建（文档已验证示例，按现场表名/库名调整）
# CREATE INDEX idx_lshshjb_jlshj ON "t_历史数据表" USING btree (((data_field_map -> '记录时间')));
# 4) 字段扩容（运维参考，pkg 样式问题）
# ALTER TABLE gdmp.t_sys_config ALTER COLUMN app_to_logon_pic TYPE varchar(4000);
# 5) MongoDB（可选，数据库运维文档已验证）
# mongodump -o /data/db/backup -d yulin_jxkh --authenticationDatabase admin
# mongorestore -d yulin_jxkh /data/db/backup
```
- 备份脚本含压缩与保留：`tar -zcvf` 归档、`find /data/backup/* -mtime +5 | xargs rm -rf`（清理不可逆，须确认保留策略）。

## 7 预期结果
- 备份成功日志：`[Result] pgsqldb gdmp backup success`（脚本日志格式，已验证）；`.bak` 生成并可 `tar -zcvf` 归档。
- `exportCIData` 生成 `.data` 文件；`importCIData` 后应用无 `值太长了(128)`、样式正常（运维参考）。
- 索引/字段变更按预期生效，`pg_indexes` 可查；应用启动 `Synchroning to database table:` 正常、无 `relation already exists`。
- 手工索引在 pkg 迁移后需**手动重建**（pkg 不导出手工索引，已验证）。

## 8 成功判据
- 备份产物经校验可读；迁移前后行数/关键表抽查一致（抽查口径由台账定义，**待确认**）。
- 应用接口 200 / `status=success`，错误码无异常； catalina 无 `Caused by`。
- DB 变更与发布/应用回滚分别验收、分别记录，不混同；审批与备份证据齐全。
- 任一不满足 → 停止后续变更，转第 9 节。

## 9 故障处理
| 现象 | 根因（证据） | 处置 |
|---|---|---|
| 备份 failed | `pg_dump` 路径/凭据错误（脚本 pg14 vs 现场 pg16） | 核对 `pdumpath`/`PGPASSWORD` 后重试，须审批 |
| `relation already exists` / exit 255 | `GdmpTableMigrate` 中间态 | 按部署文档“重置 schema 干净迁移”（步骤待确认）；先备份，勿盲目删表 |
| pkg 迁移后样式不更新 / 值太长(128) | `app_to_logon_pic` 长度 128 | 扩到 `varchar(4000)` 后重导 pkg（运维参考） |
| 迁移后手工索引丢失 | pkg 只建默认索引（已验证） | 按 `pg_indexes` 快照重建手工索引 |
| 导入后数据不一致 | `importCIData` 非幂等或源数据不全 | 用导出 `.data` 备份恢复，重新评估（R7） |
| 磁盘被备份占满 | 保留策略/大文件 | 核对 5 天清理策略，谨慎执行 `find ... -mtime +5 -exec rm`（不可逆） |

## 10 回滚
- **DB 回滚与应用回滚分离**：旧应用不保证兼容新库结构，二者方案独立制定，不得默认互逆（R7）。
- 数据恢复：使用迁移前 `exportCIData` 的 `.data` 备份（如 `/tmp/202203281.data`）或 `pg_dump` 的 `.bak`；`importCIData` 恢复步骤依现场台账，**待确认**。
- 索引/字段回滚：按迁移前 `pg_indexes`/表结构快照逆向；DDL 逆向属不可逆操作，须审批 + 备份。
- 清理备份（`find ... | xargs rm -rf`）属不可逆，仅在确认保留策略与审批后执行。

## 11 记录和验证
- 记录维护类型、库/端口/卷、脚本与参数、备份产物路径与大小、迁移前后抽查结果、`pg_indexes` 快照、`<审批单号>`、`<变更窗口>`。
- 归档 `<现场台账路径>`、备份日志 `[Result]` 行、 catalina `Synchroning...`/无 `Caused by` 证据。
- **使用的占位符（取值来源：现场台账/交付文档）**：`<宿主机IP>`、`<DB_PORT>`、`<DB_USER>`、`<DB_PASSWORD>`、`<容器名-db>`、`<表名>`、`<日期>`、`<审批单号>`、`<变更窗口>`、`<现场台账路径>`。
- 证据缺口：现场 pg 工具路径、业务表清单与行数口径、`.data` 恢复具体流程、MongoDB 是否启用 → **待确认**。
