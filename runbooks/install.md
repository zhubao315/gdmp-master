# 安装运行手册（GDMP 平台与知识包）

> 本文件是 GDMP 运维**知识包**中的流程文档。GDMP 无 AI Agent/Skill 运行时（决定性结论见 `audit/gdmp-skill-runtime-audit.md`）；本包不会被 AI 自动加载执行。**“知识包已安装” ≠ “AI 执行已启用”**。
> 生产默认只读；安装/初始化属变更，须审批（`<审批单号>`）、先 dry-run、先备份；数据库初始化与应用发布回滚分开制定。证据状态标注：已验证 / 文档推导 / 待确认 / 不适用。

## 1 适用版本
- 知识包版本：`gdmp-master 1.0.0`（`VERSION` / `manifest.yaml`，已验证）。
- 目标平台：文档与 WAR 观测 commit `31e1f537…`（2026-09-02）；`manifest.yaml` 明确“未识别具体平台版本号，以 commit-hash 记录”→ **版本号待确认**。
- 已验证介质：`/data/gdmp/AI_ROOT_20261117.war`（407MB）、`/data/gdmp/AI_ROOT_20260902.war`；另有 `Fonts.zip`、`postgres-latest.tar.gz`、`tomcat-9.0.118-jdk8-corretto.tar.gz`（部署记录，已验证存在）。
- 技术栈（WAR 实测 + 部署记录，已验证）：Spring Boot 1.5.22、PostgreSQL 16.16、Tomcat 9 / JDK8 Corretto、Druid/Hazelcast/Quartz/ActiveMQ。
- 安装子进程：`/oc/.opencode/skills/private-cloud-deploy/SKILL.md`（已验证存在，覆盖 Docker+Portainer Agent+目录+DB+Tomcat+WAR）。
- 不适用：无产品后端源码仓库（`/oc/gdmp-site` 仅 Hugo 文档站），不可做源码级构建/CI（R3）。

## 2 适用环境
- Linux 宿主机（技能默认 `192.168.1.32`，`root` + `sshpass`；文档推导，**未取得凭据→待确认**）；Windows 宿主机 `192.168.0.57`（Docker Desktop 4.68 / Engine 29.3.1，Linux 容器，双实例，已文档验证）。
- 端口映射（技能定义，文档推导）：app 宿主 `8080–8089` ↔ 外网 `3280–3289`（nginx 反代）；DB 宿主 `5432–5441`；Portainer Agent `9001`；docker 目录 `dk = pg − 2152`。
- 目录规则：`/home/data/pgsql/data/<port>`；`/home/docker/<dk>-<pg>/{webapps,conf,logs,bin}`，`bin/upload`、`bin/tmp` 挂载到容器。
- Windows 双实例实测：`gdmp-app`(8080:8080 / 5432, 卷 `gdmp_pg2`) 与 `gdmp8081-app`(8081:8080 / 5433, 卷 `gdmp_pg3`)；镜像 `gdmp-app-fixed:20261123`，MAC 固定 `ca:ad:cf:d3:27:93`。
- 明确排除：`https://219.142.87.233:9191/` 是 Hugo 文档站（Caddy **:9191**），**不是产品后台**（R2）；OpenCode 本机不运行 GDMP。

## 3 风险分级
- **高**：无 GDMP 后台/SSH 合法凭据（R4）、无后端源码（R3）→ 安装后无法运行时枚举验证；License 按 MAC 激活，MAC 处理错误会导致授权失效。
- **中**：`application-default.properties` 缺 `db.type` / `druid.*` / `jms.url` 导致 ROOT 启动失败（192.168.0.57 已验证，R5）。
- **中**：空 `bin`/`conf` 目录挂载覆盖镜像 `catalina.sh` / `server.xml`，启动报 `catalina.sh: executable file not found`（技能“关键坑”）。
- **中**：Docker Hub 被墙、get.docker.com 连不上导致安装中断（技能常见问题）。
- 默认只读；安装属变更操作，须 `<审批单号>` 与 `<变更窗口>`，逐条干跑后再执行。

