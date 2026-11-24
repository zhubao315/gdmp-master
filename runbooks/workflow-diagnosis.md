# 工作流诊断运行手册（只读优先）

> GDMP 运维**知识包**流程文档；GDMP 无 AI Agent/Skill 运行时（见 `audit/gdmp-skill-runtime-audit.md`），本包不被 AI 自动加载执行。
> 生产默认只读；诊断命令以查询为主，任何修复须审批、dry-run、备份；DB 与应用回滚分开。证据状态：已验证 / 文档推导 / 待确认 / 不适用。

## 1 适用版本
- 知识包 `gdmp-master 1.0.0`（VERSION/manifest，已验证）。
- 平台：观测 commit `31e1f537…`（2026-09-02）；具体版本号**待确认**。
- 工作流相关栈（WAR 实测，已验证）：Quartz 2.3.2（调度）、ActiveMQ 5.16.8（JMS 命令/事件队列）、Hazelcast 3.12.13（集群）、Groovy 2.5.23（脚本）、nutz 1.r.69（DAO）。
- 配置：`scheduler.properties`（Quartz）、`cluster.properties`（Hazelcast）、`application-default.properties` 中 `jms.*`（运维参考 config，已验证）。
- 文档模块（文档站功能描述，运行时未核验→待确认）：工作流设计/引擎/实例/节点/调度/异常/部署/版本；审批流。

## 2 适用环境
- Quartz 线程池：`org.quartz.threadPool.threadCount = 10`，`misfireThreshold = 60000`，`RAMJobStore`（scheduler.properties，已验证）。
- 线程名（运维参考已验证）：`GDMP_QUARTZ_Worker-*`（调度）、`hz.GDMP->*`（Hazelcast 集群）、`PushService-delaySendThread`（消息推送）、`http-nio-808X-exec-*`（Web）。
- JMS 队列/主题（config 已验证）：`jms.workflow.command.queue=workflow.command.queue`、`jms.scheduledTask.event.queue=scheduledTask.event.queue`、`CMS.Notify.Topic` 等；`jms.url` 指向 broker（192.168.0.57 为 `failover://(tcp://127.0.0.1:61616)...`，但该宿主 **61616 未监听**，遗留事项已验证）。
- 日志：`/usr/local/tomcat/logs/catalina.<date>.log`；工作流状态/实例数据存于数据库（数据架构已验证）。
- 不适用：AI 工作流/智能体（无运行时）；把 `:9191` 当工作流后台（R2）。

## 3 风险分级
- **高**：R6——升级后历史流程兼容性风险；流程定义/实例状态在 DB，应用与 DB 回滚不对等（R7）。
- **中**：JMS broker 缺失（192.168.0.57 未监听 61616）→ 依赖 JMS 的流程功能异常，但主流程与接口正常（遗留事项已验证）。
- **中**：集群 Hazelcast 配置（`gdmp.cluster.*`，端口 7800）影响多实例流程负载/会话。
- **中**：日志 `Start failed` / `Caused by` 指向模块启动失败，可能中断工作流引擎（源码视角）。
- 诊断默认只读；停/启流程、改调度配置、改 JMS 指向均属变更，须审批 `<审批单号>`。

## 4 前置条件
- 台账 `<现场台账路径>`：`<容器名>`、`<APP_PORT>`、`<DB_PORT>`、`<JMS_URL>`、实例/集群拓扑、流程编号/实例号（由业务方提供）。
- 明确现象：流程不发起 / 卡在节点 / 调度不执行 / 通知不到 / 版本升级后流程异常。
- 记录基线：`Server startup`、`Caused by`、`GDMP_QUARTZ_Worker-*` 线程、`pg_isready`、错误码统计。
- 凭据最小权限、不落盘；工作流实例表**表名未取得证据→待确认**，不得凭猜测写 SQL。

## 5 诊断步骤（只读命令，来自运维参考/技能）
```bash
# 1) 日志定位模块异常（按 troubleshooting 顺序：Start failed → 首个 Caused by → 对应模块）
grep -E "Start failed|Caused by|Server startup" /usr/local/tomcat/logs/catalina.$(date +%Y-%m-%d).log
# 2) 线程面：查找调度与集群线程是否存活
top -H
ps -ef | grep tomcat
# jstack -l <十六进制线程号> > jstack.log   （线程号转换见 troubleshooting；需要时由授权人员执行）
# 3) 数据库连通（工作流状态存 DB）
docker exec <容器名-db> pg_isready -U postgres
# 4) 错误码基线
curl -sS http://<宿主机IP>:<APP_PORT>/cms/v1/system/logo/currentSysTime
```
- 核对 `jms.url` 实际配置（192.168.0.57 缺 broker 为已验证反例），确认 TCP 61616 是否监听（连接探测**待确认**，无凭据）。
- 核对 `scheduler.properties` 的 `threadCount` 与集群开关 `gdmp.cluster.enabled`（默认值见 config 文档）。

