# 迁移指南

> **证据状态**：已验证（工具 / 驱动 / 字段约束来自文档与实测） · 文档推导（迁移流程） · 待确认（现场源 / 目标环境） · 不适用。
> **知识包性质**：版本化运维知识包，非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行迁移。
> **变更基线**：生产默认只读；迁移须审批；先 dry-run / 演练；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`audit/gdmp-data-architecture.md`；`content/product/domestic-compliance/migration/`；`content/docs/ops-reference/database/`；`content/docs/faq/scenario/{config-migration,db-migration}/`。

## 1 两类数据，两条路径（文档）
- **平台应用配置数据**（UI、变量、角色 / 权限、脚本等）：通过应用配置 pkg 包迁移；平台提供配置迁移功能（详见《平台配置迁移操作说明》）。
- **业务数据**：体量大，经平台脚本导出到源应用服务器本地磁盘，再拷到目标服务器导入。
- 内置驱动支撑多库：PostgreSQL 42.7.3、MySQL 8.2.0、Oracle 12.2.0.1、Kingbase 8.6.0、DM 8.1.3.140、HighGo 6.2.3、MongoDB 3.4.3（实测）。

## 2 通用步骤（文档模板）
① 备份源数据 → ② 备份程序与配置 → ③ 修改 GDMP 配置链接目标库、发布应用配置 pkg → ④ 数据同步。
- 备份用于**改造回退，务必保留**。
- 导出期间**禁止外部用户访问源应用**，防止数据变化导致不一致；确保源应用服务器磁盘空间足够。
- 导入顺序：**先应用配置数据，再业务数据**；业务数据文件放平台应用可读目录（容器示例 `/usr/local/tomcat/upload/…`）。

## 3 平台数据模型工具（文档脚本，执行前须审批 + dry-run）
- 导出：`DataModelUtils.exportCIData('/tmp/202203281.data')`（或配置按钮无参数导出 `exportCIData()`）。
- 导入：`DataModelUtils.importCIData('/tmp/202203281.data')`（容器路径示例 `'/usr/local/tomcat/upload/20230522.data'`）。
- 经管理员账号进入「脚本管理」新建脚本，输入上述语句并调试，控制台看日志 / 进度。
- 迁移完成检查： pkg 仅建默认索引，**手工在库中增加的索引不会导出**，需按索引清单重建（见 database-operations）。

## 4 跨库改造路径（文档记录）
- Oracle → 国产库 / PG：数据泵备份（回退）+ 数据模型工具备份（迁移）→ OS 命令备份安装目录 + 业务应用中心备份配置 → 改配置连目标库、发布 pkg → 同步 data。
- MongoDB → Oracle / 国产库：备份 MongoDB 安装目录（回退）+ 数据模型工具备份 → 后续同上。

## 5 跨库约束（迁移前核对，文档记录）
- 表名长度：MongoDB 128 / PG 64 / Oracle、达梦更短（GBK 15 汉字、UTF-8 10 汉字）；属性名亦有限制。
- 名称不能以数字开头（Oracle 报错）。
- 主键仅字符串 / 整型；Oracle 同表字符串主键长度和 ≤ 6398 字节，PG ≤ 8191 字节。
- MongoDB 不支持 SQL：源或目标为 MongoDB 时 SQL 视图及相关功能不可用。

## 6 已知坑位
- 迁移 pkg 后样式未更新（`值太长了(128)`）：`t_sys_config.app_to_logon_pic` 扩到 4000 后重导（SQL 见 database-operations）。
- 手工改表 / 手工索引与 `GdmpTableMigrate` 自动迁移冲突 → 迁移后核对启动日志。

## 7 纪律与边界
- 迁移期间生产默认只读；所有导出 / 导入 / 改配置须审批 + 备份 + 演练；DB 与应用回滚独立预案（R7）。
- 「智能问数 / AI」是业务功能，不是 AI Skill Runtime；不得借迁移引入 AI 执行或远程通道。
