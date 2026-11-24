# 数据架构

- 主库 PostgreSQL 16.16（容器卷 `gdmp_pg2` / `gdmp_pg3`），驱动 42.7.3；支持多库（MySQL/Oracle/Kingbase/DM）。
- 连接池 Druid 1.2.28；缓存 Hazelcast 3.12；调度 Quartz 2.3；JMS ActiveMQ 5.16。
- 业务数据、应用元数据、流程状态均在数据库中，升级/回滚必须分开制定 DB 与代码方案，不得默认互逆。
- 配置项 `application-default.properties` 中 db.type / druid.* / jms.url 缺失会导致 ROOT 启动失败（已验证于 192.168.0.57 故障记录）。
