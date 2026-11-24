# 升级运行手册（版本/介质升级）

> GDMP 运维**知识包**流程文档；GDMP 无 AI Agent/Skill 运行时（见 `audit/gdmp-skill-runtime-audit.md`），本包不被 AI 自动加载执行。
> 生产默认只读；升级属高风险变更，须审批（`<审批单号>`）、dry-run、全量备份；**升级必须验证历史应用/组件/流程兼容性（R6）**，**DB 迁移与应用回滚分开制定（R7）**。证据状态：已验证 / 文档推导 / 待确认 / 不适用。

## 1 适用版本
- 知识包 `gdmp-master 1.0.0`（VERSION/manifest，已验证）。
- 当前平台基线：观测 commit `31e1f537…`（2026-09-02）；`manifest.yaml` 明确“未识别具体平台版本号”→ 升级前后均须以 commit-hash + 现场台账标识，**版本号待确认**。
- 已知 WAR 介质（已验证本地存在）：`/data/gdmp/AI_ROOT_20260902.war`、`/data/gdmp/AI_ROOT_20261117.war`（407MB）；技能示例 `AI_ROOT_20260824.war`。
- 组件基线（1117 实测，已验证）：Spring Boot 1.5.22、Spring Security 4.2.13、nutz 1.r.69、Druid 1.2.28、Hazelcast 3.12.13、Quartz 2.3.2、Groovy 2.5.23、fastjson2 2.0.66、ActiveMQ 5.16.8；0902 基线为 fastjson2 2.0.64、hutool 5.8.47（差异已验证）。
- 不适用：AI Skill 升级（无运行时）；源码级构建升级（无后端仓库，R3）。

## 2 适用环境
- 升级对象：WAR（`ROOT.war`/ROOT 目录）、前端 `build/*`、`WEB-INF/lib/` 下 jar、`application-default.properties`/`setenv.sh`/`server.xml`、DB 结构（自动迁移）。
- 路径（已验证）：`/home/docker/<dk>-<pg>/webapps/ROOT/`（Linux）、`/usr/local/tomcat/webapps/ROOT/`（容器）；配置模板 `application-default.properties.bak`。
- 端口与映射：`8080–8089` ↔ `3280–3289`；DB `5432–5441`。
- 环境分级（运维参考已验证）：DEV / TEST / QAS / UAT / PRD；升级路径应在 TEST/QAS/UAT 验证后再上 PRD。
- 多实例：Windows 双实例 8080/8081 与 10 实例编排须逐台/分批升级，保持 MAC（如 `ca:ad:cf:d3:27:93`）。

## 3 风险分级
- **高（R6）**：升级后历史应用/组件/流程兼容性——组件中心版本/依赖、工作流定义与实例、数据模型、权限配置可能不兼容（任务书 + 平台性质，已登记为高风险）。
- **高（R7）**：DB 迁移与应用回滚不可默认互逆；`GdmpTableMigrate` 自动迁移可能在中间态报错。
- **高（R3/R1）**：无后端源码无法做源码级 Diff/CI；无 AI 运行时，不得把“知识包版本升级”说成“AI 能力升级”。
- **中（R5）**：升级覆盖配置时丢失 `db.type`/`druid.*`/`jms.url` → ROOT 启动失败。
- **中**：MAC/License 绑定，容器重建可能改变 MAC 导致授权失效（8001）。
- 升级为高风险变更，须 `<审批单号>`、`<变更窗口>`、完整备份与回退演练。

## 4 前置条件
- 审批 `<审批单号>`、`<变更窗口>`；升级方案含：目标介质、组件清单、兼容性矩阵、回退方案（DB 与应用分别）。
- 台账 `<现场台账路径>`：当前 commit、WAR/前端/jar 版本、配置快照、容器/卷/MAC、端口、License 状态。
- 全量备份（不可逆前置）：应用 ROOT 目录与配置、数据库（`pg_dump` 或 `exportCIData` 的 `.data`，见 `database-maintenance.md`）。
- 在 TEST/QAS/UAT 完成升级演练：历史应用（设计器页面/组件）、历史组件版本、历史工作流（定义与实例）、数据源与权限逐项验证（R6）。
- 介质 SHA256 校验；凭据不落盘（`<DB_PASSWORD>` 等）。

## 5 诊断步骤（只读先行）
```bash
# 当前版本/介质基线
curl -sS http://<宿主机IP>:<APP_PORT>/cms/v1/system/logo/currentSysTime   # commit 可从页面/台账核对
sha256sum <WAR_PATH> <JAR_PATH>
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' | grep gdmp
docker inspect --format '{{.NetworkSettings.Networks.bridge.MacAddress}}' <容器名>   # MAC 基线
cat /usr/local/tomcat/webapps/ROOT/WEB-INF/classes/application-default.properties | \
  grep -E '^(db.type|druid\.|jms\.url)'
grep -E "Caused by|relation already exists|Synchroning to database table" \
  /usr/local/tomcat/logs/catalina.$(date +%Y-%m-%d).log
```
- 记录升级前错误码基线（1000/7001/7002/7100/8001）与健康检查基线（见 `health-check.md`）。
- 核对历史应用/组件/流程清单（来自台账；清单本身待确认）。

