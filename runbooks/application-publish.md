# 应用发布运行手册（WAR / 前端 / jar / pkg）

> GDMP 运维**知识包**流程文档；GDMP 无 AI Agent/Skill 运行时（见 `audit/gdmp-skill-runtime-audit.md`），本包不被 AI 自动加载执行。
> 生产默认只读；发布属变更，须审批（`<审批单号>`）、先 dry-run、先备份；DB（pkg/data 导入）与应用发布回滚分开。证据状态：已验证 / 文档推导 / 待确认 / 不适用。

## 1 适用版本
- 知识包 `gdmp-master 1.0.0`（VERSION/manifest，已验证）。
- 平台：观测 commit `31e1f537…`（2026-09-02）；具体版本号**待确认**。
- 已知 WAR 介质（已验证本地存在）：`/data/gdmp/AI_ROOT_20261117.war`（407MB）、`/data/gdmp/AI_ROOT_20260902.war`；技能示例 `AI_ROOT_20260824.war`。
- 前端与 jar 更新实测（2026-11-23，已验证）：`/oc/gdmp/build.zip`（136MB，`build/` 下 4935 文件）、`gdmp-module-new-page-element-1.1.0-SNAPSHOT.jar`；另 `gdmp-module-db-adapter-1.1.0-SNAPSHOT.jar`（介质清单）。
- 组件版本基线（WAR 1117 实测，已验证）：Spring Boot 1.5.22、nutz 1.r.69、Druid 1.2.28、Hazelcast 3.12.13、Quartz 2.3.2、ActiveMQ 5.16.8。
- 不适用：AI Skill 发布（无运行时）；源码构建发布（无后端仓库，R3）。

## 2 适用环境
- Linux 编排实例：webapps 目录 `/home/docker/<dk>-<pg>/webapps/ROOT/`（技能）；Windows 容器：`/usr/local/tomcat/webapps/ROOT/`（部署记录）。
- 配置：`ROOT/WEB-INF/classes/application-default.properties`（模板 `.bak` 同目录）；jar 目录 `ROOT/WEB-INF/lib/`；日志 `/usr/local/tomcat/logs/`。
- 发布方式（已验证）：`scp` WAR → `docker restart` 解压 → `docker cp` 前端/jar → `docker restart`；Windows 用 xfreerdp 目录重定向 `/drive:gdmp,/oc/gdmp` → `\\tsclient\gdmp` → `robocopy`。
- 数据/pkg 导入：`DataModelUtils.exportCIData` / `importCIData`（数据库运维文档，已文档验证）。
- 端口：app `8080–8089`；外网 `3280–3289`。

## 3 风险分级
- **高**：pkg 导入只建默认索引，手工索引不导出（数据库运维文档已验证）；导入前必须扩容 `t_sys_config.app_to_logon_pic`（128→4000），否则报“值太长了(128)”样式不更新。
- **高**：版本兼容性——升级后历史应用/组件/流程兼容性风险（R6）；发布前必须逐项验收（见 `upgrade.md`）。
- **中**：ROOT 启动失败若配置了缺 `db.type`/`druid.*`/`jms.url`（R5）。
- **中**：组件上传“主键冲突”残留记录（`t_gdmp_file_item`），需清理后重传（运维参考）。
- 发布为变更，须审批 `<审批单号>`、窗口 `<变更窗口>`，先备份 ROOT 与 DB。

## 4 前置条件
- 审批 `<审批单号>`、`<变更窗口>`、台账 `<现场台账路径>`；记录当前 WAR/前端/jar 版本与 SHA256 基线。
- 介质 SHA256 校验（部署记录中 index.html、asset-manifest.json.gz、chunk.css、jar 均有 SHA-256 记录，可复用比对方法）。
- 备份：现有 `ROOT` 目录、`application-default.properties`、`WEB-INF/lib/`、数据库（见 `database-maintenance.md`）。
- 确认 `<WAR_PATH>` / `<BUILD_PATH>` / `<JAR_PATH>` 来源可信；凭据不落盘。
- 对多实例（如 8080/8081、10 实例）逐台发布并逐台验收，不建议同时全量切换。

## 5 诊断步骤（只读先行）
```bash
# 基线接口与容器
curl -sS http://<宿主机IP>:<APP_PORT>/cms/v1/system/logo/currentSysTime
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' | grep gdmp
# 当前介质指纹（示例字段来自 192.168.0.57 记录）
sha256sum <WAR_PATH> <JAR_PATH>
# 组件冲突残留（只读 SQL，表名来自运维参考，需确认库名）
# select * from gdmp.t_gdmp_file_item where file_uri like '%component_package_path%';
```
- 读取当前 `application-default.properties` 是否含 `db.type`/`druid.*`/`jms.url`，记录为基线。
- 核对页面 commit-hash（`31e1f537…` 为观测基线），确认发布前后差异可追溯。

