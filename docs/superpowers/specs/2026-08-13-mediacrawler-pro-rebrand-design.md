# MediaCrawler Pro Rebrand Design

**Date:** 2026-08-13  
**Status:** Approved (Approach 2)

## Goals

Rebrand this fork as **MediaCrawler Pro**, an upgraded edition of the upstream open-source MediaCrawler, with open-source facade standards. Remove upstream-author personal materials, sponsorship ads, and commercial MediaCrawlerPro subscription promo. Keep NCL 1.1 license text.

## Decisions

| Topic | Choice |
|-------|--------|
| Public repo | `https://github.com/Viyozc/MediaCrawler-Pro` |
| Attribution | Credit upstream NanmiCoder/MediaCrawler; no Relakkes socials/avatar |
| Scope | Docs/UI facade + package/app identifiers (not bulk `.py` file headers) |
| License | Keep NON-COMMERCIAL LEARNING LICENSE 1.1 |

## Out of scope

- Bulk rewrite of source file copyright headers
- Renaming MCP URI scheme / `MEDIACRAWLER_*` env vars
- Changing crawler core behavior

## Deliverables

1. Rewritten README (zh/en); Spanish README redirected or slimmed
2. Remove author/sponsor/subscription docs and stop referencing ad assets
3. UI brand name, GitHub links, footer attribution, license i18n
4. Package names: `mediacrawler-pro`, webui, electron desktop
5. Open-source facade: CONTRIBUTING, issue templates, FUNDING/CODEOWNERS cleanup
6. Note Electron userData path change when package name changes
