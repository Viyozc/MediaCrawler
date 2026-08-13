# MediaCrawler Pro

<div align="center">

[![GitHub Stars](https://img.shields.io/github/stars/Viyozc/MediaCrawler-Pro?style=social)](https://github.com/Viyozc/MediaCrawler-Pro/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Viyozc/MediaCrawler-Pro?style=social)](https://github.com/Viyozc/MediaCrawler-Pro/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/Viyozc/MediaCrawler-Pro)](https://github.com/Viyozc/MediaCrawler-Pro/issues)
[![License](https://img.shields.io/badge/license-NCL%201.1-blue)](./LICENSE)
[![中文](https://img.shields.io/badge/🇨🇳_中文-当前-blue)](README.md)
[![English](https://img.shields.io/badge/🇺🇸_English-Available-green)](README_en.md)

**基于开源 MediaCrawler 的升级版** —— 多平台自媒体数据采集 · WebUI · 桌面端 · 任务中心 · AI 分析 · MCP

</div>

> **免责声明**
>
> 请以学习与研究为目的使用本仓库。参见 [爬虫违法违规的案件](https://github.com/HiddenStrawberry/Crawler_Illegal_Cases_In_China)。
>
> 本仓库内容仅供学习参考，禁止商业用途与大规模干扰平台运营的行为。因使用本仓库引起的法律责任由使用者自行承担。详细条款见 [LICENSE](./LICENSE) 与下文 [免责声明](#disclaimer)。

## 项目简介

MediaCrawler Pro 是在上游开源项目 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 基础上的维护与能力升级版，支持小红书、抖音、快手、B站、微博、贴吧、知乎等平台的公开信息采集。

### 相对上游的升级点

| 能力 | 说明 |
|------|------|
| WebUI | 可视化配置、日志、数据预览 |
| 桌面端 | Electron 包装，本地一键启动 |
| 任务中心 | 历史任务、输出文件关联、日志归档 |
| AI Chat | 基于任务结果的本地 LLM 分析对话 |
| MCP | 只读 MCP 服务，供 Cursor / Claude Desktop 等查询任务数据 |

### 技术原理

- 基于 [Playwright](https://playwright.dev/) 浏览器自动化与登录态复用
- 在保留登录态的上下文中获取签名参数，降低 JS 逆向门槛
- 默认支持 CDP 模式连接本机 Chrome

## 功能矩阵

| 平台 | 关键词搜索 | 指定帖子 | 二级评论 | 创作者主页 | 登录态缓存 | IP 代理池 | 评论词云 |
|------|------------|----------|----------|------------|------------|-----------|----------|
| 小红书 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 抖音 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 快手 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B 站 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 微博 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 贴吧 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 知乎 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## 快速开始

### 前置依赖

- [uv](https://docs.astral.sh/uv/getting-started/installation)（推荐）
- Node.js >= 16（抖音 / 知乎等需要）
- Python >= 3.11

```shell
git clone https://github.com/Viyozc/MediaCrawler-Pro.git
cd MediaCrawler-Pro
uv sync
```

标准 Playwright 模式需安装浏览器驱动：

```shell
uv run playwright install
```

CDP 模式可复用本机 Chrome 登录态，详见 [CDP 模式使用指南](./docs/CDP模式使用指南.md)。

### 命令行运行

```shell
uv run main.py --platform xhs --lt qrcode --type search
uv run main.py --help
```

配置说明见 `config/base_config.py`。

### WebUI（开发）

```shell
# 终端 1
uv run uvicorn api.main:app --port 8080 --reload

# 终端 2
cd webui && npm install && npm run dev
```

浏览器打开 `http://localhost:5173/`。

生产构建：

```shell
cd webui && npm run build   # 输出到 api/webui/
uv run uvicorn api.main:app --port 8080
```

### 桌面端（Electron）

```shell
cd electron && npm install && npm start
```

> **注意：** 桌面端应用标识为 `mediacrawler-pro-desktop`，用户数据目录与旧版 `mediacrawler-desktop` 不同。若需迁移历史任务，请手动复制旧 Application Support 目录下的 `data/`。

### MCP

见 [MCP 服务使用指南](./docs/MCP服务使用指南.md)。

## 文档

- [使用索引](./docs/index.md)
- [数据存储](./docs/data_storage_guide.md)
- [常见问题](./docs/常见问题.md)
- [代理使用](./docs/代理使用.md)

## 致谢

本项目基于 [NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 开源版本演进。感谢上游作者与贡献者的工作。

MediaCrawler Pro 是本仓库的维护品牌，与上游作者的商业订阅产品无关。

## 参与贡献

请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)。Issue / PR 请提交到本仓库。

## 许可证

[NON-COMMERCIAL LEARNING LICENSE 1.1](./LICENSE)（非商业学习使用许可证）。仅限学习研究，禁止商业用途。

<a id="disclaimer"></a>

## 免责声明

1. 本仓库所有内容仅供学习与研究，禁止用于商业或非法用途。
2. 使用者应遵守目标平台条款与 robots 规则，合理控制频率。
3. 因使用本仓库内容引起的任何法律责任，本仓库维护者不承担。
4. 使用本仓库即表示同意 LICENSE 与本免责声明。
