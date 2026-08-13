# MediaCrawler Pro

<div align="center">

[![GitHub Stars](https://img.shields.io/github/stars/Viyozc/MediaCrawler-Pro?style=social)](https://github.com/Viyozc/MediaCrawler-Pro/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Viyozc/MediaCrawler-Pro?style=social)](https://github.com/Viyozc/MediaCrawler-Pro/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/Viyozc/MediaCrawler-Pro)](https://github.com/Viyozc/MediaCrawler-Pro/issues)
[![License](https://img.shields.io/badge/license-NCL%201.1-blue)](./LICENSE)
[![中文](https://img.shields.io/badge/🇨🇳_中文-Available-green)](README.md)
[![English](https://img.shields.io/badge/🇺🇸_English-Current-blue)](README_en.md)

**An upgraded edition of open-source MediaCrawler** — multi-platform social data collection · WebUI · Desktop · Task history · AI chat · MCP

</div>

> **Disclaimer**
>
> Use this repository for learning and research only. See [Crawler illegal cases in China](https://github.com/HiddenStrawberry/Crawler_Illegal_Cases_In_China).
>
> Commercial use and large-scale disruption of platforms are prohibited. Users bear all legal responsibility. See [LICENSE](./LICENSE).

## About

MediaCrawler Pro is a maintained upgrade of upstream [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler), supporting Xiaohongshu, Douyin, Kuaishou, Bilibili, Weibo, Tieba, Zhihu, and more.

### Upgrades vs upstream

| Feature | Description |
|---------|-------------|
| WebUI | Visual config, logs, data preview |
| Desktop | Electron wrapper for local one-click launch |
| Task center | History, output file linking, log archive |
| AI Chat | Local LLM analysis over task results |
| MCP | Read-only MCP server for Cursor / Claude Desktop |

### How it works

- [Playwright](https://playwright.dev/) browser automation with persisted login state
- Sign parameters via JS in an authenticated context (less reverse-engineering)
- Optional CDP mode against your local Chrome

## Quick start

```shell
git clone https://github.com/Viyozc/MediaCrawler-Pro.git
cd MediaCrawler-Pro
uv sync
uv run main.py --platform xhs --lt qrcode --type search
```

WebUI (dev):

```shell
uv run uvicorn api.main:app --port 8080 --reload
cd webui && npm install && npm run dev
```

Desktop: `cd electron && npm install && npm start`

> Desktop app id is `mediacrawler-pro-desktop`. User data path differs from the old `mediacrawler-desktop` name — migrate `data/` manually if needed.

More docs: [docs/index.md](./docs/index.md), [MCP guide](./docs/MCP服务使用指南.md).

## Acknowledgments

Built on [NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler). Thanks to the upstream authors and contributors.

MediaCrawler Pro is this repository’s brand and is unrelated to any commercial subscription product from upstream.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

[NON-COMMERCIAL LEARNING LICENSE 1.1](./LICENSE). Learning and research only; no commercial use.
