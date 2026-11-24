# 权限管理

> **证据状态**：文档推导（安全中心功能描述） · 已验证（配置实测 / 错误码 / 故障记录） · 待确认（后台账号 / 凭据） · 不适用。
> **知识包性质**：版本化运维知识包，非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行，**禁止绕过平台权限体系自建远程执行通道**。
> **变更基线**：生产默认只读；变更须审批；先 dry-run；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`audit/gdmp-skill-runtime-audit.md`、`gdmp-risk-register.md`；`content/docs/ops-reference/_index.md`、`config/`、`troubleshooting/`；`content/docs/faq/scenario/admin-recovery/`、`account-lock/`。

## 1 权限模型（文档推导 → 待确认）
- 安全中心：统一登录、系统权限、数据安全、登录 / 操作日志审计；统一组织与权限（用户、角色、部门、岗位、数据范围）。
- 流程发起 / 查看 / 审批 / 转办分别授权，支持数据范围控制；工作流运行留痕支撑审计。
- 常用账号：`admin`（GDMP 管理员）；内容平台 `admin/zhubao`；**密码见交付文档，不在公开文档明文记录**。

## 2 错误码（已验证，文档记录）
| 码 | 含义 | 码 | 含义 |
|----|------|----|------|
| 1000 | 正常 | 7200 | 页面元素未登录 |
| 7001 | 登录超时 | 8001 | License 文件过期 |
| 7002 | 非法请求 token | 7100 | 权限拒绝 |

## 3 账号应急（文档记录，执行前须审批 + 停服评估）
- **admin 密码遗忘 / 丢失**：先停止 Tomcat → 删除数据库 admin 账号（MongoDB / PG / Oracle-DM 命令见原文）→ 重启 Tomcat → 系统默认重建 admin，初始密码 `123456`；2021-08-25 后版本初始密码在 `security.properties` 设置。
- **非 admin 账号锁定**：多次错误密码触发锁定（阈值见 `session.login.fail.exceed=3`、`fail.lock.time=15`、`fail.lock.switch=0` 配置示例）；紧急时由 admin 在「系统管理 → 账号管理」先禁用再启用解锁。
- 初始化密码另有文档 SQL：`delete from gdmp.gdmp_account where "accountNo"='admin';`（PG）/ `db.gdmp_account.remove({accountNo:"admin"})`（Mongo）→ 高风险变更，须审批、备份、单独回滚方案。

## 4 安全配置开关（配置文档，现场值待确认）
- `gdmp.security.password.encrypt`（登录 / 改密 / 加账号预加密，新包默认 false）。
- `gdmp.security.web.disableToken`、`gdmp.security.web.tokenAfterPrefix`（同机多实例区分 token）。
- `gdmp.security.web.cors.allowed.origins/methods`、`gdmp.security.web.headers.frame.options.*`、`contentSecurityPolicy.*`、`gdmp.security.authorization.anonymous.files.download`。
- `gdmp.security.manager.sandbox.policyFilePath`（沙箱策略）；`session.timeout=60`、`session.login.limit=-1`（配置示例）。
- 传输加密：`transport-encryption.properties` 控制 `/cms/v1/login`（字段 `account`，密码 RSA 加密），新包默认关闭；旧值还原会引发登录 400 / 解密失败（详见 troubleshooting）。

## 5 AI / Skill 边界（决定性）
- WAR 无 ai-agent / mcp / skill / llm / vector / embedding 组件，无 Skill 管理页面证据 → 无 AI 执行环境。
- 知识包安装仅是「校验后放目录 + 登记版本」，不赋予任何权限；不得借「AI 助手 / MCP / 扩展接口」之名绕过鉴权或建立远程执行通道。
- 未来若出现受控 AI 助手 / 扩展接口，须经审批并纳入平台权限体系后再评估集成。

## 6 纪律
- 只读查看账号 / 角色 / 日志为默认；改密、解锁、权限变更、安全开关调整须审批 + dry-run。
- DB（账号表）与应用（配置 / License）回滚分别制定；禁止默认互逆。
