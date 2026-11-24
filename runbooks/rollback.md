# 回滚运行手册（应用 / 配置 / 数据库分离）

> GDMP 运维**知识包**流程文档；GDMP 无 AI Agent/Skill 运行时（见 `audit/gdmp-skill-runtime-audit.md`），本包不被 AI 自动加载执行。
> 生产默认只读；回滚属高风险变更，须审批（`<审批单号>`）、dry-run、**不可逆操作前先备份**；**数据库与应用回滚分开制定，不得默认互逆（R7）**。证据状态：已验证 / 文档推导 / 待确认 / 不适用。

## 1 适用版本
- 知识包 `gdmp-master 1.0.0`（VERSION/manifest，已验证）。
- 平台：观测 commit `31e1f537…`（2026-09-02）；版本号**待确认**，回滚前后以 commit-hash + 台账标识。
- 已验证回退资产（192.168.0.57 部署记录，2026-11-23）：镜像 `gdmp-app-fixed:20261123` / `gdmp8081-app-fixed:20261123`；DB 卷 `gdmp_pg2` / `gdmp_pg3`（记录明确“未改动”）；原始 MAC `ca:ad:cf:d3:27:93`。
- 已验证介质：`/data/gdmp/AI_ROOT_20260902.war`、`/data/gdmp/AI_ROOT_20261117.war`；完整配置模板 `application-default.properties.bak`。
- 不适用：把“知识包卸载”当成 GDMP 平台回滚（二者无关）；无证据的 DB 逆向迁移。

## 2 适用环境
- 应用回滚对象：容器/镜像、ROOT 目录、`WEB-INF/lib` jar、`application-default.properties`、`setenv.sh`、`server.xml`、前端 `build/*`。
- DB 回滚对象：卷（如 `gdmp_pg2`/`gdmp_pg3`）、`pg_dump` 的 `.bak`、`DataModelUtils.exportCIData` 的 `.data`（数据库运维文档已验证）。
- 容器命令环境：Linux 原生 Docker / Windows Docker Desktop（192.168.0.57）；端口 `8080–8089` ↔ `3280–3289`，DB `5432–5441`。
- 多实例：双实例（gdmp-app/gdmp8081-app）与 10 实例编排逐台回退、逐台验收。
- 不适用：OpenCode 本机（无 GDMP 容器）。

## 3 风险分级
- **高（R7）**：DB 与旧代码不兼容——旧应用可能无法读取新库结构；二者回退必须分别评估与审批。
- **高（不可逆）**：删容器（`docker rm -f`）、删卷、DROP/DELETE、`find | xargs rm`、覆盖配置均不可撤销，须先备份。
- **高（R6）**：回退后历史应用/组件/流程兼容性需重新验收，不能只验接口 200。
- **中（R5）**：配置回退时漏 `db.type`/`druid.*`/`jms.url` → ROOT 启动失败。
- **中（License）**：回退到未固定 MAC 的容器需指定原镜像/原 MAC（192.168.0.57 回退记录）。
- 回滚为高风险变更，须 `<审批单号>`、`<变更窗口>`、备份与回退演练。

## 4 前置条件
- 审批 `<审批单号>`、`<变更窗口>`；台账 `<现场台账路径>`：当前镜像/配置/MAC/卷、目标回退版本、备份位置。
- 确认备份可用且可校验：ROOT/WAR/jar/前端备份、`pg_dump` `.bak` 或 `.data`、配置快照（`# sha256sum`）。
- 明确回滚范围：仅应用？仅配置？仅 DB？还是升级整体（分别制定，见 `upgrade.md`）。
- 记录当前状态（供二次回退）：`docker ps`、`docker inspect`（镜像/MAC/重启策略）、`currentSysTime`、catalina `Caused by`、错误码。
- 凭据不落盘（`<DB_PASSWORD>` 等）；不可逆步骤逐条确认。

## 5 诊断步骤（只读先行）
```bash
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | grep gdmp
docker inspect --format '{{.Config.Image}} {{.HostConfig.RestartPolicy.Name}} {{.NetworkSettings.Networks.bridge.MacAddress}}' <容器名>
sha256sum <WAR_PATH> <JAR_PATH>                       # 备份介质与当前介质对比
curl -sS http://<宿主机IP>:<APP_PORT>/cms/v1/system/logo/currentSysTime
grep -E "Caused by|Start failed|relation already exists" /usr/local/tomcat/logs/catalina.$(date +%Y-%m-%d).log
ls -l /data/backup/                                   # 确认 .bak/.data 备份存在
```
- 核对升级记录：目标回退版本是否为 `gdmp-app-fixed:20261123` 等已验证镜像；卷 `gdmp_pg2`/`gdmp_pg3` 是否应保持原样。
- 若 DB 已被升级/迁移但未备份 → **停止回退**，先评估数据风险（R7）。

