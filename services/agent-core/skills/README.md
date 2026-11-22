# Workspace skills

这些 Markdown 是场景技能。agent-core 每轮对话前读取 `SKILL.md`，文件改完下一轮就生效。命中的技能说明会附在提示词后面。

知识库和联网仍由 `core_svc/api.py` 在生成前调用。配置了 `[mcp_servers]` 时走对应的 HTTP MCP，否则直接查服务。