## 6 操作命令
- 升级执行**沿用已验证的发布路径**（`application-publish.md`），不臆造新命令：
  - WAR：`scp <WAR_PATH> ... ROOT.war` → `docker restart <容器名>`（技能已验证）。
  - 前端/jar：`docker cp <BUILD_PATH>/. <容器名>:/usr/local/tomcat/webapps/ROOT/`、`docker cp <JAR_PATH> ... WEB-INF/lib/` → `docker restart <容器名>`（部署记录已验证）。
  - 配置：以 `application-default.properties.bak` 为模板覆盖本实例参数，补 `db.type`/`druid.*`/`jms.url`（R5）。
- **无任何已验证的“一键升级”或版本迁移脚本**：组件兼容性处理、DB schema 升级的具体步骤在文档中**未给出→待确认**，须由现场厂商方案提供，不得自造。
- 数据库由应用启动时自动迁移（`GdmpTableMigrate`），升级后观察 `Synchroning to database table:` 日志；出现 `relation already exists` 走 `database-maintenance.md`（步骤待确认）。
- 多实例逐台升级、逐台验收，避免全量同时切换。

## 7 预期结果
- 升级后 `Server startup` 正常、无新的 `Caused by`；`/` 与 `currentSysTime` 200 / `{"status":"success"}`。
- 组件版本与介质清单一致（如 fastjson2 由 2.0.64 → 2.0.66 之类差异，以实际介质为准）。
- 历史应用（页面/设计器）、组件、工作流、数据源、权限在 UAT/PRD 逐项可用（R6 验收通过）。
- MAC 未变、License 未失效（无 8001）；配置必填项完整。

## 8 成功判据
- **兼容性验收清单全部通过**（每项有证据）：历史应用可打开与发布、历史组件可安装/依赖解析、历史工作流可发起/流转/调度、数据模型与权限正常。
- 健康检查全部达标（见 `health-check.md`），错误码无异常增长。
- DB 与应用分别验收；DB 迁移结果与记录一致，无未解释的表结构变化。
- 任一兼容性项不通过 → 判升级失败，按第 10 节回退；R6 未验收不得宣称升级成功。

## 9 故障处理
| 现象 | 根因（证据） | 处置 |
|---|---|---|
| 启动 255 / `relation already exists` | `GdmpTableMigrate` 中间态（troubleshooting） | 按 `database-maintenance.md`（步骤待确认）；先备份 |
| ROOT 404 / placeholder 缺失 | 升级覆盖配置丢 `db.type`/`druid.*`/`jms.url`（R5） | 用 `.bak` 模板补全后重启 |
| 历史应用/组件/流程异常 | 兼容性（R6） | 停止升级，回退应用并单独评估 DB |
| 页面 400 / 密码解密失败 | 传输加密配置被还原（troubleshooting：`/cms/v1/login` 用 `account` + RSA） | 核对 `transport-encryption.properties`，新包默认关闭 |
| 8001 License 过期 | MAC 变化或授权问题 | 核对 MAC 与 `/root/.gdmp/license.key`，须审批 |
| 组件 jar 版本不一致 | 缺 `gdmp-module-*` 更新（部署记录 jar 更新案例） | 核对 `WEB-INF/lib` 清单与介质 SHA256 |

## 10 回滚
- **DB 与应用回滚分离（R7）**：应用回退 = 恢复备份的 ROOT/WAR/前端/jar/配置并 `docker restart <容器名>`（镜像如 `gdmp-app-fixed:20261123`）；DB 回退 = 使用升级前 `pg_dump`/`.data` 备份单独恢复（步骤见 `database-maintenance.md`，具体待确认）。
- 不得假设旧代码可直接访问升级后的库结构；回退前分别评估兼容性并审批。
- 若升级伴随容器重建，按 `rollback.md` 恢复 MAC/镜像/卷；不可逆操作前再次备份。
- 回退后重新执行兼容性验收与健康检查，确认回到基线。

## 11 记录和验证
- 记录升级前后 commit、介质路径与 SHA256、组件版本差异、配置快照、MAC、`<审批单号>`、`<变更窗口>`、逐项兼容性验收结果、健康检查返回码。
- 归档 `<现场台账路径>`、备份位置、UAT/PRD 验收证据、`Caused by`/`Server startup` 日志摘要。
- **使用的占位符（取值来源：现场台账/介质清单）**：`<WAR_PATH>`、`<JAR_PATH>`、`<BUILD_PATH>`、`<宿主机IP>`、`<APP_PORT>`、`<容器名>`、`<DB_PASSWORD>`、`<审批单号>`、`<变更窗口>`、`<现场台账路径>`。
- 证据缺口：具体目标版本号、组件兼容性矩阵、DB schema 升级脚本、工作流迁移工具 → **待确认**（无源码/无凭据/无厂商升级文档）。
