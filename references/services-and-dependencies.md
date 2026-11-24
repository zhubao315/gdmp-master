# 服务与依赖

> **证据状态**：已验证（HTTP 探测 / 部署记录 / WAR jar 实测） · 待确认（运行时 / 凭据缺失） · 文档推导 · 不适用。
> **知识包性质**：版本化运维知识包，非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行。
> **变更基线**：生产默认只读；变更须审批；先 dry-run；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`audit/gdmp-services.md`、`gdmp-architecture.md`、`gdmp-data-architecture.md`；`content/docs/ops-reference/tech-stack/`。

## 1 已知服务清单
| 服务 | 证据 | 状态 |
|------|------|------|
| `192.168.1.32:8080` GDMP App | HTTP 200，commit `31e1f537…` | 已验证（HTTP） |
| `219.142.87.231:3280` 外网映射 | HTTP 200 | 已验证（HTTP） |
| `192.168.0.57` gdmp-app / gdmp8081-app | 部署记录（2026-11-23） | 文档已验证，运行时待确认 |
| `192.168.0.57` gdmp-db / gdmp5433-db（postgres 16.16） | 同上 | 文档已验证，运行时待确认 |
| Portainer Agent `9001` | 私有云部署技能定义 | 待确认 |
| 文档站 `219.142.87.233:9191` | Caddy → Hugo 1314 | 已验证（非产品） |

> 本机（OpenCode 主机）无 GDMP 容器 / 8080 监听；GDMP 部署在远端宿主机。

## 2 端口与目录约定（部署技能定义）
- 宿主 app `8080–8089` ↔ 外网 `3280–3289`；数据库 `5432–5441`；Portainer Agent `9001`。
- 目录：`/home/data/pgsql/data/<port>`；`/home/docker/<dk>-<pg>`（webapps / conf / logs / bin / upload）。
- 192.168.0.57 实例：8080/5432、8081/5433；Windows 10.0.26300.9974、Docker Desktop 4.68、Engine 29.3.1。

## 3 运行时依赖组件（AI_ROOT_20261117.war jar 文件名实测）
| 组件 | 版本 | 角色 |
|------|------|------|
| Spring Boot / Spring Security | 1.5.22.RELEASE / 4.2.13.RELEASE | Web / 安全链 |
| nutz | 1.r.69 | ORM / DAO、表迁移 |
| Druid | 1.2.28 | 连接池 / SQL 解析 |
| Hazelcast | 3.12.13 | 分布式缓存 / 集群 |
| Quartz | 2.3.2 | 任务调度 |
| Groovy | 2.5.23 | 业务脚本 |
| ActiveMQ | 5.16.8 | JMS 消息 |
| fastjson2 / hutool-all / jackson | 2.0.66 / 5.8.48 / 2.17.3 | JSON / 工具 / 序列化 |
| oshi-core | 4.2.0 | 机器码（License 绑定） |
| aspose-words / cells | 21.12 / 21.11 | Word / Excel 模板预览 |
| cas-client | 3.5.0 | 单点登录 |
| thymeleaf | 2.1.6.RELEASE | 模板 |

- 数据库驱动（内置）：PostgreSQL 42.7.3、MySQL 8.2.0、Oracle ojdbc8 12.2.0.1、Kingbase 8.6.0、DM 8.1.3.140、HighGo 6.2.3、MongoDB 3.4.3。
- MQ 文档另记 Artemis 2.17.0 / Hawtio 4.14.x，与 WAR 中 ActiveMQ 5.16.8 的关系**待确认**；`webmagic 0.7.3` 见 0901 基线，1117 包 `WEB-INF/lib` 未见，业务是否依赖**待确认**。

## 4 外部系统依赖（文档推导 → 待确认）
- 集成接口文档：REST/HTTP、数据库直连、文件交换、消息队列、单点登录、自定义代码；对象含 OA/ERP/财务、统一身份、短信邮件、第三方 API。
- 内容中心同步配置 `gdmp-config.properties`：`gdmp.cmp.url` / `gdmp.cmp.scan.url`（文档示例值见原文）；账号密码见交付文档，不在公开文档明文记录。
- Git / npm / 内容平台等入口见 ops-reference；是否仍在使用**待确认**。

## 5 边界与操作纪律
- 无 AI / MCP / Skill 依赖组件；不得新增远程执行通道绕过平台权限体系。
- 探测仅只读（HTTP / 日志 / 配置快照）；端口连通性变更、容器重启须审批 + dry-run；DB 与应用回滚分离。
