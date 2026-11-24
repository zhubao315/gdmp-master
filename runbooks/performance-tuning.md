# 性能调优运行手册（诊断优先）

> GDMP 运维**知识包**流程文档；GDMP 无 AI Agent/Skill 运行时（见 `audit/gdmp-skill-runtime-audit.md`），本包不被 AI 自动加载执行。
> 生产默认只读；先取证后调参，任何配置/JVM/索引变更须审批（`<审批单号>`）、dry-run、备份；DB 与应用回滚分开。证据状态：已验证 / 文档推导 / 待确认 / 不适用。

## 1 适用版本
- 知识包 `gdmp-master 1.0.0`（VERSION/manifest，已验证）。
- 平台：观测 commit `31e1f537…`（2026-09-02）；版本号**待确认**。
- 栈（WAR 实测，已验证）：Spring Boot 1.5.22、Druid 1.2.28、Hazelcast 3.12.13、Quartz 2.3.2、ActiveMQ 5.16.8、PostgreSQL 16.16、Tomcat 9 / JDK8 Corretto。
- 调优依据（已文档验证）：`ops-reference/troubleshooting`（CPU/内存）、`ops-reference/config`（setenv.sh、Tomcat、Druid、Quartz、Hazelcast）、`ops-reference/database`（索引）。
- 不适用：用 OpenCode 主机资源充当 GDMP 容量基线（资源基线明确否定）；无证据的性能数字不得臆造。

## 2 适用环境
- JVM 参数文件：`/usr/local/tomcat/bin/setenv.sh`（Windows 记录为 780 字节，已验证）；GC 日志 `-Xloggc:$CATALINA_BASE/logs/gc-$(date +%y%m%d%H%M%S).log`。
- setenv.sh 已验证参数示例：
  - `-Xmn3500m -Xms5g -Xmx5g -XX:MetaspaceSize=384m -XX:MaxMetaspaceSize=384m`（config 第一组）
  - `-Xmn1500m -Xms2g -Xmx2g`（config 第二组 / 技能模板）
  - `-XX:+UseG1GC`、`-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=$CATALINA_BASE/logs`、`-XX:ErrorFile=$CATALINA_BASE/logs/hs_err_pid%p.log`
  - `-Djava.awt.headless=true -Dfile.encoding=UTF-8 -Djava.security.egd=file:/dev/./urandom`、xerces 解析器 30% 吞吐提升说明。
- Tomcat：`maxThreads` 默认 150（config 已验证）；`server.xml` 压缩 Connector（`compression="on"`、`compressionMinSize=2048`、mime 列表，技能模板已验证）。
- Druid：`maxActive=50` 等（config 已验证）；Quartz `threadCount=10`；Hazelcast `gdmp.cluster.server.port=7800`。

## 3 风险分级
- **中（诊断只读）**：`top`/`jstack`/`jstat`/`jmap -histo` 为查询，低风险；`jmap -dump` 产出大快照需磁盘空间。
- **高（调参变更）**：改 `-Xms/-Xmx/-Xmn`、GC 策略、`maxThreads`、`maxActive` 影响稳定性，须审批 `<审批单号>`、先在小环境验证、备份 setenv.sh。
- **中**：DB 索引变更会影响应用自动迁移，须备份（见 `database-maintenance.md`）。
- **中**：压缩 Connector 与 timezone 配置调整需重启才生效，走 `restart.md`。
- 默认只读；无容量基线（宿主机资源待确认），不得“凭感觉”扩容。

## 4 前置条件
- 台账 `<现场台账路径>`：`<容器名>`、`<宿主机IP>`、`<APP_PORT>`、当前 setenv.sh / server.xml / application-default.properties 快照。
- 明确现象与指标：CPU 飙高 / 内存飙高 / 响应慢 / GC 频繁 / 连接池等待，以及发生时间窗。
- 工具可用性：JDK 工具（`jstack`/`jstat`/`jmap`）、`top`；堆快照落盘路径与磁盘余量。
- 凭据最小权限、不落盘；`<PID>`、`<DumpPath>` 由授权人员现场确定。

## 5 诊断步骤（只读命令，来自运维参考 troubleshooting）
```bash
# CPU 飙高（troubleshooting 已验证流程）
top -H                              # 找高占用进程
top -Hp <PID>                       # 进程内线程占用
printf '%x\n' <线程PID>             # 线程号转 16 进制
ps -ef | grep tomcat                # 取 tomcat PID
jstack -l <十六进制线程号> > jstack.log   # 导出线程栈（troubleshooting 原文）
# 内存飙高（troubleshooting 已验证流程）
jstat -gc <PID> 1000                # GC 次数/时间，每秒
jstat -gcutil -t -h10 <PID> 2000 10000
jmap -histo <PID> | head -20        # 占用前 20 对象类型
jmap -dump:live,format=b,file=<DumpPath> <PID>   # 堆快照（需磁盘，授权执行）
```
- 判断法则（troubleshooting 已验证）：GC 频繁但回收空间正常→对象创建过快；每次回收很少→疑似内存泄漏（visualVM 离线分析 dump）。
- 线程分析：关注 `waiting on xxxxxx` 与持锁线程；线程前缀 `GDMP_QUARTZ_Worker-*`/`hz.GDMP->*`/`http-nio-808X-exec-*` 定位机制层。
- 日志面：查 gc log 是否有 full gc；查 catalina `Insufficient free space`（技能注：资源缓存告警，可忽略）。

