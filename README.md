# gdmp-master

<p align="center">
  <strong>GDMP 无代码平台版本化运维知识包</strong><br>
  真实审计 · 18 篇参考 · 11 个 runbook · 升级兼容性 · 备份恢复
</p>

<p align="center">
  <img alt="Skill" src="https://img.shields.io/badge/skill-gdmp--master%20v1.0.0-7c3aed?style=flat-square">
  <img alt="Platform" src="https://img.shields.io/badge/platform-GDMP%20no--code-2563eb?style=flat-square">
  <img alt="Execution" src="https://img.shields.io/badge/AI%20execution-not%20enabled-ef4444?style=flat-square">
</p>

> 重要：GDMP **没有 AI Agent/Skill 运行时**（WAR 中无 ai-agent/mcp/skill/llm/vector/embedding 组件，文档「AI 能力」是业务功能）。本包是**版本化运维知识包**，`manifest.yaml` 明确 `native_skill_runtime: false`、`ai_execution: not_enabled`。「知识包已安装」≠「AI 执行能力已启用」。

## 一条命令安装

```bash
npm install -g github:zhubao315/gdmp-master#skill-v1.0.0
gdmp-master                      # 安装知识包到 ~/.config/opencode/skills
gdmp-master --check-only
gdmp-master --uninstall
```

免安装运行：`npx github:zhubao315/gdmp-master#skill-v1.0.0`

提示词安装：

> 请从 GitHub 仓库 `zhubao315/gdmp-master` 的 `skill-v1.0.0` 标签安装 `gdmp-master` 运维知识包，运行结构校验，并明确说明 GDMP 无 AI Skill 运行时、AI 执行未启用。

## 能力

| 领域 | 内容 |
|---|---|
| 审计 | 8 份真实审计报告（平台/架构/模块/服务/资源/数据/Skill Runtime/风险） |
| 技术栈 | Spring Boot 1.5.22、nutz、Druid、Hazelcast、Quartz、ActiveMQ、PostgreSQL 16.16、Tomcat 9 |
| 运维 | 18 references + 11 runbooks（11 节结构）：部署、应用发布、工作流/数据源/数据库诊断、性能调优、升级、回滚 |
| 升级兼容 | 历史应用/组件/流程/数据模型兼容性验收；DB 与应用回滚分离 |
| 安全 | 生产只读、变更审批、dry-run、凭据不落盘 |

## 真实验证状态

- ✅ 知识包 SHA256 校验通过；安装到 `.installed/1.0.0`；读回内容一致；登记 `ai_execution: not_enabled`。
- ⚠️ 9191 是文档站，产品实例在 `192.168.1.32:8080` / `219.142.87.231:3280`。
- ⚠️ 无 GDMP 后台/宿主机授权，运行时功能与容量基线标「待确认」；场景测试标「待执行」，未伪造通过证据。

详见 `install-verification.md` 与 `manifest.yaml`。

## 目录

```
SKILL.md / manifest.yaml / VERSION / CHANGELOG.md / README.md
audit/       8 份审计报告
references/  18 篇专业参考
runbooks/    11 个标准操作流程
scripts/     端点探测/资源采集/DB 检查清单
tests/       结构/场景/兼容/安全
deploy/      知识包 install/uninstall/verify-install
bin/         npm one-command installer
dist/        发布产物 + SHA256SUMS
```
