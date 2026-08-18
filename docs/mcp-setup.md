# Zotero MCP 配置（可选增强）

本 skill **默认不使用 MCP**——通过 Zotero Web API（只读）直接交互已覆盖全部需求。以下内容仅供需要更精细 Zotero 操作的场景（如按标签批量整理、跨库检索、在对话中频繁搜索/管理 Zotero 库）。

如果你的 Claude Code 需要**搜索、读取、管理** Zotero 条目的能力，可以配置 Zotero MCP Server。

## 方案 1：社区 MCP Server（推荐）

社区项目 `zotero-mcp` 封装了 Zotero Web API 为 MCP 工具。配置方式：

在 Claude Code 的 settings.json 中添加：

```json
{
  "mcpServers": {
    "zotero": {
      "command": "npx",
      "args": ["-y", "zotero-mcp"],
      "env": {
        "ZOTERO_API_KEY": "你的API密钥",
        "ZOTERO_USER_ID": "你的UserID"
      }
    }
  }
}
```

或在 `%APPDATA%\Claude\claude_desktop_config.json` 中配置。

## 方案 2：Zotero 本地 API（实验性）

Zotero 7 内置了本地 HTTP API（默认端口 23119），可读取已打开的本地库。但**只能读不能写**，写入仍需 Web API。

## MCP 提供的典型能力

- 搜索条目（标题/作者/标签/DOI）
- 读取条目元数据与附件
- 管理集合（Collections）与标签
- 创建/修改笔记与条目

## 本 skill 与 MCP 的关系

**不需要。** 本 skill 用 Zotero Web API（只读：搜索 → 定位 PDF → 读元数据）完成"论文 → 笔记"流水线，无需 MCP。MCP 是可选增强，适合需要在对话中频繁搜索/管理 Zotero 库的场景。
