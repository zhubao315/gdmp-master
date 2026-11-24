# Skill Runtime 审计（决定性结论）

1. WAR `AI_ROOT_20261117.war` 的 jar/文件名中**无** ai-agent / mcp / skill / llm / vector / embedding 相关组件（unzip -l 实测，无命中）。
2. 文档站全文搜索无 "Agent Skill / Skill 加载 / 智能体运行时" 命中；「AI 能力」章节描述的是业务功能。
3. 产品页面（192.168.1.32:8080）为 React SPA 壳，无 Skill 管理页面证据；无 SSH/后台凭据做运行时枚举 → 待确认。
4. **结论：GDMP 当前没有可加载 Agent Skill 的 AI 执行环境。** 不得伪造加载成功。

## 允许的安装形态
- 仅作为**版本化运维知识包**：SKILL.md + references + runbooks + scripts，带 VERSION/manifest/SHA256，安装=校验后放入约定目录并登记版本。
- 必须明确区分「知识包已安装」与「AI 执行能力已启用」；后者为 **未启用/受阻**。
- 若未来出现 AI 助手/MCP/扩展接口，再评估受控集成，禁止绕过平台权限体系自建远程执行通道。
