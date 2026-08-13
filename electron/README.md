# MediaCrawler Desktop (MVP)

把 MediaCrawler 的 WebUI + FastAPI 后端包成一个 Electron 桌面应用。

## 前置条件（一次性）

```shell
# 项目根目录
cd /Users/zc/Documents/ai-space/MediaCrawler
uv sync

# 前端依赖
cd webui
npm install
```

## 启动

```shell
cd electron
npm install     # 首次，装 electron
npm start
```

Electron 启动后会自动：
1. 选一个空闲 API 端口（默认从 8081 开始递增）
2. 在项目根目录 spawn `uv run uvicorn api.main:app --port <apiPort>`
3. 在 `webui/` 目录 spawn `npm run dev`（Vite 5174）
4. 健康检查通过后打开窗口加载 `http://localhost:5174/`

## 与已有 dev 进程共存

如果启动 Electron 时 `8081` 或 `5174` 已经在监听（比如你已经在终端手动起过），Electron 会**直接复用**而不再 spawn，方便联调：
- 复用已有后端：保留 `--reload` 的热加载
- 复用已有 Vite：保留 React HMR

## 退出清理

关闭窗口 / Cmd+Q 时，Electron 会向所有它拉起的子进程组发送 SIGTERM（Windows 用 `taskkill /t`）。**复用模式**下不会动你手动起的进程。

## 已知限制（MVP）

- ⚠️ 仍是开发模式，依赖 `uv`、`node`、`npm` 都在 PATH 里
- ⚠️ 没有打包成 .dmg/.exe，不分发
- ⚠️ Python 后端、Vite 各自占一个终端输出，日志混在 Electron 主进程 stdout 里
- ⚠️ 没有自动更新、代码签名

## 后续路线（不在 MVP 范围）

| 项 | 说明 |
|----|------|
| PyInstaller 打包 | 把 Python 后端打成单可执行文件，去 `uv` 依赖 |
| `crawler_manager` 改造 | 把 `subprocess.Popen(["uv", "run", ...])` 改成调打包后的入口 |
| electron-builder | 出 dmg / nsis / AppImage |
| 去 Playwright | 桌面版强制 CDP 模式，去掉 Chromium 依赖（~170MB） |
| 代码签名 | macOS notarize + Windows authenticode |
| 自动更新 | electron-updater |

## 故障排查

| 现象 | 原因 / 解法 |
|------|-------------|
| 弹窗「启动失败」 | 看终端 stdout，检查 `uv`、`node` 是否在 PATH |
| 窗口打开但白屏 | Vite 还没 ready，等几秒会自动加载；或手动访问 `http://localhost:5174/` 确认 |
| 端口冲突 | Electron 会自动避让 8081；5174 是 Vite 写死的，被占用时 spawn 会报错 |
| 找不到 Python | 确认 `uv sync` 已在项目根目录跑过 |
