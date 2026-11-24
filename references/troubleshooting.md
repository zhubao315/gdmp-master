# 故障排查

> **证据状态**：已验证（配置 / 错误码 / 故障记录） · 文档推导（排故脚本 / 源码视角） · 待确认（生产现场） · 不适用。
> **知识包性质**：版本化运维知识包，非 AI 可执行 Skill；GDMP 无 AI Agent / Skill 运行时，不得宣称 AI 执行排障。
> **变更基线**：生产默认只读（先取证）；变更须审批；先 dry-run；数据库与应用回滚分别制定、不得默认互逆。
> **证据来源**：`content/docs/ops-reference/troubleshooting/`、`database/`、`frontend/_index.md`；`content/docs/faq/scenario/`；`audit/gdmp-risk-register.md`。

## 1 错误码速查（已验证）
| 码 | 含义 | 码 | 含义 |
|----|------|----|------|
| 1000 | 正常 | 7200 | 页面元素未登录 |
| 7001 | 登录超时 | 8001 | License 文件过期 |
| 7002 | 非法请求 token | success/fail | 成功 / 失败 |
| 7100 | 权限拒绝 | | |

## 2 CPU / 内存（文档排故流程）
- CPU 飙高（只读取证）：`top -H` → `top -Hp <PID>` → `printf '%x\n' <线程PID>` → `jstack -l <十六进制线程号> > jstack.log` → 找长期 waiting / blocked 与持锁线程 → 定位业务方法。
- 内存飙高：`jstat -gc <PID> 1000`、`jstat -gcutil -t -h10 <PID> 2000 10000`、`jmap -histo <PID> | head -20`；GC 频繁但回收正常→对象创建快；回收很少→疑似泄漏 → `jmap -dump:live,format=b,file=/home/myheapdump.hprof <PID>` + visualVM 离线分析。
- 日志：查看 tomcat 日志目录 gc log，出现 **Full GC** 分析内存泄漏 / 分配；`ps -ef | grep tomcat` + `jmap -dump` 后 `tar -czvf` 压缩转出。

## 3 启动失败 / exit 255（源码视角）
- 链路：`ServerModuleManager.start(ctx)` → 任一 `*Module.start` 抛异常 → `ServerMain$1` 捕获 → License 兜底校验 → 命中需处理状态 → `System.exit(-1)` → 容器退出 255。
- 排查顺序：`Start failed` → 首个 `Caused by` → 对应模块。
- 常见根因一：DB 迁移 `relation already exists`（中间态库误判）→ 部署文档「重置 schema 干净迁移」。
- 常见根因二：多模块数据兼容（如数据流读定制表缺列）→ 国产化适配改造方案。
- 配置缺失：`application-default.properties` 的 `db.type`/`druid.*`/`jms.url` 缺失致 ROOT 启动失败（192.168.0.57 已验证）。

## 4 登录 / 组件 / 升级 / 队列（文档处置，执行前须审批 + dry-run）
- **登录 400 / 解密失败**：`/cms/v1/login` 字段为 `account`，密码需 `transport.encryption.publicKey` RSA 加密；明文 → `BadBlockException`；DTO 装配失败 → HTTP 400；传输加密被还原旧值会触发，新包默认关闭。
- **组件上传主键冲突**：`delete FROM gdmp.t_gdmp_file_item where file_uri like '%component_package_path%';`（先核对命中、备份）。
- **迁移后样式未更新**：`CaseMessage=错误: 对于可变字符类型来说，值太长了(128)` → `ALTER TABLE gdmp.t_sys_config ALTER COLUMN app_to_logon_pic TYPE varchar(4000);` 后重导 pkg。
- **升级后表格不显示复选框**：老系统升级需跑 Mongo 脚本，脚本内容**待确认**。
- **定时脚本崩溃后仍执行**：清理 ActiveMQ `scheduledTask.event.queue`（Hawtio `/admin/queues.jsp`，文档示例 admin/admin）→ 会丢消息，须评估并审批。
- **admin 密码遗忘 / 账号锁定**：见 permission-management（停 Tomcat 删账号重建 / admin 禁用再启用解锁）。

## 5 线程名对照（文档）
`http-nio-808X-exec-*` / `ajp-nio-8019-AsyncTimeout`（Tomcat）、`GDMP_QUARTZ_Worker-*`（Quartz）、`hz.GDMP->*`（Hazelcast）、`PushService-delaySendThread`（消息推送）。

## 6 纪律
- 取证优先只读；`jstack` / `jmap` / 日志导出只读，dump 可能含敏感数据，按交付文档保管。
- 删除记录、清队列、改表、改配置均须审批 + 备份 + dry-run；DB 与 App 回滚独立预案（R7）。
- 无 AI Skill Runtime，不得让「AI 自动排障」参与生产变更；本包仅提供人工处置参考。
