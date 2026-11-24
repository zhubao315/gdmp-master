# 备份与恢复

> **证据状态**：已验证（脚本 / 路径 / 配置实测） · 文档推导（运维脚本示例） · 待确认（现场备份策略 / 凭据） · 不适用。
> **知识包性质**：版本化运维知识包，非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行备份 / 恢复。
> **变更基线**：生产默认只读；备份 / 恢复须审批；先 dry-run / 恢复演练；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`audit/gdmp-data-architecture.md`、`gdmp-risk-register.md`；`content/docs/ops-reference/database/`；`content/product/operations/`；`content/docs/faq/scenario/admin-recovery/`。

## 1 备份对象清单（文档 / 实测）
| 对象 | 方式（文档示例） | 备注 |
|------|------------------|------|
| PostgreSQL 库 | `pg_dump -h 127.0.0.1 -U gdmp -d gdmp > …bak`，`tar -zcvf` 压缩 | 主库 PG 16.16，卷 `gdmp_pg2`/`gdmp_pg3` |
| MongoDB 库 | `mongodump -o …` / `mongorestore` | 如现场使用 |
| 业务数据 | `DataModelUtils.exportCIData('/path/x.data')` | 平台脚本，容器路径示例 `/usr/local/tomcat/upload/…` |
| 应用配置 | 业务应用中心备份 / pkg 包 | 配置迁移用 |
| 程序与目录 | OS 命令备份 GDMP 安装目录 | 改造回退用（迁移文档） |
| 前端静态资源 | `webapps/ROOT` 指定目录 | 更新前备份（frontend 文档） |
| License | `/root/.gdmp/license.key` | 机器码绑定，见 frontend 文档 |
| 附件 / 文件 | 文件存储目录（`file.storage.type=0` 本地 / 1 fastDFS） | 现场路径待确认 |

## 2 定时备份脚本（文档示例，须按现场核对）
- crontab（文档原文）：`0 0 * * * sh /app/scripts/sqlbak.sh`；`50 1 * * * sh /app/scripts/backup_pg.sh >> /data/backup/backup.log 2>&1`；`0 2 * * * find /data/backup/* -mtime +5 -name "*" | xargs rm -rf`（保留 5 天）；另有 dev-8081 备份条目。
- PG 脚本变量：`dbname="gdmp"`、`pguser="gdmp"`、`backpath="/data/backup"`、`pdumpath="/usr/pgsql-14/bin/"`、`export PGPASSWORD=<密码>`（示例路径与现场版本不一致时以现场为准 → 待确认）。
- MongoDB 脚本：`mongodump -o …/mongo_$(date +%Y%m%d_%H%M%S)` → `tar -czf …` → 删除临时目录。

## 3 恢复 / 回滚（分开制定）
- 数据恢复：`DataModelUtils.importCIData('/path/x.data')`；或 `pg_dump` 产物经 `pg_restore`/`psql` 导入（具体命令按现场备份格式确定 → 待确认）。
- 顺序：**先应用配置数据，再业务数据**（迁移文档）；恢复后核对索引、样式字段 `t_sys_config.app_to_logon_pic`、流程实例。
- **数据库回滚与应用（WAR / 配置）回滚分别制定预案，不得默认互逆**（R7）；业务数据、应用元数据、流程状态均在 DB。
- 恢复演练在测试环境进行；生产恢复须审批 + 先 dry-run + 保留现场快照。

## 4 已知关联场景
- admin 丢失 / 密码忘记：停 Tomcat → 删库内 admin 账号 → 重启自动重建（初始 `123456`，2021-08-25 后版本在 `security.properties` 设置）→ 改密（详见 permission-management）。
- 升级 / 迁移前必须备份应用、配置、数据库三项（operations / upgrade / migration 文档一致要求）。

## 5 纪律与边界
- 备份文件含敏感数据，按交付文档保管；密码不在公开文档明文记录。
- 知识包自身带 VERSION / manifest / SHA256，安装即校验后放目录并登记版本；**安装 ≠ AI 执行**，执行能力未启用 / 受阻。
- 所有恢复动作须审批 + dry-run；DB 与 App 回滚分离，完成后复盘更新知识库。
