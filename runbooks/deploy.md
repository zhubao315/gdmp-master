# 部署运行手册（实例编排与对外映射）

> GDMP 运维**知识包**流程文档；GDMP 无 AI Agent/Skill 运行时（见 `audit/gdmp-skill-runtime-audit.md`），本包不被 AI 自动加载执行，“知识包已安装” ≠ “AI 执行已启用”。
> 生产默认只读；部署属变更，须审批（`<审批单号>`）、先 dry-run、先备份；DB 初始化与应用发布回滚分开。证据状态：已验证 / 文档推导 / 待确认 / 不适用。
> 安装基础环境（Docker/Portainer Agent/目录）见 `install.md`；本文件聚焦**多实例编排、对外映射与验收**。

## 1 适用版本
- 知识包 `gdmp-master 1.0.0`（VERSION/manifest，已验证）。
- 平台版本：观测 commit `31e1f537…`（2026-09-02），具体版本号**待确认**（manifest 未识别版本号）。
- 编排依据：`/oc/.opencode/skills/private-cloud-deploy/SKILL.md`“二、创建 Portainer stack（10 个实例）”“六、Nginx 反向代理”（文档推导，未现场核验→待确认）。
- 镜像（技能已验证引用）：`tomcat:9.0.120-jdk8-corretto`、`postgres:latest`/`postgres:16.16-alpine`；Windows 记录镜像 `gdmp-app-fixed:20261123`。
- 不适用：源码级部署/CI（无后端仓库，R3）；AI Skill 部署（无运行时）。

## 2 适用环境
- Portainer（技能默认 `<PORTTAINER_IP>:8089` API，环境 `<ENV_ID>`；账号见交付文档），凭据从环境变量读取。
- 10 对实例：i=0–9，`pg=5432+i`、`dk=3280+i`、`ap=8080+i`；stack 名 `{dk}-{pg}`；DB 宿主 `{pg}:5432`，app 宿主 `{ap}:8080`。
- MAC：技能模板 `fa:46:ea:d6:16:00`（用户指定，所有实例相同）；192.168.0.57 实测为 `ca:ad:cf:d3:27:93` → 两套宿主取值不同，按台账。
- 对外映射：外网 `3280–3289` → `http://192.168.1.32:8080–8089/`（nginx `fwd.conf`，`## gdmp-common` 锚点前追加）。
- 已知产品入口：`http://192.168.1.32:8080`（内网）、`http://219.142.87.231:3280`（外网），HTTP 200 已验证。

## 3 风险分级
- **高**：Portainer API 创建 stack 字段/端点用错（`Invalid stack name`）；License 与 MAC 绑定，MAC 取值错误影响授权。
- **中**：外网映射端口与目录编号错位导致访问不通；`nginx -s reload` 与 systemd 语义差异（该 nginx 非 systemd 管理）。
- **中**：bin/conf 覆盖导致 `catalina.sh` 缺失（见 install.md）。
- 部署为变更操作，须审批 `<审批单号>`、窗口 `<变更窗口>`，先在 TEST/QAS/UAT 验证再上 PRD（环境分类见运维参考）。

## 4 前置条件
- 审批与台账 `<现场台账路径>`：`PORTTAINER_IP`、`ENV_ID`、端口分配表、MAC、卷、账号来源。
- `install.md` 已完成：目录、Docker镜像加速器、Portainer Agent(9001)、bin/conf 默认文件、setenv.sh、server.xml。
- 介质 `ROOT.war` 已就位（`<WAR_PATH>`，如 `/data/gdmp/AI_ROOT_20261117.war`）并校验 SHA256。
- 凭据不落盘：Portainer admin 密码、`<DB_PASSWORD>` 由环境变量/交付文档提供。
- 对既有 stack 先备份 compose 内容（`docker stack` 待确认）与卷，再做变更。

## 5 诊断步骤（只读先行）
```bash
TOKEN=$(curl -sS -X POST http://<PORTTAINER_IP>:8089/api/auth -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"<PASSWORD>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('jwt',''))")   # 技能原文
curl -sS http://<PORTTAINER_IP>:8089/api/endpoints/<ENV_ID> -H "Authorization: Bearer $TOKEN"
docker ps | grep gdmp                                        # 基线：现存容器
ss -tlnp | grep -E ':32[89][0-9] '                           # nginx 基线监听（nginx 机）
```
- 记录 `<APP_PORT>`、`<DB_PORT>`、`<dk>-<pg>` 的目标分配，复核 `ap-8080 == pg-5432 == dk-3280 == i`。
- 若目标端口已有服务，停止编排，转现场台账确认。

