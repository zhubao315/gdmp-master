# 安全指南

> **证据状态**：已验证（配置实测 / WAR 实测 / 错误码） · 文档推导（安全能力描述） · 待确认（现场安全配置 / 凭据） · 不适用。
> **知识包性质**：版本化运维知识包（VERSION / manifest / SHA256），非 AI 可执行 Skill；**GDMP 运行时无 AI Agent / Skill 加载器**，不得宣称 AI 执行或技能被加载。
> **变更基线**：生产默认只读；安全变更须审批；先 dry-run；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`audit/gdmp-skill-runtime-audit.md`、`gdmp-risk-register.md`、`gdmp-platform-audit.md`；`content/docs/ops-reference/_index.md`、`config/`、`frontend/`；`content/docs/faq/scenario/{admin-recovery,password-encryption}/`。

## 1 安全机制（文档 / 配置实测）
- 登录密码传输加密：AES128 对称加密、国密 SM2、4 算法（文档描述）；用户密码存储为 MD5 与 DES 的密文消息认证算法；加密字段为 DES3 三种对称算法。
- 传输加密开关 `transport-encryption.properties`：`/cms/v1/login` 字段 `account`，密码用 `transport.encryption.publicKey` RSA 加密，由 `DecodePasswordHttpServletRequestWrapper` 解密；**新包默认关闭**，还原旧值会引发登录 400 / 解密失败 / 7100。
- `security.properties`：`gdmp.security.password.encrypt`（默认 false）、`tokenAfterPrefix`、`disableToken`、`cors.allowed.origins/methods`、`headers.frame.options.*`、`contentSecurityPolicy.*`、`anonymous.files.download`、`sandbox.policyFilePath`（现场值待确认）。
- 会话：`session.timeout=60`、`session.login.limit=-1`、`session.login.fail.exceed=3`、`fail.lock.time=15`、`fail.lock.switch=0`（配置示例）。
- License / 机器码：`java -classpath ./machine_no.jar com.yr.gdmp.module.license.ShowCmd`；文件 `/root/.gdmp/license.key`；过期错误码 8001。

## 2 账号与权限（详见 permission-management）
- admin 密码见交付文档，不在公开文档明文记录；账号锁定由 admin 禁用再启用解锁；admin 丢失需停 Tomcat 后按库型删账号重建。
- 错误码：7001 登录超时、7002 非法 token、7100 权限拒绝、7200 页面元素未登录。
- 运行留痕：登录 / 操作 / 接口日志审计，流程留痕支撑审计复盘（文档描述，运行时待确认）。

## 3 决定性边界：无 AI Skill Runtime（已验证）
- WAR `AI_ROOT_20261117.war` 的 `WEB-INF/lib` 与文件名**无** ai-agent / mcp / skill / llm / vector / embedding 组件；文档站无「Agent Skill / Skill 加载 / 智能体运行时」命中；产品页无 Skill 管理页面证据；无后台 / SSH 凭据做运行时枚举 → 待确认。
- 文档「AI 能力」（自动写作、NL2SQL、OCR、智能推荐等）是**业务功能**，不是 Agent Skill Runtime（R1）。
- 本知识包安装 = 校验 VERSION / manifest / SHA256 后放入约定目录并登记版本；**明确区分「知识包已安装」与「AI 执行能力已启用」**，后者为**未启用 / 受阻**，不得伪造加载成功。

## 4 安全纪律
- 禁止借「AI 助手 / MCP / 扩展接口」绕过平台权限体系自建远程执行通道；未来若出现相关能力，须经审批、纳入平台权限体系后再评估受控集成。
- 生产默认只读；改密、解锁、安全开关、传输加密、License 变更须审批 + dry-run + 备份。
- 数据库（账号表 / 配置表）与应用（配置文件 / License）回滚分别制定，不得默认互逆（R7）。
- 凭据、密码、License 按交付文档保管，不写入公开文档或知识包明文。

## 5 审计边界
- R1（无 Skill Runtime）、R2（9191 为文档站非产品后台）、R4（无产品后台 / SSH 凭据，运行时安全配置待确认）为本主题直接相关风险。
- 公开文档中的 IP、端口、算法与配置项仅作查阅；现场生效值须在获批的只读巡检中采集后登记。
