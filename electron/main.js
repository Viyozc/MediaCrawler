// Minimal Electron wrapper for MediaCrawler Pro.
//
// Startup flow:
//   1. Pick a free API port (preferred 8081, auto-increment on conflict).
//   2. Spawn `uv run uvicorn api.main:app --port <apiPort>` from project root,
//      unless that port is already listening (dev-mode reuse).
//   3. Spawn `npm run dev` from webui/ (Vite dev server on 5174), unless 5174
//      is already listening.
//   4. Poll both health endpoints, then open a BrowserWindow on the Vite URL.
//   5. On quit, kill the whole process group of each spawned child.
//
// Prerequisites (one-time):
//   - `uv sync` in project root
//   - `cd webui && npm install`
//
// Run from this directory:  npm start

const { app, BrowserWindow, dialog } = require('electron');
const { spawn, execFileSync } = require('child_process');
const http = require('http');
const net = require('net');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const WEBUI_DIR = path.join(PROJECT_ROOT, 'webui');
const API_PORT_PREFERRED = 8081;
const WEBUI_PORT = 5174;
const READY_TIMEOUT_MS = 120_000; // uv sync / npm install on first run can be slow

// PyInstaller 产物路径（onedir 模式，二进制在子目录里）
const DIST_DIR = path.join(PROJECT_ROOT, 'dist');
const API_BINARY = path.join(DIST_DIR, 'mediacrawler-api', 'mediacrawler-api');
const CLI_BINARY = path.join(DIST_DIR, 'mediacrawler-cli', 'mediacrawler-cli');

let mainWindow = null;
const children = [];

const fs = require('fs');
const exists = (p) => { try { return fs.existsSync(p); } catch { return false; } };

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function findFreePort(start, maxTries = 10) {
  return new Promise((resolve, reject) => {
    let port = start;
    const tryNext = () => {
      if (port >= start + maxTries) return reject(new Error(`No free port near ${start}`));
      const srv = net.createServer();
      srv.unref();
      srv.on('error', () => { port += 1; tryNext(); });
      srv.listen(port, '127.0.0.1', () => srv.close(() => resolve(port)));
    };
    tryNext();
  });
}

// Vite 默认只监听 IPv6 [::1], uvicorn 默认监听 IPv4 127.0.0.1。
// 双栈都检查, 任一通即视为占用/就绪, 否则会重复 spawn 或永远卡健康检查。
const HOSTS = ['127.0.0.1', '::1'];

function checkHost(host, port) {
  return new Promise((resolve) => {
    const sock = net.createConnection({ port, host });
    sock.once('connect', () => { sock.end(); resolve(true); });
    sock.once('error', () => resolve(false));
  });
}

async function isPortListening(port) {
  for (const host of HOSTS) {
    if (await checkHost(host, port)) return true;
  }
  return false;
}

function httpOk(host, port, path = '/', timeoutMs = 1500) {
  return new Promise((resolve) => {
    const req = http.get(
      { hostname: host, port, path, family: host === '::1' ? 6 : 4, timeout: timeoutMs },
      (res) => {
        res.resume();
        res.statusCode === 200 ? resolve(true) : resolve(false);
      },
    );
    req.on('error', () => resolve(false));
    req.on('timeout', () => { req.destroy(); resolve(false); });
  });
}

async function waitForPortReady(port, path = '/', { timeoutMs = READY_TIMEOUT_MS, intervalMs = 500 } = {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    for (const host of HOSTS) {
      if (await httpOk(host, port, path)) return host;
    }
    await sleep(intervalMs);
  }
  throw new Error(`Timeout waiting for port ${port}${path} after ${timeoutMs}ms`);
}

function tag(tagName) {
  return (chunk) => process.stdout.write(`[${tagName}] ${chunk}`);
}

// 让后端子进程能定位打包后的 cli 二进制，并把 data/ 输出目录指向用户可写位置。
// 只在桌面模式（dist/ 已打包）注入；开发模式下 process.env 不变。
function buildChildEnv() {
  const env = { ...process.env, PYTHONUNBUFFERED: '1', FORCE_COLOR: '1' };
  if (exists(CLI_BINARY)) {
    env.MEDIACRAWLER_CLI = CLI_BINARY;
  }
  if (app && app.isReady()) {
    // 把 data/ 落到用户数据目录，避免 cwd 只读导致写不进去
    env.MEDIACRAWLER_DATA_DIR = path.join(app.getPath('userData'), 'data');
  }
  return env;
}

