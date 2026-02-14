const path = require("path");

// Store E2E state inside the frontend folder so it's self-contained.
const stateDir = path.join(__dirname, ".tmp", "e2e-state");
const dataDir = path.join(__dirname, ".tmp", "e2e-data");
const recordingsDir = path.join(__dirname, ".tmp", "e2e-recordings");

/** @type {import('@playwright/test').PlaywrightTestConfig} */
module.exports = {
  testDir: "e2e",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:3101",
    trace: "retain-on-failure",
    video: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "node scripts/e2e_webserver.cjs",
    cwd: __dirname,
    url: "http://127.0.0.1:3101/login",
    reuseExistingServer: true,
    timeout: 60_000,
    env: {
      PORT: "3101",
      WS_PORT: "3102",
      API_HOST: "127.0.0.1",
      API_PORT: "8000",
      API_MASTER_KEY: "bh_test_master_key_for_e2e_only",
      FRONTEND_STATE_DIR: stateDir,
      FRONTEND_DATA_DIR: dataDir,
      FRONTEND_RECORDINGS_DIR: recordingsDir,
      FRONTEND_HISTORY_FILE: path.join(dataDir, "transcription_history.json"),
      FRONTEND_ACTIVITY_LOG_FILE: path.join(stateDir, "activity.log"),
      FRONTEND_USERS_FILE: path.join(stateDir, "users.json"),
      FRONTEND_SESSIONS_FILE: path.join(stateDir, "sessions.json"),
      FRONTEND_LOGS_FILE: path.join(stateDir, "activity_logs.json"),
    },
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
};

