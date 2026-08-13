# MediaCrawler Pro Rebrand Implementation Plan

> **For agentic workers:** Facade rebrand only (Approach 2). No bulk `.py` header rewrites.

**Goal:** Publish MediaCrawler Pro branding, strip upstream-author promo materials, point links to `Viyozc/MediaCrawler-Pro`, keep NCL 1.1.

**Architecture:** Docs/UI/package identifiers only; crawler runtime env vars unchanged.

## Tasks

- [x] Rewrite README zh/en; slim README_es
- [x] Remove author/subscription/donation docs and promo images
- [x] Update VitePress nav/social; disable DynamicAds
- [x] UI brand, footer attribution, license i18n, GitHub links
- [x] Rename packages: mediacrawler-pro / webui / desktop
- [x] CONTRIBUTING + GitHub templates / CODEOWNERS / FUNDING
- [x] MCP docs + Electron title / app name note
- [x] Platform dir scan fix for AI chat (`dy` → `douyin`) included in tree
