#!/usr/bin/env node

const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function waitForOk(url, { timeoutMs = 60_000 } = {}) {
  const start = Date.now();
  // Node 22 has fetch; fallback isn't needed in this repo context.
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url, { redirect: "manual" });
      if (res.ok) return true;
    } catch (_) {
      // ignore while waiting
    }
    await sleep(250);
  }
  throw new Error(`Timed out waiting for OK: ${url}`);
}

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

async function main() {
  const repoRoot = path.resolve(__dirname, "..", "..");
  const frontendRoot = path.resolve(__dirname, "..");

  const PORT = process.env.PORT || "3101";
  const WS_PORT = process.env.WS_PORT || "3102";
  const API_PORT = process.env.API_PORT || "8000";
  const API_HOST = process.env.API_HOST || "127.0.0.1";
  const API_MASTER_KEY = process.env.API_MASTER_KEY || "bh_test_master_key_for_e2e_only";

  const stateDir = path.join(frontendRoot, ".tmp", "e2e-state");
  const dataDir = path.join(frontendRoot, ".tmp", "e2e-data");
  const recordingsDir = path.join(frontendRoot, ".tmp", "e2e-recordings");
  ensureDir(stateDir);
  ensureDir(dataDir);
  ensureDir(recordingsDir);

  const python = path.join(repoRoot, ".venv", "bin", "python");
  const uvicornArgs = [
    "-m",
    "uvicorn",
    "api_server:app",
    "--host",
    API_HOST,
    "--port",
    API_PORT,
    "--log-level",
    "warning",
  ];

  const backendEnv = {
    ...process.env,
    API_MASTER_KEY,
  };

  const frontendEnv = {
    ...process.env,
    PORT,
    WS_PORT,
    DISABLE_WS: "1",
    API_BASE: `http://${API_HOST}:${API_PORT}`,
    API_MASTER_KEY,
    FRONTEND_STATE_DIR: stateDir,
    FRONTEND_DATA_DIR: dataDir,
    FRONTEND_RECORDINGS_DIR: recordingsDir,
    FRONTEND_HISTORY_FILE: path.join(dataDir, "transcription_history.json"),
    FRONTEND_ACTIVITY_LOG_FILE: path.join(stateDir, "activity.log"),
    FRONTEND_USERS_FILE: path.join(stateDir, "users.json"),
    FRONTEND_SESSIONS_FILE: path.join(stateDir, "sessions.json"),
    FRONTEND_LOGS_FILE: path.join(stateDir, "activity_logs.json"),
    // keep the default admin password stable for the tests
    ADMIN_PASSWORD: "brutallyhonest2024",
  };

  // Start backend first.
  const backend = spawn(python, uvicornArgs, {
    cwd: repoRoot,
    env: backendEnv,
    stdio: "inherit",
  });

  // Start frontend.
  const frontend = spawn(process.execPath, ["server.js"], {
    cwd: frontendRoot,
    env: frontendEnv,
    stdio: "inherit",
  });

  const shutdown = () => {
    try {
      frontend.kill("SIGTERM");
    } catch (_) {}
    try {
      backend.kill("SIGTERM");
    } catch (_) {}
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
  process.on("exit", shutdown);

  // Wait until both are reachable.
  await waitForOk(`http://${API_HOST}:${API_PORT}/health`, { timeoutMs: 60_000 });
  await waitForOk(`http://127.0.0.1:${PORT}/login`, { timeoutMs: 60_000 });

  // Keep the process alive as long as children are alive.
  // If either exits, exit with failure to surface broken webServer behavior.
  const onExit = (which) => (code, signal) => {
    console.error(`[e2e_webserver] ${which} exited (code=${code}, signal=${signal})`);
    shutdown();
    process.exit(code || 1);
  };
  backend.on("exit", onExit("backend"));
  frontend.on("exit", onExit("frontend"));
}

main().catch((err) => {
  console.error("[e2e_webserver] failed:", err);
  process.exit(1);
});

