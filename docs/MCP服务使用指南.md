# MediaCrawler Pro MCP 服务使用指南

MediaCrawler Pro 提供独立的 MCP (Model Context Protocol) 服务二进制 `mediacrawler-mcp`，把桌面 app 落盘的历史任务数据暴露给本地 LLM 客户端（Claude Desktop、Cursor 等），让 Agent 实时查询和分析爬取结果。

## 特性

- **stdio 传输**：与 Claude Desktop / Cursor 的标准 MCP 配置完全兼容
- **只读访问**：只读取 `MEDIACRAWLER_DATA_DIR` 下的任务 registry 和数据文件，不修改
- **轻量独立**：单独的二进制，不依赖 Electron / FastAPI / Playwright 运行
- **6 个工具 + 3 个资源**：任务列表、详情、数据查询、统计、搜索、平台列表

## 构建

```bash
uv run --extra build pyinstaller pyinstaller/mediacrawler-mcp.spec --noconfirm
```

产物：`dist/mediacrawler-mcp/mediacrawler-mcp`

## 客户端注册

所有客户端共用同一个核心配置：
- `command`：`mediacrawler-mcp` 二进制的绝对路径
- `env.MEDIACRAWLER_DATA_DIR`：桌面 app 的数据目录绝对路径

数据目录查找规则：
- **桌面 app（macOS）**：`~/Library/Application Support/mediacrawler-pro-desktop/data`
- **旧版桌面目录（迁移）**：`~/Library/Application Support/mediacrawler-desktop/data`
- **开发模式**：项目根目录下的 `data/`（或由环境变量指定）

### Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "mediacrawler-pro": {
      "command": "/绝对路径/dist/mediacrawler-mcp/mediacrawler-mcp",
      "env": {
        "MEDIACRAWLER_DATA_DIR": "/Users/你的用户名/Library/Application Support/mediacrawler-pro-desktop/data"
      }
    }
  }
}
```

保存后**完全退出并重启** Claude Desktop（菜单栏图标 → Quit）。

### Cursor

在 Cursor MCP 设置中增加同样的 server 配置，或写入项目 / 用户 MCP JSON：

```json
{
  "mcpServers": {
    "mediacrawler-pro": {
      "command": "/绝对路径/dist/mediacrawler-mcp/mediacrawler-mcp",
      "env": {
        "MEDIACRAWLER_DATA_DIR": "/Users/你的用户名/Library/Application Support/mediacrawler-pro-desktop/data"
      }
    }
  }
}
```

在 Cursor 设置 → MCP 中确认 `mediacrawler-pro` 已连上。

## 可用资源（Resources）

| URI | 说明 |
|-----|------|
| `mediacrawler://tasks` | 最新 100 条任务记录（JSON） |
| `mediacrawler://tasks/{task_id}` | 单个任务详情 |
| `mediacrawler://tasks/{task_id}/data` | 该任务所有输出文件的数据（每个文件截断 50 行） |

## 常用提问示例

- **"列出我最近的 MediaCrawler Pro 任务"** → 调用 `list_tasks`
- **"分析 task_xxx 的评论数据"** → 调用任务数据相关 tool / resource

## 排障

1. 确认 `MEDIACRAWLER_DATA_DIR` 指向含 `tasks/registry.json` 的目录：

```bash
ls "$MEDIACRAWLER_DATA_DIR/tasks/registry.json"
```

2. 或查找：

```bash
find ~/Library/Application\ Support/mediacrawler-pro-desktop -name registry.json 2>/dev/null
find ~/Library/Application\ Support/mediacrawler-desktop -name registry.json 2>/dev/null
```

3. 开发调试：

```bash
MEDIACRAWLER_DATA_DIR=/path/to/data uv run python -m mcp_server.server
```

更多说明见仓库 README 与 `mcp_server/` 源码。
