# 健康检查运行手册（只读）

> GDMP 运维**知识包**流程文档；GDMP 无 AI Agent/Skill 运行时（见 `audit/gdmp-skill-runtime-audit.md`），本包不被 AI 自动加载执行。
> 本手册**默认全程只读**，不执行任何变更；如需处置，转对应 runbook 并先审批。证据状态：已验证 / 文档推导 / 待确认 / 不适用。

## 1 适用版本
- 知识包 `gdmp-master 1.0.0`（VERSION/manifest，已验证）。
- 平台：观测 commit `31e1f537…`（2026-09-02）；具体版本号**待确认**。
- 栈（WAR 实测，已验证）：Spring Boot 1.5.22、Spring Security 4.2.13、nutz 1.r.69、Druid 1.2.28、Hazelcast 3.12.13、Quartz 2.3.2、ActiveMQ 5.16.8、PostgreSQL 16.16、Tomcat 9 / JDK8。
- 验证端点：`/cms/v1/system/logo/currentSysTime` 返回 `{"status":"success"}`（192.168.0.57 部署记录，已验证）。
- 不适用：把 `:9191` 当产品健康检查对象——它是 Hugo 文档站（Caddy **:9191**，R2）。

## 2 适用环境
- 产品入口（已验证）：内网 `http://192.168.1.32:8080`、外网 `http://219.142.87.231:3280`；双实例 Windows `192.168.0.57:8080/8081`。
- 端口规则（技能，文档推导）：app `8080–8089`；DB `5432–5441`；外网 `3280–3289`；Portainer Agent `9001`。
- 日志：`/usr/local/tomcat/logs/catalina.<date>.log`、gc 日志（`setenv.sh` 中 `-Xloggc:$CATALINA_BASE/logs/gc-*.log`，已验证）。
- 错误码（运维参考已验证）：`1000` 正常、`7001` 登录超时、`7002` 非法 token、`7100` 权限拒绝、`7200` 页面元素未登录、`8001` License 过期、`success`/`fail`。
- 线程名（运维参考已验证）：`http-nio-808X-exec-*`、`ajp-nio-8019-*`、`GDMP_QUARTZ_Worker-*`、`hz.GDMP->*`、`PushService-delaySendThread`。

## 3 风险分级
- **低（本手册只读）**：所有命令均为查询，不修改运行态。
- **中（若发现异常）**：`Caused by` / `exit 255` 指向启动故障；`7001/7002/8001` 异常增多指向登录/License 问题（R5、运维参考）。
- **高（若据此变更）**：任何修复动作须审批、备份、dry-run，并区分 DB 与应用（R7）。
- 健康检查不替代运行时审计：无后台/SSH 凭据（R4），模块清单仅为文档描述、待确认。

## 4 前置条件
- 台账 `<现场台账路径>`：`<宿主机IP>`、`<APP_PORT>`、`<DB_PORT>`、`<容器名>`、`<dk>-<pg>`。
- 凭据：仅用于只读查询，仍按最小权限、从环境变量读取，不落盘（`<DB_USER>`/`<DB_PASSWORD>`）。
- 明确检查対象：单实例 / 双实例 / 10 实例编排 / 内网与外网分别检查。
- 记录检查时刻与基线，便于对比趋势；不臆测容量基线（OpenCode 主机非 GDMP 宿主机）。

## 5 诊断步骤（只读命令，来自技能/运维参考/部署记录）
```bash
# 入口与接口
curl -sS -o /dev/null -w "%{http_code}\n" http://<宿主机IP>:<APP_PORT>/
curl -sS http://<宿主机IP>:<APP_PORT>/cms/v1/system/logo/currentSysTime
curl -sS -o /dev/null -w "%{http_code}\n" http://219.142.87.231:3280/          # 外网映射（已验证基线）
# 容器与数据库
docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' | grep gdmp
docker exec <容器名-db> pg_isready -U postgres                                 # 技能：accepting connections
# 日志
grep -E "Server startup|Caused by|Start failed|Synchroning to database table" \
  /usr/local/tomcat/logs/catalina.$(date +%Y-%m-%d).log
```
- 线程面（CPU 异常时，运维参考已验证）：`top -H`、`top -Hp <PID>`、`jstack -l <十六进制线程号> > jstack.log`。
- 内存面：`jstat -gc <PID> 1000`、`jmap -histo <PID> | head -20`（详解见 `performance-tuning.md`）。