## 6 操作命令（来自部署记录/技能/数据库运维文档，逐条干跑）
```bash
# 1) WAR 发布（技能）
scp <WAR_PATH> root@<宿主机IP>:/home/docker/<dk>-<pg>/webapps/ROOT.war
docker restart <dk>-<pg>-gdmp-app-1
ls /home/docker/<dk>-<pg>/webapps/ROOT/WEB-INF/classes/            # 确认解压
# 2) 前端更新（运维参考 frontend / 部署记录）
# 运维参考示例：cd /app/tomcat/webapps/ROOT/ && rm -rf *.css *.html* apks assets/ css/ ... modules/ build.log favicon.*
# 部署记录实测：build/* → /usr/local/tomcat/webapps/ROOT/；jar → ROOT/WEB-INF/lib/
docker cp <BUILD_PATH>/. <容器名>:/usr/local/tomcat/webapps/ROOT/
docker cp <JAR_PATH> <容器名>:/usr/local/tomcat/webapps/ROOT/WEB-INF/lib/
docker restart <容器名>
# 3) 数据/pkg 导入（容器环境，数据库运维文档已验证）
# println DataModelUtils.exportCIData('/tmp/202203281.data')
# println DataModelUtils.importCIData('/usr/local/tomcat/upload/20230522.data')
```
- 迁移前若报“对于可变字符类型来说，值太长了(128)”：`ALTER TABLE gdmp.t_sys_config ALTER COLUMN app_to_logon_pic TYPE varchar(4000);`（运维参考已验证，**执行需审批**）。

## 7 预期结果
- `Server startup` 正常、无新的 `Caused by`；`/` 与 `currentSysTime` 返回 200 / `{"status":"success"}`（192.168.0.57 验证）。
- 新前端 chunk 文件 HTTP 200；对外 `index.html` SHA-256 与介质一致（部署记录验证方法）。
- 发布后 `application-default.properties` 必填项完整，配置未被覆盖丢失。
- pkg 导入后样式正常，无 `值太长了(128)` 报错；手工索引需在目标库重建（pkg 不导出手工索引）。

## 8 成功判据
- 逐实例：接口 200 + `status=success` + 新资源 SHA256 匹配 + catalina 无 `Caused by` + 错误码无异常（1000/success）。
- 历史应用/组件/流程兼容性逐项验收通过（R6）：发布的 WAR/前端/jar 与既有应用设计器、组件版本、工作流定义均可正常运行（逐项清单待现场台账确认）。
- DB 变更（若有 pkg 导入）单独验收，与应用发布分别判定；不混为一谈。
- 任一实例未达标 → 停止批量发布，转第 9 节。

## 9 故障处理
| 现象 | 原因 | 处置 |
|---|---|---|
| ROOT 404 / placeholder 缺失 | 配置缺 `db.type`/`druid.*`/`jms.url`（R5） | 用 `.bak` 模板补全后重启 |
| 组件上传“主键冲突” | 残留 `t_gdmp_file_item` 记录 | `delete FROM gdmp.t_gdmp_file_item where file_uri like '%component_package_path%';` 后重传（运维参考，需审批） |
| pkg 迁移后样式不更新 / 值太长(128) | `t_sys_config.app_to_logon_pic` 长度不足 | 扩到 `varchar(4000)` 后重导 pkg（运维参考） |
| 新 chunk 404 | 前端文件未完整替换 | 核对 `build/*` 替换清单与 SHA256，重发 |
| 发布后历史应用/流程异常 | 兼容性问题（R6） | 停止发布，按 `rollback.md` 回退应用并单独评估 DB |

## 10 回滚
- 应用回滚：用备份的 ROOT / WAR / jar / 前端资源恢复，`docker restart <容器名>`；校验 `Server startup` 与 SHA256 回到基线。
- DB（pkg/data 导入）回滚：**与应用回滚分离**，`importCIData` 通常非幂等且导入前备份（如 `/tmp/202203281.data`）需保留；恢复方案依台账与备份，具体步骤**待确认**，不得默认可逆（R7）。
- 不可逆操作（覆盖 ROOT、删记录、ALTER TABLE）前必须审批 + 备份。
- 组件主键冲突清理（`DELETE`）对数据有破坏性，仅针对确认残留记录，执行前备份该表。

## 11 记录和验证
- 记录发布对象（WAR/前端/jar/pkg）、介质路径与 SHA256、目标容器/端口、`<审批单号>`、`<变更窗口>`、逐实例验收结果。
- 归档：发布前备份位置、配置快照、`Server startup`/无 `Caused by` 证据、接口 200、新资源 HTTP 与 SHA256。
- **使用的占位符（取值来源：现场台账/介质清单）**：`<WAR_PATH>`、`<BUILD_PATH>`、`<JAR_PATH>`、`<宿主机IP>`、`<APP_PORT>`、`<容器名>`、`<dk>-<pg>`、`<审批单号>`、`<变更窗口>`、`<现场台账路径>`。注：WAR/介质本地路径为已验证样例，实际以台账为准。
- 证据缺口：历史应用/组件/流程兼容性清单、pkg 备份路径 → **待确认**。
