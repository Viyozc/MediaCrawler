# MediaCrawler Pro 使用索引

## 项目文档

- [中文 README](../README.md) — 项目介绍与快速开始
- [English README](../README_en.md)
- [贡献指南](../CONTRIBUTING.md)
- [MCP 服务使用指南](MCP服务使用指南.md)
- [CDP 模式使用指南](CDP模式使用指南.md)
- [数据存储](data_storage_guide.md)
- [Excel 导出](excel_export_guide.md)
- [常见问题](常见问题.md)
- [代理使用](代理使用.md)
- [词云图配置](词云图使用配置.md)

## 推荐：使用 uv 管理依赖

### 1. 前置依赖

- 安装 [uv](https://docs.astral.sh/uv/getting-started/installation)，并用 `uv --version` 验证。
- Python 建议 **3.11+**。
- Node.js（抖音、知乎等）`>= 16.0.0`。

### 2. 同步依赖

```shell
cd MediaCrawler-Pro
uv sync
```

### 3. 运行

```shell
uv run main.py --platform xhs --lt qrcode --type search
uv run main.py --help
```

WebUI / 桌面端说明见根目录 README。

## 致谢

本仓库基于 [NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 演进。
