# GDMP 平台审计（Phase 1，2026-11-24）

> 状态：已验证 / 文档推导 / 待确认 / 不适用。生产默认只读。

## 站点识别
- `https://219.142.87.233:9191/` = **Hugo 文档站**（Caddy `:9191` → `gdmp-site` Hugo 1314），已验证。
- GDMP 产品实例：`http://192.168.1.32:8080`（内网，HTTP 200 实测）、`http://219.142.87.231:3280`（外网映射，HTTP 200 实测）；页面 commit-hash `31e1f537…`，commit-time 2026-09-02。
- 另一套 Windows 宿主机 `192.168.0.57` 双实例（8080-5432 / 8081-5433）部署记录见 `/data/gdmp/DEPLOY-192.168.0.57.md`（2026-11-23）。

## 源码仓库
- `/oc/gdmp-site` Git remote `https://ghproxy.net/https://github.com/zhubao315/gdmp.git`，HEAD `3b592e9…`；远端可达。
- 仓库内容：**仅 Hugo 文档站**，无后端源码、无 WAR 构建工程、无产品 Dockerfile/Compose/CI。→ 源码级审计受阻，不得伪造。

## 技术栈（来自文档 + WAR 实测）
- 后端 Spring Boot 1.5.22 + Spring Security 4.2 + nutz 1.r.69 + Druid + Hazelcast + Quartz + Groovy + ActiveMQ；前端 React/antd。
- 数据库 PostgreSQL 16.16（容器），另有 MySQL/Oracle/人大金仓/达梦驱动。
- WAR：`/data/gdmp/AI_ROOT_20261117.war`（407MB）、`/data/gdmp/AI_ROOT_20260902.war`。

## 决定性结论
**未发现 GDMP 存在 AI Agent 执行环境或 Skill 加载器**：WAR 的 WEB-INF/lib 与文件名中无 ai-agent / mcp / skill / llm / embedding / vector 相关组件；文档「AI 能力」指业务功能（自动写作、NL2SQL、OCR 等），不是 Agent Skill Runtime。
→ 不能把 SKILL.md 放进目录就宣称技能已被 AI 执行；只能作为「版本化运维知识包」安装并明确标注执行能力未启用。