## 6 操作命令
- **诊断阶段**：仅第 5 节只读命令。
- **调参阶段（需审批+备份+重启；参数来自 config/技能，逐条干跑）**：
  - 备份 `setenv.sh` 与 `server.xml`；修改 JVM 堆/Metaspace/GC（参考第 2 节已验证参数，取值以台账与现场压测为准）。
  - 时区：`CATALINA_OPTS="$CATALINA_OPTS -Duser.timezone=Asia/Shanghai"`（frontend 已验证）。
  - Tomcat `maxThreads`（默认 150，config 已验证）、`server.xml` 压缩 Connector（技能模板）。
  - Druid 连接池 `maxActive` 等（config 已验证）；Quartz `threadCount`；Hazelcast 集群参数。
  - DB 索引：`pg_indexes` 核查后按 `database-maintenance.md` 审批创建。
  - 生效：`docker restart <容器名>`（走 `restart.md`），逐实例验证。
- 禁止：无证据的“魔法数字”、未备份直接改配置、在生产首次应用未经验证的参数。

## 7 预期结果
- CPU/内存：定位到高占用线程与机制（Tomcat/Quartz/Hazelcast/业务）；GC 趋势平稳、无持续 full gc。
- 响应：接口 `/cms/v1/system/logo/currentSysTime` 200 / `{"status":"success"}`；错误码以 1000/success 为主。
- 调参后：`Server startup` 正常、无 `Caused by`；容器 Up；资源使用在可接受范围（阈值由台账定义，**待确认**）。
- 压缩 Connector 生效后响应体压缩、带宽下降（具体收益待现场测量）。

## 8 成功判据
- 有前后对比证据（top/jstack/jstat/gc log/接口耗时），且业务方确认体验改善或问题消失。
- 所有变更有审批、备份、回滚方案；配置与基线差异可追溯。
- DB 侧调优（索引等）与应用配置调优分别验收，不因“性能”混同为一次不可逆迁移（R7）。
- 无证据表明改善时，不宣称调优成功；继续取证或升级（转 `upgrade.md`）。

## 9 故障处理
| 现象 | 根因（证据） | 处置 |
|---|---|---|
| 线程长期 waiting/blocked | 锁竞争（troubleshooting） | 按 `waiting on` 锁地址找持锁线程，定位业务方法 |
| 频繁 full gc | 内存泄漏/分配不足（troubleshooting） | `jmap -histo`/dump + visualVM 离线分析 |
| `Insufficient free space` 告警 | Tomcat 资源缓存小（技能注） | 不影响运行，可忽略；持续则记录观察 |
| 调参后启动失败 255 | 参数不兼容/内存溢出 | 恢复备份的 setenv.sh，查 catalina `Caused by`，走 `restart.md` |
| 连接池等待/超时 | Druid `maxActive` 不足（config） | 核对连接池指标后按审批调整，避免超出 DB 承载 |
| 多实例负载不均 | Hazelcast 集群配置（config） | 核对 `gdmp.cluster.*` 与台账拓扑 |

## 10 回滚
- 配置回滚：恢复备份的 `setenv.sh` / `server.xml` / `application-default.properties`，`docker restart <容器名>`。
- DB 索引回滚：按 `pg_indexes` 快照逆向（DROP 属不可逆，须审批+备份）。
- **DB 与应用回滚分离**：性能相关的 DB 变更与应用配置回滚分别制定，不默认互逆（R7）。
- 不可逆操作前审批 + 备份；未知步骤**待确认**。

## 11 记录和验证
- 记录现象、时间窗、`<容器名>`/`<APP_PORT>`、top/jstack/jstat 摘要、gc log 关键行、配置变更前后值、`<审批单号>`、`<变更窗口>`、验证结果。
- 归档 `<现场台账路径>`、备份路径、堆快照/线程栈文件位置（注意凭据与数据敏感）。
- **使用的占位符（取值来源：现场台账/授权人员现场确定）**：`<容器名>`、`<宿主机IP>`、`<APP_PORT>`、`<PID>`、`<线程PID>`、`<DumpPath>`、`<审批单号>`、`<变更窗口>`、`<现场台账路径>`。
- 证据缺口：GDMP 宿主机资源基线、性能阈值、连接池/GC 基线值 → **待确认**。