function spawnChild(cmd, args, opts) {
  // detached=true creates a new process group on Unix so we can kill the tree
  const child = spawn(cmd, args, {
    cwd: opts.cwd,
    detached: true,
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: opts.shell,
    env: buildChildEnv(),
  });
  child.stdout.on('data', tag(opts.tag || cmd));
  child.stderr.on('data', tag(opts.tag || cmd));
  child.on('exit', (code, signal) => {
    console.log(`[${opts.tag}] exited code=${code} signal=${signal}`);
  });
  child.on('error', (err) => {
    console.error(`[${opts.tag}] spawn error:`, err.message);
  });
  children.push(child);
  return child;
}

// 优先复用 preferred 端口上已在跑的服务 (dev 联调模式),
// 没监听才 findFreePort spawn 新进程, 避免重复拉起。
async function startBackend(preferredPort) {
  if (await isPortListening(preferredPort)) {
    console.log(`[backend] :${preferredPort} already listening, reusing (dev mode)`);
    return preferredPort;
  }
  const port = await findFreePort(preferredPort);

  // Packaged binary only when explicitly requested. Stale dist/ binaries otherwise
  // shadow source fixes (e.g. platform dir mapping) and confuse local `npm start`.
  const usePackaged =
    process.env.MEDIACRAWLER_USE_PACKAGED === '1' && exists(API_BINARY);

  if (usePackaged) {
    console.log(`[backend] using packaged binary: ${API_BINARY}`);
    spawnChild(API_BINARY, ['--port', String(port)], {
      cwd: DIST_DIR,
      tag: 'backend',
    });
  } else {
    if (exists(API_BINARY) && process.env.MEDIACRAWLER_USE_PACKAGED !== '1') {
      console.log(
        '[backend] dist/mediacrawler-api present but ignored; set MEDIACRAWLER_USE_PACKAGED=1 to use it',
      );
    }
    console.log('[backend] using uv run uvicorn (source)');
    spawnChild('uv', ['run', 'uvicorn', 'api.main:app', '--port', String(port)], {
      cwd: PROJECT_ROOT,
      tag: 'backend',
    });
  }
  return port;
}

async function startWebui() {
  if (await isPortListening(WEBUI_PORT)) {
    console.log(`[webui] :${WEBUI_PORT} already listening, reusing (dev mode)`);
    return;
  }
  spawnChild('npm', ['run', 'dev'], {
    cwd: WEBUI_DIR,
    tag: 'webui',
    shell: process.platform === 'win32',
  });
}

function killChildren() {
  for (const child of children) {
    try {
      if (!child.pid || child.killed) continue;
      if (process.platform === 'win32') {
        execFileSync('taskkill', ['/pid', String(child.pid), '/f', '/t'], { stdio: 'ignore' });
      } else {
        process.kill(-child.pid, 'SIGTERM'); // negative pid = process group
      }
    } catch {
      // process may have already exited
    }
  }
  children.length = 0;
}

async function bootstrap() {
  const apiPort = await startBackend(API_PORT_PREFERRED);
  console.log(`[main] using API port ${apiPort}`);
  await startWebui();

  console.log('[main] waiting for backend health...');
  await waitForPortReady(apiPort, '/api/health');
  console.log('[main] backend ready, waiting for Vite dev server...');
  const webuiHost = await waitForPortReady(WEBUI_PORT, '/');
  console.log(`[main] Vite ready on ${webuiHost}, opening window`);

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    title: 'MediaCrawler Pro',
    backgroundColor: '#0f0f0f',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.apiPort = apiPort;
  await mainWindow.loadURL(`http://localhost:${WEBUI_PORT}/`);
}

app.whenReady().then(async () => {
  try {
    await bootstrap();
  } catch (err) {
    console.error('[main] bootstrap failed:', err);
    dialog.showErrorBox(
      'MediaCrawler Pro 启动失败',
      `${err && err.message ? err.message : err}\n\n请检查：\n1. 项目根目录已执行 uv sync\n2. webui 目录已执行 npm install\n3. 端口 ${API_PORT_PREFERRED} / ${WEBUI_PORT} 未被占用`,
    );
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', killChildren);

// Clean up if the renderer process crashes
app.on('render-process-gone', (_event, _webContents, details) => {
  console.error('[main] renderer gone:', details);
});
