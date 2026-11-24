# GDMP 架构审计

- 部署：Java Web（Tomcat 9 + JDK8 Corretto 容器）+ PostgreSQL 16 容器，典型双容器/实例；Windows 宿主机用 Docker Desktop（Linux 容器），Linux 宿主机用原生 Docker。
- 端口映射规则（来自私有云部署技能）：宿主 app 8080–8089 ↔ 外网 3280–3289；数据库 5432–5441；Portainer Agent 9001。
- 目录规则：`/home/data/pgsql/data/<port>`、`/home/docker/<dk>-<pg>`（webapps/conf/logs/bin/upload）。
- 应用发布：WAR 放入 Tomcat webapps/ROOT；配置 `WEB-INF/classes/application-default.properties`（db.type / druid.* / jms.url 为必填，缺失会导致 ROOT 启动失败，见 192.168.0.57 部署记录）。
- **无 AI Agent / Skill 子系统**；扩展性通过「组件扩展接口」（文档提及接入 AI/IoT 等外部系统）实现，不等于本机 Skill Runtime。
- 源码级依赖/调用链审计：受阻（无后端仓库），标注代码推导/待确认。
