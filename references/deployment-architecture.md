# 部署架构

> **证据状态**：已验证（部署记录 / WAR / 配置实测） · 文档推导（部署文档） · 待确认（运行时 / 凭据） · 不适用。
> **知识包性质**：版本化运维知识包，非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行。
> **变更基线**：生产默认只读；变更须审批；先 dry-run / 测试环境验证；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`audit/gdmp-architecture.md`、`gdmp-services.md`；`content/docs/deploy-ops/deploy/`；`content/docs/ops-reference/config/`。

## 1 典型拓扑（已验证 + 文档推导）
- Java Web：Tomcat 9（`tomcat:9.0.120-jdk8-corretto` 容器）+ PostgreSQL 16.16 容器，典型双容器 / 实例。
- 容器层：应用服务层 / 容器引擎层 / 云服务器层 / 物理机层（文档分层）。
- Windows 宿主机用 Docker Desktop（Linux 容器），Linux 宿主机用原生 Docker。
- 集群：双实例 Hazelcast（基于 `gdmp.cluster.*`） + Nginx SLB（双机文档）。

## 2 端口与目录约定（部署技能定义）
- 宿主 app `8080–8089` ↔ 外网 `3280–3289`；数据库 `5432–5441`；Portainer Agent `9001`（待确认）。
- 数据卷目录 `/home/data/pgsql/data/<port>`；应用目录 `/home/docker/<dk>-<pg>`（webapps / conf / logs / bin / upload）。
- 192.168.0.57：8080/5432、8081/5433；生产映射 219.142.87.231:3280。

## 3 应用发布与配置（已验证）
- WAR 放入 `webapps/ROOT`；发布包 `AI_ROOT_20261117.war` / `AI_ROOT_20260902.war` 位于 `/data/gdmp/`。
- `WEB-INF/classes/application-default.properties` 必填 `db.type`、`druid.*`、`jms.url`；缺失致 ROOT 启动失败（192.168.0.57 故障记录，R5）。
- PG 示例：`db.type=postgresql`、`druid.url=jdbc:postgresql://<IP>:5432/gdmp?currentSchema=gdmp`、`druid.driverClassName=org.postgresql.Driver`（示例值来自容器部署文档，现场值待确认）。
- `setenv.sh`：XML 解析器 / `urandom` / `headless` / UTF-8 / G1GC / OOM HeapDump / GC 日志等参数（详见 configuration 文档）；时区可加 `-Duser.timezone=Asia/Shanghai`。
- License：机器码 `java -classpath ./machine_no.jar com.yr.gdmp.module.license.ShowCmd`；License 文件 `/root/.gdmp/license.key`（前端运维文档）。

## 4 部署模式（文档推导）
- 单机（开发 / 演示，8 核/32G/200G）、双机（约 3,000 人，应用与库分离 + 双实例 + SLB）、分布式集群（20,000–50,000+）、容器 / k8s。
- 容器集成部署要点：拉取 nginx / tomcat / activemq / postgres 镜像 → 建库建用户 → 发布部署包 → 激活授权 → 字体安装 → 导入 pkg / data。
- 启动成功标志（日志）：`Started GDMPServer in … seconds` / `Start GDMP server(1.0) sucessfully`。

## 5 数据架构与回滚边界
- 主库 PostgreSQL 16.16（容器卷 `gdmp_pg2` / `gdmp_pg3`，驱动 42.7.3）；Druid 1.2.28；Hazelcast 3.12；Quartz 2.3；ActiveMQ 5.16。
- 业务数据、应用元数据、流程状态均在数据库中；**升级 / 回滚必须分开制定 DB 与代码（应用）方案，不得默认互逆**（R7）。
- 表由应用启动时 `GdmpTableMigrate` 自动维护；手工改表需谨慎（见 database-operations）。

## 6 纪律
- 发布 / 重启 / 容器变更须审批，先测试环境 + dry-run；生产默认只读观察。
- 无 AI / MCP / Skill 组件，WAR 升级不会带来 Skill Runtime；知识包版本与平台版本独立管理。
