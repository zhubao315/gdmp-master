# 性能优化

> **证据状态**：已验证（配置实测 / 部署基线） · 文档推导（JVM / 容量文档） · 待确认（生产实测指标 / 凭据） · 不适用。
> **知识包性质**：版本化运维知识包，非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行。
> **变更基线**：生产默认只读（先测量）；调参须审批；先 dry-run / 测试环境验证；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`content/docs/ops-reference/config/`、`troubleshooting/`、`tech-stack/`；`content/docs/deploy-ops/deploy/deployment-modes/`；`audit/gdmp-resource-baseline.md`。

## 1 先测量，后调参（已验证边界）
- 本机（OpenCode 主机，128 CPU / 499GiB / 7×RTX4090）**不运行 GDMP**，不得作为 GDMP 性能基线；生产指标须现场采集（待确认）。
- 采集项：CPU / 内存 / 磁盘 / inode、JVM 堆与 GC 日志、PG 连接数与慢查询、Hazelcast 成员、Quartz 线程、ActiveMQ 队列深度。
- 压测在测试环境进行；生产默认只读观察。

## 2 JVM / Tomcat 参数（配置文档原文，现场值待确认）
- `setenv.sh`：JDK 自带 Xerces（文档称提升约 30% XML 解析吞吐）、`-Djava.security.egd=file:/dev/./urandom`、`-Djava.awt.headless=true -Dfile.encoding=UTF-8 -XX:-OmitStackTraceInFastThrow`、`-XX:+UseG1GC`、`ErrorFile`、`HeapDumpOnOutOfMemoryError`、GC 日志（按日期命名）。
- 堆大小示例：文档两处分别为 `-Xmn3500m -Xms5g -Xmx5g` 与 `-Xmn1500m -Xms2g -Xmx2g`，Metaspace 384m；容器文档建议 `-Xms/-Xmx` 为物理内存 1/4、`-Xmn` 约 `-Xmx` 的 75% → 以现场实际配置为准，勿照抄。
- Tomcat `maxThreads` 默认 150（同时处理任务数）；时区可加 `-Duser.timezone=Asia/Shanghai`。

## 3 中间件与调度
- Druid 1.2.28：`maxActive=50`、`initialSize=5`、`maxWait=60000`、`testWhileIdle=true`、`removeAbandoned=true/1800`（配置示例）→ 按连接数实测调整。
- Hazelcast 3.12.13：`gdmp.cluster.enabled=false`（默认单实例）、`mode=0`（嵌入）、`server.port=7800`、`heartbeat=500ms`、`work.thread.size=2`（配置示例）；双机文档为双实例集群 + Nginx SLB。
- Quartz 2.3.2：`threadCount=10`、`RAMJobStore`、`misfireThreshold=60000`（scheduler.properties 示例）。

## 4 数据与查询
- 索引：按实际慢查询在 JSON 字段（`data_field_map ->> '字段'`）上建 btree 表达式索引（SQL 示例见 database-operations）；手工索引不随 pkg 导出，迁移后需重建。
- 数据基座文档：预计算加速（高频查询提前计算并缓存）、分层建模（贴源 / 明细 / 汇总 / 应用层）、指标统一；属功能描述，运行时效果待确认。
- 前端静态资源更新只删指定目录（见 frontend 运维原文），生产执行前备份。

## 5 排故联动（详见 troubleshooting）
- CPU 飙高：`top -H` → `top -Hp <PID>` → `printf '%x'` → `jstack -l` 分析 waiting / blocked。
- 内存飙高：`jstat -gc`、`jmap -histo`、`jmap -dump` + visualVM；GC 日志中 Full GC 频繁 → 内存泄漏 / 分配问题。
- 线程名定位：`http-nio-808X-exec-*`（Tomcat）、`GDMP_QUARTZ_Worker-*`（Quartz）、`hz.GDMP->*`（Hazelcast）、`PushService-delaySendThread`（消息推送）。

## 6 纪律
- 所有参数变更须审批 + dry-run；先回滚预案（应用配置与 DB 分别制定）再动生产。
- 文档「高并发 / 大容量」为能力描述，非本机实测；不得据此宣称已验证的性能或 AI 能力。