## 6 操作命令
- 本手册**诊断阶段无写入命令**。上节为只读取证；下列为“需审批后、由授权人员执行”的候选动作（命令未取得现场证据，标**待确认**）：
  - 补 JMS broker 或改 `jms.url` 指向——具体 broker 部署/地址待确认（192.168.0.57 遗留事项）。
  - 调整 `scheduler.properties` / `cluster.properties`——须先备份、dry-run、审批。
  - 重启调度相关服务——走 `restart.md`，并评估对运行中流程实例的影响（影响面待确认）。
- 禁止自行重写流程实例数据或跨过平台权限体系执行“修单”（平台无 Skill Runtime，不得自建远程执行通道）。

## 7 预期结果
- 健康态：catalina 有 `Server startup`、无 `Caused by`；`GDMP_QUARTZ_Worker-*`、`hz.GDMP->*` 线程存在；DB `accepting connections`；错误码以 1000/success 为主。
- 流程发起/流转/调度/通知按业务预期；版本一致（对照 commit `31e1f537…`）。
- 若 `jms.url` 指向无 broker（如 61616 未监听），依赖 JMS 的功能异常但主接口仍 200——记录为环境限制，非平台崩溃。

## 8 成功判据
- 故障定位到具体层：配置（`jms.*`/`scheduler.*`/`cluster.*`）、DB（连通/数据）、线程资源（Quartz/Hazelcast）、或版本兼容（R6），并给出证据。
- 业务方确认流程实例恢复且无脏数据；修复动作有审批与备份记录。
- 若无法取得后台/DB 凭据完成定位 → 如实报告“受阻/待确认”，不宣称已修复。

## 9 故障处理
| 现象 | 可能根因（证据） | 处置 |
|---|---|---|
| 流程不发起 / 卡节点 | JMS broker 缺失（192.168.0.57 61616 未监听，已验证） | 补 broker 或改 `jms.url`，须审批（具体待确认） |
| 调度任务不执行 | Quartz `threadCount`/`RAMJobStore` 或线程阻塞（config 已验证） | 查 `GDMP_QUARTZ_Worker-*` 与 jstack；调参需审批 |
| 多实例流程负载异常 | Hazelcast `gdmp.cluster.*`（端口 7800）配置（config 已验证） | 核对台账拓扑，调参需审批 |
| 升级后流程报错 | 历史流程兼容性（R6） | 走 `upgrade.md`/`rollback.md`，DB 与应用分离（R7） |
| 启动即退出 255 | `Start failed`（源码视角） | 查首个 `Caused by`，转 `restart.md`/`datasource-diagnosis.md` |
| 7001/7002 登录态异常 | token/超时（运维参考） | 查登录链路与传输加密配置，非工作流本身 |

## 10 回滚
- 诊断本身无变更，无需回滚。
- 若已执行配置/重启等变更：按 `restart.md`/`rollback.md` 回退应用配置与容器；工作流实例/流程状态在 DB，**不得随应用直接回退**（R7）。
- 升级后流程兼容问题的回退：应用镜像/配置回退与 DB 方案分别制定，先备份再操作；未知步骤**待确认**。

## 11 记录和验证
- 诊断报告含：现象、时间、`<容器名>`/`<APP_PORT>`/`<DB_PORT>`、日志 `Caused by` 摘录、线程栈摘要、`jms.url`/`scheduler`/`cluster` 配置值、错误码统计、结论（已定位/待确认/受阻）。
- 归档 `<审批单号>`（若修复）、`<现场台账路径>`、业务方确认记录。
- **使用的占位符（取值来源：现场台账/交付文档）**：`<容器名>`、`<容器名-db>`、`<宿主机IP>`、`<APP_PORT>`、`<DB_PORT>`、`<JMS_URL>`、`<PID>`、`<审批单号>`、`<现场台账路径>`。
- 证据缺口：工作流实例/节点表结构、流程状态字段、JMS broker 实际部署、调度配置项运行时值 → **待确认**（无后台/DB 凭据）。
