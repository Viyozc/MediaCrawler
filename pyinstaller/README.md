# PyInstaller 打包说明

把 MediaCrawler Pro 后端 + 爬虫 CLI 打包成可独立分发的二进制，
配合 `electron/` 形成完整的桌面 app，**不再依赖用户系统装 uv / python / playwright**。

## 产物

| 二进制 | 入口 | 体积 | 说明 |
|--------|------|------|------|
| `dist/mediacrawler-api/mediacrawler-api` | `api_entry.py` | ~300MB | FastAPI + uvicorn |
| `dist/mediacrawler-cli/mediacrawler-cli` | `cli_entry.py` | ~600-800MB | 含 Playwright + Chromium，可独立跑爬虫 |

## 前置准备

```shell
# 1. 项目根目录已 uv sync
cd /Users/zc/Documents/ai-space/MediaCrawler

# 2. 安装 PyInstaller（加 --extra build）
uv sync --extra build

# 3. 下载 Playwright Chromium（cli 打包必需，api 不需要）
uv run playwright install chromium
```

## 打包命令

```shell
# 后端 API（无 Playwright，速度快，先打它验证流程）
uv run pyinstaller pyinstaller/mediacrawler-api.spec --noconfirm

# 爬虫 CLI（含 Playwright Python 包）
uv run pyinstaller pyinstaller/mediacrawler-cli.spec --noconfirm

# ⚠️ 必需：把 Playwright Chromium 拷进 cli 产物
# （Chromium 的签名 .app 不能被 PyInstaller 直接打包，必须构建后拷贝）
uv run python pyinstaller/post_build.py
```

首次打包各需 5-10 分钟，重打有缓存会快很多。**`post_build.py` 不能漏**，
否则 cli 运行时会报 `Executable doesn't exist at .../playwright_driver/chromium-XXXX/...`。

## 单独验证二进制

```shell
# API：启在 9999 端口
./dist/mediacrawler-api/mediacrawler-api --port 9999 &
curl http://127.0.0.1:9999/api/env/check
# 期望 {"success": true, ...}

# CLI：看帮助
./dist/mediacrawler-cli/mediacrawler-cli --help
# 期望显示 typer 帮助，含 --platform / --lt / --type 等
```

## Electron 集成

`electron/main.js` 会自动检测 `dist/mediacrawler-api/` 和 `dist/mediacrawler-cli/`，
存在则用二进制（桌面模式），不存在则 fallback 到 `uv run`（开发模式）。

启动后端时注入 `MEDIACRAWLER_CLI` 环境变量，让 `crawler_manager` 调用打包后的 cli 二进制，
不再依赖 `uv run python main.py`。

## 目录结构（打包后）

```
dist/
  mediacrawler-api/              ← PyInstaller onedir 产物
    mediacrawler-api               (可执行入口)
    _internal/                     (Python + 依赖)
      docs/                        (hit_stopwords.txt + STZHONGS.TTF)
      api/, config/, media_platform/
  mediacrawler-cli/
    mediacrawler-cli
    _internal/
      playwright_driver/
        chromium-XXXX/             ← post_build.py 拷贝进来
          chrome-mac-arm64/
            Google Chrome for Testing.app   (macOS ARM64)
      ...
```

## 文件清单

| 文件 | 作用 |
|------|------|
| `_common.py` | 共享的 spec 配置：collect_all、hiddenimports、datas |
| `api_entry.py` | API 入口，argparse 解析 `--port --host` |
| `cli_entry.py` | CLI 入口，复用 `main.py` 的 main/async_cleanup |
| `runtime_patches.py` | 启动时设置 `PLAYWRIGHT_BROWSERS_PATH` 和 cwd |
| `post_build.py` | **构建后**把 Chromium 拷进 cli 产物（绕过 PyInstaller 签名失败） |
| `mediacrawler-api.spec` | API 的 PyInstaller spec |
| `mediacrawler-cli.spec` | CLI 的 PyInstaller spec |

## 故障排查

| 现象 | 原因 / 解法 |
|------|-------------|
| `ModuleNotFoundError: No module named 'xxx'` | spec 里 hiddenimports 漏了，加到 `_common.py: common_hiddenimports()` |
| `FileNotFoundError: docs/hit_stopwords.txt` | runtime_patches 没生效，或 spec 里 `datas` 漏了 |
| Playwright 报 `Executable doesn't exist` | 漏跑 `post_build.py`，或 `PLAYWRIGHT_BROWSERS_PATH` 未指向 `_internal/playwright_driver`；检查 `runtime_patches.py` |
| 打包报 `Failed to process binary '.../Google Chrome for Testing'` | Chromium 的签名 .app 不能进 PyInstaller datas/binaries；确认 `_common.py: playwright_deps()` 没有把 chromium 加进去，改用 `post_build.py` 拷贝 |
| 打包后 `data/` 写不进去 | Electron 主进程没注入 `MEDIACRAWLER_DATA_DIR`，或 cwd 是只读路径 |
| macOS 第一次运行被 Gatekeeper 拦截 | 未签名；右键 → 打开，或 `xattr -d com.apple.quarantine /path/to/app` |
| 打包报错 `Failed to load Python dylib` | macOS 版本不兼容，PyInstaller 跨 minor 版本可能出问题 |
| 体积过大 | `du -sh dist/mediacrawler-cli/_internal/` 排查；opencv、pandas、Chromium 占大头 |

## 重新打包的快速调试

调试 spec 问题时加 `--log-level DEBUG`：
```shell
uv run pyinstaller pyinstaller/mediacrawler-api.spec --noconfirm --log-level DEBUG 2>&1 | tee build.log
```