## 4 前置条件
- 审批：`<审批单号>`、`<变更窗口>`；现场台账 `<现场台账路径>`（宿主机管理 IP、账号来源、端口分配、MAC/License、卷名）。
- 介质就位并校验 SHA256；`<WAR_PATH>` 默认 `/data/gdmp/AI_ROOT_20261117.war`（已验证本地样例）。
- 凭据从环境变量读取、不落盘：`<PASSWORD>`（SSH）、`<DB_PASSWORD>`、`<DB_USER>`、`<JMS_URL>` 取自台账/交付文档，禁止写死。
- 确认目标端口未被占用；对既有实例先备份配置与数据卷（见 `database-maintenance.md`），再执行不可逆步骤。
- 平台版本与知识包声明版本不一致时**停止高风险操作**，先更新台账。

## 5 诊断步骤（只读先行）
```bash
sshpass -p '<PASSWORD>' ssh -o StrictHostKeyChecking=no root@<宿主机IP> \
  'cat /etc/os-release | grep PRETTY_NAME'                     # 连接测试（技能，已验证命令）
docker info --format '{{.DockerRootDir}} {{json .RegistryConfig.Mirrors}}'   # data-root 与加速器
docker ps | grep gdmp                                           # 现存实例清单
ss -tlnp | grep -E ':32[89][0-9] '                             # nginx 外网端口监听（在 nginx 机）
```
- Windows 侧在任何改动前读取原始 MAC：`docker inspect --format '{{.NetworkSettings.Networks.bridge.MacAddress}}' gdmp-app`（192.168.0.57 记录为 `ca:ad:cf:d3:27:93`）。
- 记录 `curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:<APP_PORT>/` 的基线（无 ROOT 时 404 属正常，技能已验证）。

## 6 操作命令（来自 private-cloud-deploy 技能，执行前逐条干跑）
```bash
# 目录规划（每个 pg 端口 5432–5441，dk=pg-2152）
for p in $(seq 5432 5441); do mkdir -p /home/data/pgsql/data/$p; d=$((p-2152));
  mkdir -p /home/docker/$d-$p/webapps /home/docker/$d-$p/conf /home/docker/$d-$p/logs \
           /home/docker/$d-$p/bin/upload /home/docker/$d-$p/bin/tmp; done
# Docker（阿里云源 + daemon.json data-root=/home/docker-data + registry-mirrors，技能原文），systemctl enable --now docker
# Portainer Agent：docker run -d --name portainer_agent --restart=always -p 9001:9001 \
#   -v /var/run/docker.sock:/var/run/docker.sock -v /var/lib/docker/volumes:/var/lib/docker/volumes -v /:/host portainer/agent:latest
# 防止 bin/conf 覆盖（stack 创建前）：docker run --rm -v .../bin:/dst/bin -v .../conf:/dst/conf \
#   --entrypoint sh tomcat:9.0.120-jdk8-corretto -c "cp -a /usr/local/tomcat/bin/. /dst/bin/ && cp -a /usr/local/tomcat/conf/. /dst/conf/"
# DB 初始化：docker exec <容器> psql -U postgres -c "CREATE DATABASE gdmp;"; CREATE USER gdmp ...; CREATE SCHEMA gdmp; GRANT ALL ...
# setenv.sh（JVM 参数见 performance-tuning.md）、server.xml 压缩 Connector（技能模板），chmod 0755
# WAR：scp <WAR_PATH> root@<宿主机IP>:/home/docker/<dk>-<pg>/webapps/ROOT.war ; docker restart <容器>
# 配置：编辑 .../ROOT/WEB-INF/classes/application-default.properties（基于 .bak 模板），补 db.type/druid.*/jms.url
```
- 知识包安装（**非 AI 加载**）：`export GDMP_KNOWLEDGE_HOME=/oc/gdmp-site/gdmp-master/.installed`（默认 `/oc/gdmp-site/gdmp-master/.installed/<version>`）→ `./deploy/install.sh` → `./deploy/verify-install.sh`（README/SKILL，已验证）。

