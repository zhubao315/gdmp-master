# 数据源诊断运行手册（只读优先）

> GDMP 运维**知识包**流程文档；GDMP 无 AI Agent/Skill 运行时（见 `audit/gdmp-skill-runtime-audit.md`），本包不被 AI 自动加载执行。
> 生产默认只读；诊断以查询为主，改配置/DDL 须审批、dry-run、备份；DB 与应用回滚分开。证据状态：已验证 / 文档推导 / 待确认 / 不适用。

## 1 适用版本
- 知识包 `gdmp-master 1.0.0`（VERSION/manifest，已验证）。
- 平台：观测 commit `31e1f537…`（2026-09-02）；具体版本号**待确认**。
- 数据库（已验证）：主库 PostgreSQL 16.16（`postgres:16.16-alpine` 容器，卷如 `gdmp_pg2`/`gdmp_pg3`）；驱动 PostgreSQL 42.7.3，另有 MySQL 8.2.0 / Oracle ojdbc8 / 人大金仓 8.6.0 / 达梦 8.1.3.140 / 瀚高 / MongoDB 3.4.3（WAR 实测，多库支持）。
- 连接池（已验证）：Druid 1.2.28；ORM nutz 1.r.69。
- 不适用：AI/NL2SQL 数据源能力属业务功能（文档“AI 能力”章节），非 Skill 运行时。

## 2 适用环境
- 配置文件：`ROOT/WEB-INF/classes/application-default.properties`，关键必填项 `db.type`、`druid.*`、`jms.url`（运维参考 config + 192.168.0.57 故障记录，已验证）。
- 已验证连接串模板（技能 + 部署记录）：
  - Linux 编排：`jdbc:postgresql://<宿主机IP>:<DB_PORT>/gdmp?databaseMetadataCacheFields=0&currentSchema=gdmp`
  - Windows 双实例：`jdbc:postgresql://host.docker.internal:5432/gdmp?...` 与 `...:5433/gdmp?...`；`db.type=postgresql`、`druid.driverClassName=org.postgresql.Driver`、`druid.username=gdmp`。
- Druid 参数（config 已验证示例）：`maxActive=50`、`initialSize=5`、`maxWait=60000`、`minIdle=1`、`testWhileIdle=true`、`removeAbandoned=true`、`removeAbandonedTimeout=1800`。
- 端口：DB `5432–5441`；容器内 pg 端口 `5432`；外网映射 `3280–3289`（app，非 DB）。
- 常用表（数据库运维文档已验证）：`t_sys_config`（`app_to_logon_pic` 需 4000）、`t_icon`、`t_icon_data`。

## 3 风险分级
- **高（R5）**：配置缺 `db.type`/`druid.*`/`jms.url` → `Could not resolve placeholder 'druid.maxActive'` / `SQLDBCondition.matches` NPE / ROOT 启动失败（192.168.0.57 已验证）。
- **高（R7）**：数据源/DB 变更与应用回滚不对等；表结构由应用启动时 `GdmpTableMigrate` 自动维护，中间态库可能 `relation already exists` → `exit 255`（源码视角）。
- **中**：多库方言差异（Oracle/PostgreSQL/国产库）导致 SQL/驱动不匹配；`db.type` 决定 `SqlDBConfiguration`（config 源码映射已验证）。
- **中**：手工加索引/表可能被自动迁移对齐或报错（数据库运维文档已验证）。
- 诊断默认只读；改 `druid.*`、`db.type`、DDL 须审批 `<审批单号>`、先备份。

## 4 前置条件
- 台账 `<现场台账路径>`：`<宿主机IP>`、`<DB_PORT>`、`<DB_USER>`、`<DB_PASSWORD>`、`<容器名-db>`、卷名、库名/schema（如 `gdmp`）。
- 凭据最小权限、只读优先、不落盘；`<JMS_URL>` 如需核查从配置读取。
- 明确现象：ROOT 启动失败 / 连接池耗尽 / 慢查询 / 连错库 / 多库方言报错 / 自动迁移异常。
- 记录基线：配置快照、`pg_isready`、catalina 日志、gc 日志、错误码。

## 5 诊断步骤（只读命令，来自技能/运维参考/数据库运维文档）
```bash
# 1) 连通性（技能已验证）
docker exec <容器名-db> pg_isready -U postgres
docker exec <容器名-db> psql -U <DB_USER> -d gdmp -c '\dt'          # 需授权
# 2) 配置核查（只读）
cat /usr/local/tomcat/webapps/ROOT/WEB-INF/classes/application-default.properties | \
  grep -E '^(db.type|druid\.|jms.url|upload.path|tmp.file.path)'
# 3) 日志根因（troubleshooting 源码视角顺序）
grep -E "Start failed|Caused by|relation already exists|Synchroning to database table|Could not resolve placeholder" \
  /usr/local/tomcat/logs/catalina.$(date +%Y-%m-%d).log
# 4) 索引检查（数据库运维文档已验证）
# select * from pg_indexes where tablename='<表名>';
```
- 对照 192.168.0.57 反例：配置曾精简到 7 行，缺 `jms.url`、`db.type`、`druid.maxActive`，报 3 类 placeholder/NPE 错误。
- 核对 `druid.url` 端口是否对应本实例（8081 实例用 5433），避免连错库。