## 6 操作命令
- **应用/配置回退（沿用已验证命令，逐条干跑）**：
  - 恢复 ROOT/WAR/前端/jar（用备份或既有介质，见 `application-publish.md` 的 `scp`/`docker cp` 已验证命令）→ `docker restart <容器名>`。
  - 恢复 `application-default.properties`（基于 `.bak` 模板，含 `db.type`/`druid.*`/`jms.url`）与 `setenv.sh`、`server.xml`。
  - 容器重建回退（192.168.0.57 记录的回退方式，仅当确需回退到未固定 MAC 状态时）：
    ```cmd
    docker rm -f gdmp-app gdmp8081-app
    docker run -d --name gdmp-app --restart unless-stopped -p 8080:8080 gdmp-app-fixed:20261123
    docker run -d --name gdmp8081-app --restart unless-stopped -p 8081:8080 gdmp8081-app-fixed:20261123
    ```
    （即：相同 `docker run` 但**去掉 `--mac-address`** 并指定原镜像；192.168.0.57 回退记录已验证。执行前须审批与备份。）
- **DB 回退**：使用升级前备份（`pg_dump` `.bak` 或 `exportCIData` `.data`）恢复；**具体恢复命令在现有文档中未给出→待确认**，须由现场厂商方案提供，不得自造（见 `database-maintenance.md`）。
- **禁止**：凭猜测执行 `DROP`/`DELETE`/删除卷；把 DB 回退“顺带”在应用回退里一起做。

## 7 预期结果
- 应用回退后：`Server startup` 正常、无新 `Caused by`；`/` 与 `currentSysTime` 200 / `{"status":"success"}`。
- 配置/MAC/镜像与台账目标一致（如 `ca:ad:cf:d3:27:93` 或记录允许的“未固定 MAC”状态），License 无 8001。
- DB 保持升级前备份状态（若执行 DB 回退），卷未被误删；应用与 DB 分别验收。
- 历史应用/组件/流程在回退版本上恢复正常（R6 重新验收）。

## 8 成功判据
- 健康检查全部达标（见 `health-check.md`），错误码无异常（1000/7001/7002/7100/8001）。
- 应用与 DB 分别给出回退结论与证据，不混同；审批、备份、回退操作记录齐全。
- 兼容性清单（应用/组件/流程/数据源/权限）逐项通过（R6）。
- 无法验证 DB 回退或兼容性未通过 → 判“回退未完成/受阻”，继续处置，不宣称成功。

## 9 故障处理
| 现象 | 根因（证据） | 处置 |
|---|---|---|
| 回退后 ROOT 404 / placeholder 缺失 | 配置漏 `db.type`/`druid.*`/`jms.url`（R5） | 用 `.bak` 模板补全后重启 |
| 回退后启动 255 / `relation already exists` | 旧代码与新库结构不兼容（R7） | 停止，单独评估 DB 回退，勿反复重启 |
| 8001 License 过期 | MAC 与授权不匹配 | 按台账恢复原 MAC（如 `ca:ad:cf:d3:27:93`），须审批 |
| 容器重建后前端/jar 回退不全 | 介质版本不一致 | 核对 `WEB-INF/lib`/前端 SHA256，按备份补齐 |
| DB 回退无命令可用 | 文档未提供恢复脚本（待确认） | 暂停并申请厂商方案，禁止自造 SQL |
| 误删卷/数据 | 不可逆操作 | 立即停止，依赖备份恢复；按事故流程上报 |

## 10 回滚（回滚本身的再回退）
- 若回退后仍异常：以回退前记录的状态为基线，重新应用备份的镜像/配置/介质，**再次** `docker restart <容器名>`；这是一次新的变更，须重新审批。
- DB：若已执行 DB 回退且新状态不可用，使用同一份升级前备份的另一个副本重新恢复（前提是有多份备份；否则停止并上报）。
- 始终遵守：DB 与应用分别回退、不可逆操作前备份、无证据步骤标**待确认**。
- 原则：宁可报告“受阻”，不做未经备份/审批的破坏性尝试。

## 11 记录和验证
- 记录回退原因、范围（应用/配置/DB）、目标版本、备份位置、`<审批单号>`、`<变更窗口>`、执行人、逐项验收结果。
- 归档 `<现场台账路径>`、回退前后 `docker inspect`（镜像/MAC）、`Server startup`/无 `Caused by`、`currentSysTime` 200、错误码、兼容性验收证据。
- **使用的占位符（取值来源：现场台账/交付文档）**：`<容器名>`、`<宿主机IP>`、`<APP_PORT>`、`<DB_PORT>`、`<DB_PASSWORD>`、`<WAR_PATH>`、`<JAR_PATH>`、`<审批单号>`、`<变更窗口>`、`<现场台账路径>`。注：镜像/卷/MAC 为 192.168.0.57 已验证回退样例，实际以台账为准。
- 证据缺口：DB 恢复具体命令、知识包卸载对登记外的资源影响、各环境回退演练结果 → **待确认**。