## 7 预期结果
- 20 个容器（10 DB + 10 App）全部 Up；`pg_isready -U postgres` 全部 accepting connections。
- `curl .../cms/v1/system/logo/currentSysTime` 返回 `200` 且 `{"status":"success"}`（部署记录验证端点）。
- catalina 日志出现 `Server startup`，无 `Caused by`；ROOT 目录含 `WEB-INF/classes/application-default.properties`。
- 知识包：`verify-install.sh` 通过，安装登记写入 `GDMP_KNOWLEDGE_HOME`；不产生任何 AI 运行时注册。

## 8 成功判据
- 内网 `http://<宿主机IP>:<APP_PORT>/` 与外网 `http://219.142.87.231:3280/` HTTP 200（已验证基线）。
-  MAC/License：容器 MAC 与台账一致；License 文件 `/root/.gdmp/license.key`（路径已验证）。
- 错误码语义正确：`1000` 正常、`7001` 登录超时、`7002` 非法 token、`7100` 权限拒绝、`8001` License 过期（运维参考已验证）。
- 以上任一不满足 → 不判成功，转第 9 节。

## 9 故障处理
| 现象 | 原因（技能已验证） | 处置 |
|---|---|---|
| `get.docker.com` 连不上 | 外网受限 | 用阿里云 `docker-ce` 仓库 |
| `docker pull` 超时 | Docker Hub 被墙 | 配置 `registry-mirrors` |
| `catalina.sh: executable file not found` | 空 bin/conf 覆盖镜像 | 先从镜像复制默认 bin/conf |
| `Invalid stack name` | 端点/字段名错 | 用 `/api/stacks/create/standalone/string` + `stackFileContent` |
| `HTTP 000` | 应用启动慢 | 等待约 60s 重试 |
| `Insufficient free space` 告警 | Tomcat 资源缓存小 | 不影响运行，可忽略 |
| ROOT 404 / `Could not resolve placeholder 'jms.url'/'druid.maxActive'` | 配置精简缺必填项（192.168.0.57 已验证） | 用 `application-default.properties.bak` 模板重建，补全 `db.type`/`druid.*`/`jms.url` |

## 10 回滚
- 知识包：`./deploy/uninstall.sh`，删除 `<GDMP_KNOWLEDGE_HOME>` 下登记；不影响 GDMP 运行态。
- 平台安装回滚：停止新建容器 → 恢复安装前备份的镜像/配置/卷；数据卷（如 `gdmp_pg2`/`gdmp_pg3`）若未改动则保持原样（192.168.0.57 回退记录）。
- **DB 与应用回滚分离**：应用镜像/容器可独立回退，数据库卷初始化/迁移需单独制定方案，不得默认互逆（R7）。
- 不可逆步骤（删容器、改卷）前须再次审批与备份；本文件不提供未经证据的回滚命令，具体以现场台账为准（待确认）。

## 11 记录和验证
- 安装后执行 `./deploy/verify-install.sh`；记录 `docker ps`、`pg_isready`、`currentSysTime` 返回码与 catalina `Server startup` 行。
- 归档：`<审批单号>`、`<变更窗口>`、介质 SHA256、台账 `<现场台账路径>`、端口/MAC 实测值。
- **使用的占位符（取值来源：现场台账/交付文档，禁止臆造）**：`<宿主机IP>`、`<APP_PORT>`、`<DB_PORT>`、`<dk>-<pg>`、`<容器名>`、`<DB_USER>`、`<DB_PASSWORD>`、`<PASSWORD>`、`<JMS_URL>`、`<WAR_PATH>`、`<审批单号>`、`<变更窗口>`、`<现场台账路径>`、`<PORTTAINER_IP>`、`<ENV_ID>`。
- 证据缺口：平台具体版本号、运行时用户/流程状态、Portainer Agent 实际监听 → **待确认**，取得授权后补审计。
