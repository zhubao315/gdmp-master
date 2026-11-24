# 应用生命周期

> **证据状态**：文档推导（应用构建 / 运营管理功能描述） · 已验证（发布 / 配置实测项） · 待确认（后台操作未核实） · 不适用。
> **知识包性质**：版本化运维知识包，非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行。
> **变更基线**：生产默认只读；变更须审批；先 dry-run / 测试环境验证；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`audit/gdmp-architecture.md`、`gdmp-data-architecture.md`；`content/product/application-builder/`、`content/product/operations/`、`content/product/devops/`。

## 1 生命周期阶段（文档推导 → 待确认）
1. 创建应用 → 2. 设计（设计器：页面 / 数据模型 / 表单）→ 3. 预览 → 4. 配置流程与权限 → 5. 发布（PC + 移动端）→ 6. 运行与监控 → 7. 版本记录 / 回滚。
- 发布：WAR 放入 Tomcat `webapps/ROOT`；无代码应用配置经版本管理进入发布流程（DevOps 文档）。
- 一套应用多端适配：桌面浏览器与移动端（文档描述，运行时待确认）。

## 2 发布与回滚（运营管理平台文档，须审批 + dry-run）
- 标准流程：① 测试环境验证应用包与数据库脚本 → ② 备份当前版本应用、配置与数据库 → ③ 低峰窗口发布并记录版本号 / 变更说明 → ④ 健康检查与关键业务冒烟 → ⑤ 异常时按预案回滚应用或数据库 → ⑥ 变更复盘、更新知识库。
- **数据库回滚与应用回滚分开制定**；应用元数据、流程状态、业务数据均在 DB，不可默认二者互逆（R7）。
- 发布包可按环境迁移（DEV/TEST/QAS/UAT/PRD），配置按环境隔离（DevOps 文档）。

## 3 发布介质与配置（已验证）
- WAR：`AI_ROOT_20260902.war`（对应 product commit `31e1f537…`，2026-09-02）、`AI_ROOT_20261117.war`（407MB）。
- `WEB-INF/classes/application-default.properties` 必填 `db.type`、`druid.*`、`jms.url`；缺失致 ROOT 启动失败（R5）。
- 表结构由应用启动自动迁移（`GdmpTableMigrate`）；手工建表 / 补列可能在重启时被对齐或报错。

## 4 已知发布后异常（文档记录）
- 迁移 pkg 后样式未更新：`值太长了(128)` → 扩 `t_sys_config.app_to_logon_pic` 至 4000 后重导（详见 database-operations）。
- 升级后表格不显示复选框：老系统升级需跑 Mongo 脚本，脚本内容**待确认**。
- 登录 400 / 密码解密失败：传输加密配置被改动时可能出现（详见 troubleshooting / security-guide）。

## 5 边界与纪律
- 应用「AI 能力」为业务功能；知识包不是 AI 可执行技能，不得宣称 AI 执行应用变更。
- 默认只读；创建 / 保存 / 发布 / 回滚须审批，先 dry-run 与测试验证；记录版本号、校验值与回滚预案。
