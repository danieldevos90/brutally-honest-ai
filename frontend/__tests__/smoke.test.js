const fs = require("fs");
const os = require("os");
const path = require("path");
const request = require("supertest");

// Silence expected logs for test runs (must happen before requiring server.js).
const logSpy = jest.spyOn(console, "log").mockImplementation(() => {});
const warnSpy = jest.spyOn(console, "warn").mockImplementation(() => {});
const errorSpy = jest.spyOn(console, "error").mockImplementation(() => {});

// Ensure requiring server.js doesn't bind ports or mutate real data.
const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "bh-frontend-test-"));
process.env.FRONTEND_STATE_DIR = tmpRoot;
process.env.FRONTEND_DATA_DIR = tmpRoot;
process.env.FRONTEND_RECORDINGS_DIR = path.join(tmpRoot, "recordings");
process.env.FRONTEND_HISTORY_FILE = path.join(tmpRoot, "transcription_history.json");
process.env.FRONTEND_ACTIVITY_LOG_FILE = path.join(tmpRoot, "activity.log");
process.env.DISABLE_WS = "1";

// Use a fast-failing backend base for any proxy endpoints we hit.
// Note: Node's built-in fetch blocks some ports as "forbidden"; use a high port.
process.env.API_BASE = "http://127.0.0.1:65534";

const { app } = require("../server");

describe("frontend smoke", () => {
  afterAll(() => {
    logSpy?.mockRestore();
    warnSpy?.mockRestore();
    errorSpy?.mockRestore();
  });

  test("GET /login renders", async () => {
    const res = await request(app).get("/login");
    expect(res.statusCode).toBe(200);
    expect(res.text.toLowerCase()).toContain("login");
  });

  test("auth flow + main pages render", async () => {
    const agent = request.agent(app);

    // Login with the built-in default admin user.
    const loginRes = await agent.post("/api/auth/login").send({
      email: "admin@brutallyhonest.io",
      password: "brutallyhonest2024",
    });
    expect(loginRes.statusCode).toBe(200);
    expect(loginRes.body).toMatchObject({ success: true });

    const pages = ["/", "/documents", "/profiles", "/validation", "/documentation", "/settings"];
    for (const p of pages) {
      const res = await agent.get(p);
      expect(res.statusCode).toBe(200);
      // Basic sanity: HTML responses for pages.
      expect(res.headers["content-type"] || "").toContain("text/html");
    }
  });

  test("public assets are accessible without auth", async () => {
    const res = await request(app).get("/design-system.css");
    expect(res.statusCode).toBe(200);
    expect(res.headers["content-type"] || "").toContain("text/css");
  });

  test("protected JS assets are served with no-cache headers", async () => {
    const agent = request.agent(app);
    await agent.post("/api/auth/login").send({
      email: "admin@brutallyhonest.io",
      password: "brutallyhonest2024",
    });

    const res = await agent.get("/shared.js");
    expect(res.statusCode).toBe(200);
    expect((res.headers["cache-control"] || "").toLowerCase()).toContain("no-cache");
  });

  test("reanalyze proxy does not crash on missing backend", async () => {
    const agent = request.agent(app);
    await agent.post("/api/auth/login").send({
      email: "admin@brutallyhonest.io",
      password: "brutallyhonest2024",
    });

    const res = await agent.post("/api/reanalyze/test-id-123");
    // Backend is unreachable; important part is that handler exists and responds.
    expect([500, 502, 504]).toContain(res.statusCode);
  });
});

