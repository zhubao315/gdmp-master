# 重启运行手册（容器/实例与服务）

> GDMP 运维**知识包**流程文档；GDMP 无 AI Agent/Skill 运行时（见 `audit/gdmp-skill-runtime-audit.md`），本包不被 AI 自动加载执行。
> 生产默认只读；重启属变更，须审批（`<审批单号>`）、先 dry-run、先备份配置与日志；DB 与应用回滚分开。证据状态：已验证 / 文档推导 / 待确认 / 不适用。

## 1 适用版本
- 知识包 `gdmp-master 1.0.0`（VERSION/manifest，已验证）。
- 平台：观测 commit `31e1f537…`（2026-09-02）；具体版本号**待确认**。
- 容器运行时：Linux 原生 Docker（技能默认宿主 `192.168.1.32`）；Windows `192.168.0.57` 为 Docker Desktop 4.68 / Engine 29.3.1（部署记录，已文档验证）。
- 已验证镜像/容器：`gdmp-app` / `gdmp8081-app`（镜像 `gdmp-app-fixed:20261123`、`gdmp8081-app-fixed:20261123`）；DB `gdmp-db` / `gdmp5433-db`（`postgres:16.16-alpine`）。
- 不适用：OpenCode 本机无 GDMP 容器/8080 监听（审计已验证）。

## 2 适用环境
- 单实例：`docker restart <容器名>`；批量：`docker restart gdmp-app gdmp8081-app`（192.168.0.57 记录 2026-11-23 最后一次重启，两套均恢复 200，已验证）。
- 编排实例（技能）：`docker restart <dk>-<pg>-gdmp-app-1`；stack 重启命令**待确认**（无证据）。
- 重启策略：Windows 两套为 `unless-stopped`；技能 stack 模板为 `restart: always`（文档推导）。
- 端口：app `8080–8089`；DB `5432–5441`；外网 `3280–3289`。
- 关键路径：`/usr/local/tomcat/logs/catalina.$(date +%Y-%m-%d).log`；`/usr/local/tomcat/webapps/ROOT/WEB-INF/classes/application-default.properties`。

## 3 风险分级
- **中**：重启触发应用启动时 `GdmpTableMigrate` 自动迁移，中间态库可能 `relation already exists` → `exit 255`（运维参考源码视角，已文档验证）。
- **中**：配置缺 `db.type`/`druid.*`/`jms.url` 时重启后 ROOT 启动失败（R5，192.168.0.57 已验证）。
- **中**：MAC/License 绑定——若容器被重建而非仅 restart，MAC 变化可能影响授权（192.168.0.57 固定 MAC `ca:ad:cf:d3:27:93`）。
- **低**：短暂服务中断；须在 `<变更窗口>` 内执行并公告。
- 默认只读；restart 属变更，须审批，`docker restart` 前先确认目标容器清单（dry-run 心智演练）。

## 4 前置条件
- 审批 `<审批单号>`、`<变更窗口>`；台账 `<现场台账路径>`（容器名、端口、卷、MAC、当前镜像）。
- 记录基线：`docker ps`、`docker inspect` 的 MAC/镜像/重启策略、最近 catalina 日志、错误码端点返回。
- 备份 `application-default.properties` 与 `setenv.sh`（不可逆改动前必须备份）。
- 确认无正在执行的关键业务/流程实例（工作流运行状态需现场台账确认，**待确认**）；否则先 draining（机制待确认）。
- 凭据不落盘：`<容器名>`、`<宿主机IP>` 取自台账。

## 5 诊断步骤（只读先行）
```bash
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}' | grep gdmp
docker inspect --format '{{.HostConfig.RestartPolicy.Name}} {{.NetworkSettings.Networks.bridge.MacAddress}}' <容器名>
grep -E "Server startup|Caused by|Synchroning to database table|Start failed" \
  /usr/local/tomcat/logs/catalina.$(date +%Y-%m-%d).log     # 日志路径已验证（容器内）
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:<APP_PORT>/cms/v1/system/logo/currentSysTime
```
- 记录重启前错误码基线（1000 正常 / 7001 登录超时 / 7002 非法 token / 7100 权限拒绝 / 8001 License 过期，运维参考已验证）。
- 查找 `Caused by` 首个根因，确认无未处理的迁移中间态再重启。

