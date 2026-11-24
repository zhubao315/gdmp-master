---
name: gdmp-master
description: GDMP 无代码开发平台（文档站 https://219.142.87.233:9191/，产品实例 192.168.1.32:8080 / 219.142.87.231:3280）专属运维知识包。当任务涉及该平台的架构、资源评估、部署、应用/设计器/组件/工作流/数据源运维、数据库维护、性能诊断、版本升级、历史应用兼容性、备份恢复或安全审计时使用。重要：GDMP 当前没有 AI Agent/Skill 运行时，本技能是版本化运维知识包，不是可被 AI 自动加载执行的技能；不得宣称 AI 已加载或执行。所有结论必须基于证据，生产默认只读，变更需审批。
---

# gdmp-master

## 1. 技能定位

GDMP 平台的专业运维**知识包**：提供架构事实、资源评估方法、部署与运维流程、升级兼容性与回滚方案。它不是 AI 可执行的 Skill——GDMP 无原生 Skill Runtime（见 `audit/gdmp-skill-runtime-audit.md`）。

## 2. 适用范围

- 文档站：`https://219.142.87.233:9191/`（Hugo，**不是产品后台**）。
- 产品实例：`http://192.168.1.32:8080`、`http://219.142.87.231:3280`（实测 commit `31e1f537…`）。
- 已知栈：Spring Boot 1.5.22、nutz 1.r.69、Druid 1.2.28、Hazelcast 3.12、Quartz 2.3、ActiveMQ 5.16、PostgreSQL 16.16、Tomcat 9/JDK8。
- 不适用：AI-Agent 平台（请用 ai-agent-master）；未取得证据的其他 GDMP 版本。

## 3. 触发条件

用户提到：GDMP / 无代码平台 / 设计器 / 组件 / 工作流 / 应用发布 / 数据源 / PostgreSQL / Tomcat / 端口 3280-3289 / 部署 / 升级兼容性 / 备份 / 回滚 / 性能。

## 4. 工作原则

1. 证据优先：先读 `audit/`，结论标注「已验证 / 文档推导 / 待确认 / 不适用」。
2. 不宣称 AI 执行：本包只能被人或外部 Agent 作为知识参考，GDMP 不会自动加载它。
3. 生产只读：任何启停、发布、迁移、配置变更需审批；先 dry-run、先备份。
4. DB 与应用回滚分离：不得默认旧代码能直接访问新数据结构。
5. 升级必验历史应用：组件、流程、数据模型、权限的兼容性要逐项验收。
6. 不编造：无凭据、无源码的细节标「待确认」。

## 5. 环境识别

读取 `manifest.yaml` 声明版本；通过产品页面 commit-hash / 现场台账确认实际版本；版本不一致时停止高风险操作。资源基线不得以 OpenCode 主机代替 GDMP 宿主机（见 `references/resource-assessment.md`）。

## 6. 工作流程

评估 → `references/resource-assessment.md`；部署/发布 → `runbooks/install.md`、`deploy.md`、`application-publish.md`；故障 → `runbooks/troubleshooting`（在工作流/数据源/数据库 runbook 中）；升级 → `references/upgrade-guide.md`、`migration-guide.md` + `runbooks/upgrade.md`、`rollback.md`；备份 → `references/backup-restore.md`。

## 7. Reference 加载规则

入口只保留判断逻辑；按需加载 2–3 份 reference，具体操作再加载 runbook。标注「待确认」的段落不得作为操作依据。

## 8. 安全与权限

- 不使用未授权 SSH/RDP；凭据只从环境变量读取，不落盘。
- 不绕过 GDMP 权限体系；不自建与平台权限脱节的远程执行通道。
- 数据库/业务数据变更需确认；禁止未经备份的不可逆迁移。

## 9. 输出标准

给出：环境事实（含证据状态）、风险等级、前置条件、操作命令（来自 runbook，未知处用占位符并说明取值来源）、验收标准、回滚方案、遗留不确定性。明确区分「知识包已安装」与「AI 执行未启用」。

## 10. 完成条件

证据已记录、操作有审批、验收已执行、回滚方案已给出、版本兼容已校验；否则报告「未完成/受阻」。

## 11. 安装形态

`deploy/install.sh` 做版本化知识包安装：校验 SHA256 → 写入 `GDMP_KNOWLEDGE_HOME`（默认 `/oc/gdmp-site/gdmp-master/.installed/<version>`）→ 生成安装登记。它**不注册任何 AI 运行时**。