## 6 操作命令
- 本手册**诊断阶段无写入命令**。以下为需审批后由授权人员执行的候选动作（命令来自已验证文档，实际执行以台账为准）：
  - 补全配置：以 `application-default.properties.bak`（完整模板，192.168.0.57 已验证）为基础，覆盖 `druid.url`/`druid.username`/`druid.password`/`db.type`/`jms.url`/`upload.path`/`tmp.file.path`，再 `docker restart <容器名>`。
  - 创建索引（数据库运维文档已验证示例）：`CREATE INDEX idx_lshshjb_jlshj ON "t_历史数据表" USING btree (((data_field_map -> '记录时间')));` —— 表名/库名以现场为准，**执行前备份并审批**。
  - 手工表结构变更：谨慎——应用迁移只认实体定义，库中手工改动可能被重启对齐或报错（数据库运维文档）。
- 禁止在诊断中直接改 `db.type` 或跨库迁移数据；多库方言切换须完整方案与审批。

## 7 预期结果
- `pg_isready` = accepting connections；配置必填项齐全；ROOT 启动 `Server startup` 无 `Caused by`。
- 连接池正常（Druid 参数与台账一致），无 `Could not resolve placeholder`、无 `relation already exists`。
- 慢查询/索引问题有 `pg_indexes` 等证据支撑，不臆测。
- 错误码以 1000/success 为主，无 7100 权限拒绝（数据库权限）异常。

## 8 成功判据
- 数据源故障定位到具体层：配置（必填项/连错库）、连通（容器/端口/卷）、迁移（`relation already exists`/自动建表）、性能（连接池/索引），并给出证据。
- 业务方确认数据读写正常、页面无报错；修复动作有审批与备份记录。
- 无法取得 DB/后台凭据完成定位 → 报告“受阻/待确认”，不宣称已修复。

## 9 故障处理
| 现象 | 根因（证据） | 处置 |
|---|---|---|
| `Could not resolve placeholder 'druid.maxActive'` | 配置缺 Druid 参数（192.168.0.57 已验证） | 用 `.bak` 模板补全整套 `druid.*` |
| `SQLDBCondition.matches` NPE / `db.type` 缺失 | 配置缺 `db.type`（已验证） | 补 `db.type=postgresql`（按实际库） |
| ROOT 404 / placeholder `jms.url` | 配置缺 JMS（R5） | 补 `jms.url`，与 `restart.md` 协同 |
| `relation already exists` / exit 255 | `GdmpTableMigrate` 中间态（源码视角） | 按部署文档“重置 schema 干净迁移”（步骤待确认），勿自行删库 |
| 连错库（8081 实例连 5432） | `druid.url` 端口错 | 改为本实例端口（如 5433），审批后重启 |
| 值太长(128) / pkg 样式问题 | `t_sys_config.app_to_logon_pic` 长度不足（运维参考） | 扩为 `varchar(4000)`，走 `application-publish.md` |

## 10 回滚
- 配置回滚：恢复备份的 `application-default.properties`（含 `.bak` 原始模板），`docker restart <容器名>`。
- 索引/DDL 回滚：保留创建前 `pg_indexes`/表结构快照，按快照逆向（具体 SQL 依现场，**待确认**）。
- **DB 与应用回滚分离**：旧应用不保证兼容新库结构；任何 DB 变更回滚需单独审批与备份（R7）。
- 不可逆操作（DROP/DELETE/覆盖配置）前必须审批 + 备份。

## 11 记录和验证
- 诊断报告含：现象、时间、`<宿主机IP>`/`<DB_PORT>`/`<DB_USER>`、配置必填项核查结果、`pg_isready`、日志 `Caused by`/`relation already exists` 摘录、`pg_indexes` 证据、结论。
- 归档 `<审批单号>`（若修复）、`<现场台账路径>`、配置快照与备份位置。
- **使用的占位符（取值来源：现场台账/交付文档）**：`<宿主机IP>`、`<DB_PORT>`、`<DB_USER>`、`<DB_PASSWORD>`、`<容器名>`、`<容器名-db>`、`<JMS_URL>`、`<表名>`、`<审批单号>`、`<现场台账路径>`。
- 证据缺口：工作流/业务具体表结构、运行时连接池指标、国产库现场参数 → **待确认**。
