# Contributing to MediaCrawler Pro

Thanks for your interest in contributing.

## Before you start

- This project is for **learning and research** under the [NON-COMMERCIAL LEARNING LICENSE 1.1](./LICENSE).
- Do not submit changes intended for commercial crawling products or for circumventing platform abuse protections at scale.
- Search [existing issues](https://github.com/Viyozc/MediaCrawler-Pro/issues) before opening a new one.

## Development setup

```shell
uv sync
cd webui && npm install
```

Backend: `uv run uvicorn api.main:app --port 8080 --reload`  
Frontend: `cd webui && npm run dev`

## Pull requests

1. Fork / branch from `main`
2. Keep changes focused; prefer one concern per PR
3. Add or update tests when fixing scanner / API behavior
4. Use English for code comments and new UI copy keys; user-facing zh/en i18n as needed
5. Do not reintroduce upstream-author personal promo, sponsorship ads, or third-party affiliate banners unless maintainers ask

## Reporting bugs

Use the Bug Report issue template. Include platform, OS, Python/Node versions, and minimal reproduction steps.

## Code of conduct

Be respectful. Harassment or spam will be closed without discussion.