## 6 操作命令
- 本手册**无写入类操作命令**。上节即为全部命令；任何 `restart` / `docker cp` / SQL DDL 不在此执行。
- 如必须修复：按现象路由——启动失败→`restart.md`/`datasource-diagnosis.md`；工作流异常→`workflow-diagnosis.md`；数据库→`database-maintenance.md`；性能→`performance-tuning.md`；版本问题→`upgrade.md`/`rollback.md`。

## 7 预期结果
| 检查项 | 健康预期 |
|---|---|
| `/` | HTTP 200 |
| `/cms/v1/system/logo/currentSysTime` | HTTP 200 + `{"status":"success"}` |
| 外网 `:3280` | HTTP 200（已验证基线） |
| `docker ps` | gdmp 容器全部 Up |
| `pg_isready` | accepting connections |
| catalina 日志 | 有 `Server startup`，无新 `Caused by`/`Start failed` |
| 错误码 | 无 7001/7002/7100/8001 异常增长 |
| 日志/磁盘 | gc 日志正常生成；无 `Insufficient free space` 持续告警（技能注：可忽略级别） |

## 8 成功判据
- 上表所有项达标，且内网/外网/各实例结果一致 → 判健康。
- 错误码 `1000`/`success` 为主，无 `fail` 集中出现。
- 资源指标（CPU/内存/GC）趋势平稳，无长时间 `waiting`/`blocked` 线程（线程定位见运维参考）。
- 任一核心项（接口 200、容器 Up、DB accepting、无 `Caused by`）不达标 → 判不健康，转对应 runbook。

## 9 故障处理
| 现象 | 可能根因 | 路由 |
|---|---|---|
| `/` 404 | 无 ROOT 应用（安装未完成）或 ROOT 启动失败 | `install.md`；查 `Caused by` |
| `Could not resolve placeholder 'jms.url'/'druid.maxActive'` | 配置缺必填项 | `datasource-diagnosis.md` |
| 退出 255 / `relation already exists` | 启动迁移中间态 | `restart.md`、`database-maintenance.md` |
| 7001/7002/7100 增长 | 登录超时/非法 token/权限拒绝 | 运维参考：`/cms/v1/login` 用 `account` 字段 + RSA 加密（见 troubleshooting） |
| 8001 | License 过期 | 核对 `/root/.gdmp/license.key` 与 MAC，须审批 |
| CPU/内存飙高 | 线程锁竞争/内存泄漏 | `performance-tuning.md` |

## 10 回滚
- 本手册只读，无变更对象，故无回滚动作。
- 若检查过程中误触变更（不应发生），立即停止并按所涉 runbook 回滚；恢复后重新执行本检查。
- 原则：DB 与应用的恢复分开制定，不得默认互逆（R7）。

## 11 记录和验证
- 健康检查报告应含：检查时刻、`<宿主机IP>`/`<APP_PORT>`/`<DB_PORT>`、各项 HTTP 返回、容器状态、`pg_isready`、日志 `Server startup`/`Caused by` 摘要、错误码统计。
- 归档 `<现场台账路径>`；对“待确认”项如实标注，不补写未核验结论。
- **使用的占位符（取值来源：现场台账/交付文档）**：`<宿主机IP>`、`<APP_PORT>`、`<DB_PORT>`、`<容器名>`、`<容器名-db>`、`<dk>-<pg>`、`<DB_USER>`、`<DB_PASSWORD>`、`<PID>`、`<现场台账路径>`。
- 证据缺口：业务级健康指标（在线用户、流程吞吐、数据量）需现场采集建立容量模型，**待确认**。
