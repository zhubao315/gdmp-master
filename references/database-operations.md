# 数据库运维

> **证据状态**：已验证（WAR 驱动 / 配置 / 故障记录实测） · 文档推导（运维文档 SQL、脚本） · 待确认（库内实际数据 / 凭据） · 不适用。
> **知识包性质**：版本化运维知识包，非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行。
> **变更基线**：生产默认只读；变更须审批；先 dry-run / 备份；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`audit/gdmp-data-architecture.md`；`content/docs/ops-reference/database/`；`content/docs/ops-reference/frontend/`；`content/docs/faq/scenario/db-migration/`。

## 1 基线（已验证）
- 主库 PostgreSQL 16.16（容器卷 `gdmp_pg2` / `gdmp_pg3`，驱动 42.7.3）；Druid 1.2.28；Hazelcast 3.12；Quartz 2.3；ActiveMQ 5.16。
- 业务数据、应用元数据、流程状态均在 DB → **升级 / 回滚必须分开制定 DB 与应用方案**（R7）。
- `db.type`/`druid.*`/`jms.url` 缺失致 ROOT 启动失败（R5）。

## 2 常用表与已知变更（文档记录）
| 表 | 说明 |
|----|------|
| `t_sys_config` | 系统配置；`app_to_logon_pic` 需从 128 扩到 4000（迁移后样式异常修复） |
| `t_icon` / `t_icon_data` | 子系统图标清单 / 数据 |
| `gdmp_account` | 账号表（admin 重置场景） |
| `t_gdmp_file_item` | 文件项（组件主键冲突处置） |

- 修复 SQL（文档原文，执行前须审批 + 备份）：
  `ALTER TABLE gdmp.t_sys_config ALTER COLUMN app_to_logon_pic TYPE varchar(4000);`
- 组件上传主键冲突：`delete FROM gdmp.t_gdmp_file_item where file_uri like '%component_package_path%';` → 先核对 `WHERE` 命中行、备份后执行。

## 3 自动表迁移（源码视角，文档记录）
- 应用启动时 `GdmpTableMigrate` 扫描 `com.yr` 下 `@Table` 实体：已存在 → `Daos.migration`（幂等 ALTER 补列）；缺失 → `dao.create`；日志记录 `Synchroning to database table:…`。
- 手工改表需谨慎：应用迁移只认实体定义，库中手工改动可能在重启时被对齐或报错。
- 启动 `exit 255` 常见根因之一：DB 迁移 `relation already exists`（中间态库误判），处置见部署文档「重置 schema 干净迁移」；**DB 方案与代码发布分别制定**。

## 4 索引与备份（文档脚本）
- 索引示例（文档原文，须按实际库表核对）：
  `select * from pg_indexes where tablename='…';`
  `CREATE INDEX … ON gwschema."t_…" USING btree (((data_field_map ->> '年份'::text)), …);`
- 备份脚本（文档示例，crontab 定时）：`pg_dump -h 127.0.0.1 -U gdmp -d gdmp > …bak`，`tar -zcvf` 压缩，保留 5 天（`find -mtime +5` 清理）；MongoDB 用 `mongodump` / `mongorestore`。
- 平台级数据迁移工具：`DataModelUtils.exportCIData('/path/x.data')` / `importCIData('/path/x.data')`（容器路径示例 `/usr/local/tomcat/upload/…`）；pkg 应用配置仅含默认索引，手工索引不导出。
- 内容中心同步参数见 `gdmp-config.properties`（账号见交付文档）。

## 5 纪律
- 只读查询为默认；DDL / DML / 备份恢复 / 索引变更须审批 + dry-run + 备份。
- 任何 DB 回滚与 App 回滚独立预案；禁止假设「回滚 WAR 即回滚数据」。
- 数据库密码等凭据见交付文档，不在公开文档明文记录。