## 6 操作命令（来自技能，执行前逐条干跑）
```bash
# 1) 逐实例生成 YAML（技能模板）：postgres:latest + POSTGRES_PASSWORD；gdmp-app user:root, privileged,
#    mac_address, TZ=Asia/Shanghai，挂载 webapps/conf/logs/bin/upload/tmp、/root/.gdmp、/etc/localtime、/usr/share/fonts
# 2) 通过 API 创建（注意端点与字段名）：
#    POST http://<PORTTAINER_IP>:8089/api/stacks/create/standalone/string?endpointId=<ENV_ID>
#    body: {"name":"<dk>-<pg>","stackFileContent":"<YAML>"}
#    （不要用 /standalone/file；该端点需 multipart/form-data：Name + file）
# 3) 数据库初始化（每实例容器内）：
docker exec <dk>-<pg>-gdmp-db-1 psql -U postgres -c "CREATE DATABASE gdmp;"
docker exec <dk>-<pg>-gdmp-db-1 psql -U postgres -d gdmp -c "CREATE USER gdmp WITH PASSWORD '<DB_PASSWORD>';"
docker exec <dk>-<pg>-gdmp-db-1 psql -U postgres -d gdmp -c "CREATE SCHEMA gdmp;"
docker exec <dk>-<pg>-gdmp-db-1 psql -U postgres -d gdmp -c "GRANT ALL ON SCHEMA gdmp TO gdmp;"
# 4) Web 应用：scp <WAR_PATH> root@<宿主机IP>:/home/docker/<dk>-<pg>/webapps/ROOT.war
#    docker restart <dk>-<pg>-gdmp-app-1 → 修改 application-default.properties（druid.url 用本实例 {pg}）→ 再 restart
# 5) nginx：在 /etc/nginx/conf.d/fwd.conf 的 ## gdmp-common 前追加 server{ listen 328+i; proxy_pass http://192.168.1.32:808+i; ... }
#    （技能模板含 proxy_set_header Host/X-Real-IP/X-Forwarded-For/X-Forwarded-Proto 与 buffer 配置）
nginx -t && nginx -s reload                                # 该 nginx 非 systemd 管理
```
- `druid.url` 示例（技能原文）：`jdbc:postgresql://<宿主机IP>:<DB_PORT>/gdmp?databaseMetadataCacheFields=0&currentSchema=gdmp`；必须有 `db.type`、`druid.*`、`jms.url`。

## 7 预期结果
- `docker ps | grep gdmp`：20 个容器全部 Up。
- `docker exec <dk>-<pg>-gdmp-db-1 pg_isready -U postgres`：accepting connections。
- 无 ROOT 时 `curl .../` 返回 404 属正常；部署应用后 `/` 与 `/cms/v1/system/logo/currentSysTime` 返回 200 / `{"status":"success"}`。
- `ss -tlnp | grep ':32[89][0-9] '` 看到 3280–3289 监听；外网 `http://219.142.87.231:3280/` 200（已验证基线）。

## 8 成功判据
- 逐个实例核对：内网 `<APP_PORT>` 与外网 `<dk>` 对应 same instance（`currentSysTime` 返回一致）。
- catalina 当日日志含 `Server startup` 且无 `Caused by`；ROOT 应用配置必填项齐全。
- 错误码端点语义正确（1000/7001/7002/7100/8001，见运维参考）。
- 任一实例未达标则整批不判成功，转第 9 节并按实例隔离处理。

## 9 故障处理
| 现象 | 原因（技能已验证） | 处置 |
|---|---|---|
| `Invalid stack name` | 端点/字段名错 | `/standalone/string` + `stackFileContent`，勿用 file 端点 |
| `catalina.sh: executable file not found` | 空 bin/conf 覆盖镜像 | 部署前复制镜像默认 bin/conf |
| `HTTP 000` | 应用启动慢 | 等约 60s 重试 |
| ROOT 404 / placeholder 缺失 | 配置缺 `db.type`/`druid.*`/`jms.url` | 以 `.bak` 模板补全（R5，192.168.0.57 已验证） |
| 外网端口不通 | nginx 未 reload 或锚点位置错 | `nginx -t` → `nginx -s reload`；检查 `fwd.conf` 插入位置 |
| `systemctl reload nginx` 报 invalid | 该 nginx 非 systemd 管理 | 改用 `nginx -s reload` |

## 10 回滚
- 单 stack：`POST .../api/stacks/.../delete` 的具体端点/字段**待确认**（无现场证据）；优先用 Portainer UI 删除并保留卷。
- 应用回退：替换回上一版 `ROOT.war`/配置并 `docker restart <容器>`；DB 初始化（`CREATE DATABASE/SCHEMA/USER`）**不做逆向删除**，避免误删数据（R7）。
- **DB 与应用回滚分离**：旧代码不保证兼容新库结构；DB 变更需单独方案与备份（见 `database-maintenance.md`）。
- 回滚前再次审批 + 备份卷（如 `gdmp_pg2`/`gdmp_pg3`），不可逆操作须现场确认。

## 11 记录和验证
- 记录每实例 `docker ps` 状态、`pg_isready`、`currentSysTime` 返回、`Server startup` 行、nginx `ss` 监听与 `curl` 200。
- 归档 `<审批单号>`、`<变更窗口>`、`<现场台账路径>`、stack 名清单 `{dk}-{pg}`、介质 SHA256、MAC 实测。
- **使用的占位符（取值来源：现场台账/交付文档）**：`<PORTTAINER_IP>`、`<ENV_ID>`、`<宿主机IP>`、`<APP_PORT>`、`<DB_PORT>`、`<dk>-<pg>`、`<容器名>`、`<DB_PASSWORD>`、`<PASSWORD>`、`<WAR_PATH>`、`<审批单号>`、`<变更窗口>`、`<现场台账路径>`。
- 证据缺口：Portainer ENV_ID、stack 删除 API、各实例运行时状态 → **待确认**。
