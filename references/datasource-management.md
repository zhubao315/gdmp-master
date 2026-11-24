# 数据源管理

> **证据状态**：已验证（WAR 驱动 / 配置实测） · 文档推导（数据基座 / 数据管理功能描述） · 待确认（运行时数据源台账） · 不适用。
> **知识包性质**：版本化运维知识包，非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行。
> **变更基线**：生产默认只读；变更须审批；先 dry-run；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`audit/gdmp-data-architecture.md`、`gdmp-architecture.md`；`content/product/data-foundation/`；`content/docs/ops-reference/config/`、`database/`；`content/docs/faq/scenario/db-migration/`。

## 1 数据管理能力（文档推导 → 待确认）
- 功能范畴：数据源、连接、数据模型、API、查询、权限、文件、导入导出（文档站模块清单）。
- 数据基座能力：多源接入（关系型 / 非关系型数据库、API、文件、IoT）、数据治理（清洗 / 标准化 / 质量校验）、建模、预计算、规则、分析服务（报表 / 大屏 / 智能问数）。
- 数据源台账（实际连接、账号、更新频率、责任人）须现场采集 → **待确认**。

## 2 数据库支持与驱动（已验证）
- 内置驱动：PostgreSQL 42.7.3、MySQL 8.2.0、Oracle ojdbc8 12.2.0.1、Kingbase 8.6.0、DM 8.1.3.140、HighGo 6.2.3、MongoDB 3.4.3（支撑多库）。
- 主库 PostgreSQL 16.16（容器卷 `gdmp_pg2` / `gdmp_pg3`）；Druid 1.2.28 连接池。
- 必填配置：`db.type`、`druid.url`、`druid.driverClassName`、`druid.username`、`druid.password`、`jms.url`；缺失致启动失败（R5）。
- Druid 连接池关键项（配置示例）：`maxActive=50`、`initialSize=5`、`maxWait=60000`、`testWhileIdle=true`、`filters=mergeStat` 等；现场值待确认。
- 文件存储：`file.storage.type=0`（本地磁盘）/ `1`（fastDFS），`upload.path`、`tmp.file.path`（配置示例）。

## 3 跨库设计约束（文档记录，迁移 / 建模时核对）
- 表名长度：MongoDB 128 字符，PostgreSQL 64 字符，Oracle / 达梦更短（GBK 15 汉字 / UTF-8 10 汉字）。
- 表名 / 属性名不能以数字开头（Oracle 报错）。
- 主键仅字符串 / 整型；Oracle 同表字符串主键长度和 ≤ 6398 字节，PostgreSQL ≤ 8191 字节。
- MongoDB 不支持 SQL 查询：源或目标为 MongoDB 时，SQL 视图及相关功能不可用。
- 内容中心同步配置 `gdmp-config.properties` 的 `gdmp.cmp.url` / `gdmp.cmp.scan.url`（示例值见原文）；账号见交付文档。

## 4 变更与回滚
- 数据源连接、模型、API 配置变更须审批，先在测试环境验证连通性与权限；生产默认只读。
- 配置变更通过 pkg / 平台迁移功能同步环境（详见 migration-guide）；手工改库与自动迁移冲突风险见 database-operations。
- 数据源配置（应用侧）与数据库内业务数据回滚**分别制定**，不得默认互逆（R7）。

## 5 边界
- 文档「NL2SQL / 智能问数」是业务功能，不是 AI Skill Runtime；不得宣称 AI 执行取数或改数。
