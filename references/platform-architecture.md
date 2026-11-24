# 平台架构

> **证据状态**：已验证（审计 / WAR 实测 / HTTP 探测） · 文档推导（Hugo 文档站） · 待确认（无产品后台 / SSH 凭据） · 不适用。
> **知识包性质**：本文件属于 GDMP **版本化运维知识包**（SKILL.md + references + runbooks + scripts，带 VERSION / manifest / SHA256），仅供人工查阅。GDMP 运行时**无 AI Agent / Skill 加载器**，不得宣称本包被 AI 加载或命令被 AI 执行；执行能力为**未启用 / 受阻**。
> **变更基线**：生产默认只读；任何变更须审批；先 dry-run / 测试环境验证；数据库与应用回滚分别制定，不得默认互逆。
> **证据来源**：`gdmp-master/audit/gdmp-platform-audit.md`、`gdmp-architecture.md`、`gdmp-skill-runtime-audit.md`；`content/product/architecture/`。

## 1 站点与实例识别（已验证）
- `https://219.142.87.233:9191/` = **Hugo 文档站**（Caddy `:9191` → gdmp-site，Hugo 1314），**不是产品后台**（风险 R2）。
- 产品实例：`http://192.168.1.32:8080`（内网，HTTP 200 实测）、`http://219.142.87.231:3280`（外网映射，HTTP 200 实测）；页面 commit `31e1f537…`，commit-time `2026-09-02`。
- Windows 宿主机 `192.168.0.57` 双实例部署记录：`/data/gdmp/DEPLOY-192.168.0.57.md`（2026-11-23），实例 8080-5432 / 8081-5433；运行时待确认。
- 远端仓库 `https://ghproxy.net/https://github.com/zhubao315/gdmp.git`（HEAD `3b592e9…`）**仅含 Hugo 文档站**，无后端源码 / WAR 工程 / CI → 源码级审计受阻（R3）。

## 2 平台分层（文档推导）
- **画布层**：页面 / APP / 报表 / 大屏（四大画布）。
- **引擎层**：数据管理 / 数据分析 / 工作流 / 平台接口（四大引擎）；工作流引擎文档称 10 大类、40 余种组件。
- **内容层**：组件 / 模板 / 应用 / 知识（内容中心）。
- **保障层**：安全中心 / 运营维护 / 扩展中心。
- 平台接口引擎文档支持 REST、WebService、MQ、JDBC、HTTP、Socket；上述均为功能描述，运行时逐项**待确认**。

## 3 运行时底座（审计 / WAR 实测）
- Java Web：Tomcat 9 + JDK8（Corretto）容器 + PostgreSQL 16.16 容器，典型双容器 / 实例。
- WAR：`/data/gdmp/AI_ROOT_20261117.war`（407MB）、`/data/gdmp/AI_ROOT_20260902.war`。
- 端口映射：宿主 app `8080–8089` ↔ 外网 `3280–3289`；数据库 `5432–5441`；Portainer Agent `9001`（Portainer 实际监听待确认）。
- 目录规则：`/home/data/pgsql/data/<port>`、`/home/docker/<dk>-<pg>`（webapps / conf / logs / bin / upload）。
- 发布：WAR 放入 `webapps/ROOT`；`WEB-INF/classes/application-default.properties` 的 `db.type` / `druid.*` / `jms.url` 为必填，缺失致 ROOT 启动失败（192.168.0.57 已验证，R5）。

## 4 决定性结论：无 AI Skill Runtime（已验证）
- WAR `AI_ROOT_20261117.war` 的 `WEB-INF/lib` 与文件名**无** ai-agent / mcp / skill / llm / vector / embedding 组件（`unzip -l` 实测，无命中）。
- 文档站全文无「Agent Skill / Skill 加载 / 智能体运行时」命中；文档「AI 能力」指业务功能（自动写作、NL2SQL、OCR 等），不是 Agent Skill Runtime。
- 产品页为 React SPA 壳，无 Skill 管理页面证据；无后台 / SSH 凭据做运行时枚举 → **待确认**。
- **结论：GDMP 当前没有可加载 Agent Skill 的 AI 执行环境。**「知识包已安装」≠「AI 执行能力已启用」；后者**未启用 / 受阻**，不得伪造加载成功。若未来出现 AI 助手 / MCP / 扩展接口，再评估受控集成，禁止绕过平台权限体系自建远程执行通道。

## 5 审计边界与风险
- 风险登记：R1 无 Skill Runtime；R2 9191 非产品；R3 无后端源码；R4 无凭据；R5 配置缺失启动失败；R6 升级兼容性；R7 DB / 应用回滚不可互逆。
- 本机（OpenCode 主机）无 GDMP 容器 / 8080 监听，GDMP 部署在远端宿主机。
- 生产操作一律先只读观察，变更须审批并先 dry-run；数据库与应用回滚分离。