## 6 操作命令（来自部署记录/技能，执行前逐条干跑）
```bash
# 单实例 / 双实例（192.168.0.57 已验证命令）
docker restart <容器名>
docker restart gdmp-app gdmp8081-app
# 编排实例（技能）
docker restart <dk>-<pg>-gdmp-app-1
```
- 重启**不等于**重建：本手册不提供 `docker rm -f` / `docker run` 重建命令；重建会改变 MAC/卷，须按 `install.md`/`rollback.md` 单独审批。
- 等待启发（技能已验证）：WAR 解压 391MB 约 30–60s；应用启动后约 60s 再验证接口。

## 7 预期结果
- 容器状态恢复 `Up`；重启策略保持不变（`unless-stopped` / `always`）。
- `catalina.<date>.log` 出现 `Server startup`，无新的 `Caused by`；若出现 `Synchroning to database table:` 属自动迁移日志（运维参考已验证），需确认无报错。
- `/` 与 `/cms/v1/system/logo/currentSysTime` 返回 200 / `{"status":"success"}`（192.168.0.57 验证端点）。
- 错误码语义正常，License 未失效（无 `8001` 相关异常）。

## 8 成功判据
- 目标 `<容器名>` 全部 Up，`docker inspect` MAC 与台账一致。
- `currentSysTime` = 200 且 `status=success`；外网映射 `219.142.87.231:3280` 同步恢复（如适用）。
- 无 `Start failed` / `exit 255` / `relation already exists` 等启动异常；错误码无 7001/7002/8001 异常增多。
- 不满足任一项 → 转第 9 节，必要时进入 `workflow-diagnosis.md` / `datasource-diagnosis.md`。

## 9 故障处理
| 现象 | 根因 | 处置 |
|---|---|---|
| 容器退出码 255 | `ServerModuleManager` 捕获 `Start failed`，License 兜底 `System.exit(-1)`（源码视角） | 查日志首个 `Caused by` 定位模块 |
| `relation already exists` | `GdmpTableMigrate` 中间态库误判 | 按部署文档“重置 schema 干净迁移”（**具体步骤待确认**，勿自行删库） |
| `Could not resolve placeholder 'jms.url'/'druid.maxActive'` | 配置缺必填项 | 用 `.bak` 模板补全 `db.type`/`druid.*`/`jms.url` 后重启 |
| HTTP 000 / 启动慢 | 应用未就绪 | 等约 60s 重试；核对 catalina 日志 |
| License 失效（8001） | 容器重建导致 MAC 变化 | 按台账恢复原 MAC（如 `ca:ad:cf:d3:27:93`），须审批 |

## 10 回滚
- 单纯 `restart` 无配置/数据变更，无代码层回滚对象；若重启后异常，按第 9 节恢复配置再重启。
- 若已伴随配置/镜像变更，先回退配置/镜像备份，再 `docker restart <容器名>`；**DB 不随应用自动回退**（R7）。
- 涉及重建容器（非本手册范围）时走 `rollback.md`：镜像 `gdmp-app-fixed:20261123` / `gdmp8081-app-fixed:20261123`，卷 `gdmp_pg2`/`gdmp_pg3` 保持原样（192.168.0.57 回退记录）。
- 不可逆操作前须审批 + 备份；未知步骤标**待确认**。

## 11 记录和验证
- 记录重启时间、`<审批单号>`、容器名、重启前后 `docker ps`、MAC、`Server startup`/`Caused by` 行、`currentSysTime` 返回码。
- 归档 `<变更窗口>`、`<现场台账路径>`、catalina 日志片段。
- **使用的占位符（取值来源：现场台账）**：`<容器名>`、`<宿主机IP>`、`<APP_PORT>`、`<DB_PORT>`、`<dk>-<pg>`、`<审批单号>`、`<变更窗口>`、`<现场台账路径>`。
- 证据缺口：stack 级重启 API、业务 draining 流程、中间态库重置的具体步骤 → **待确认**。
