# 升级指南

> **证据状态**：已验证（WAR 实测 / 风险登记） · 文档推导（发版 / 运维文档） · 待确认（生产兼容性现场验证） · 不适用。
> **知识包性质**：版本化运维知识包（VERSION / manifest / SHA256），非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行升级。
> **变更基线**：生产默认只读；升级须审批；先 dry-run / 测试环境验证；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`audit/gdmp-platform-audit.md`、`gdmp-risk-register.md`、`gdmp-data-architecture.md`、`gdmp-skill-runtime-audit.md`；`content/docs/ops-reference/`；`content/product/operations/`。

## 1 升级对象与版本坐标（已验证）
- 已知 WAR：`AI_ROOT_20260902.war`（对应产品页 commit `31e1f537…`，2026-09-02）、`AI_ROOT_20261117.war`（407MB，201117 基线）。
- 1117 基线实测变化：fastjson2 2.0.64→2.0.66、hutool-all 5.8.47→5.8.48；`webmagic 0.7.3` 在 0901 基线有、1117 `WEB-INF/lib` 未见（业务是否依赖**待确认**）。
- 技术栈：Spring Boot 1.5.22 + nutz 1.r.69 + Druid 1.2.28 + Hazelcast 3.12 + Quartz 2.3 + ActiveMQ 5.16 + PostgreSQL 16.16。
- 本机无后端源码仓库（R3），无法做源码级 Diff / CI；升级兼容性以测试环境实测为准。

## 2 核心风险（R6，高；R7，高）
- 升级风险明确为：**历史应用 / 组件 / 工作流兼容性**。老应用配置、自定义组件、流程定义 / 在途实例在新版本可能异常。
- 业务数据、应用元数据、流程状态均在 DB → **DB 方案与应用（WAR / 配置）方案必须分开**，不得默认回滚 WAR 即回滚数据。

## 3 升级前（须审批）
1. 盘点应用 / 组件 / 流程清单及版本、依赖、定制表与手工索引；导出台账。
2. 备份当前应用、配置（`application-default.properties` 等）与数据库（详见 backup-restore）。
3. 在测试 / UAT 环境用目标 WAR 做兼容性验证：关键应用冒烟、组件可用、在途流程跑通、登录 / 报表 / 附件。
4. 记录当前版本号与回滚预案（应用回滚包 + DB 备份各自独立）。

## 4 升级实施（先 dry-run）
- 低峰窗口发布：WAR 放入 `webapps/ROOT`；确认配置必填 `db.type`/`druid.*`/`jms.url` 完整（缺失致 ROOT 启动失败，R5）。
- 观察启动日志至 `Started GDMPServer …` / `Start GDMP server(1.0) sucessfully`；监控 GC、DB 连接、队列、流程线程。
- 发布后执行健康检查与关键业务冒烟；异常按预案分别回滚应用或数据库。

## 5 已知升级后现象（文档记录）
- 表格不显示复选框（老系统升级）：需跑 Mongo 脚本，脚本内容**待确认**。
- 登录 400 / 密码解密失败：传输加密旧值被还原；新包 `transport-encryption.properties` 默认关闭。
- 迁移 pkg 后样式未更新（128 长度报错）：扩 `t_sys_config.app_to_logon_pic` 至 4000 后重导。
- `GdmpTableMigrate` 在中间态库可能报 `relation already exists`（exit 255 根因之一）。

## 6 AI / Skill 边界（决定性）
- 升级 WAR **不会**带来 AI Agent / Skill 运行时：WAR 无 ai-agent / mcp / skill / llm / vector / embedding 组件，无 Skill 管理页面。
- 知识包版本独立于平台版本；「知识包已安装」≠「AI 执行能力已启用」（未启用 / 受阻）。
- 不得借升级引入 MCP / 远程执行通道绕过平台权限体系。

## 7 纪律
- 全程只读观察优先；任何发布 / 回滚 / 改表须审批 + dry-run + 备份；DB 与 App 回滚分离，完成变更复盘并更新知识库。
