const { test, expect } = require("@playwright/test");
const { loginAsAdmin } = require("./helpers");

test("admin APIs: /api/users and /api/logs", async ({ page, context }) => {
  await loginAsAdmin(page);

  // /api/users should be accessible as admin.
  const usersRes = await context.request.get("/api/users");
  expect(usersRes.ok()).toBeTruthy();
  const users = await usersRes.json();
  expect(Array.isArray(users.users)).toBe(true);
  expect(users.users.some((u) => u.email === "admin@brutallyhonest.io")).toBe(true);

  // Create a log entry from client.
  const postLogRes = await context.request.post("/api/logs", {
    data: { type: "system", action: "e2e_test", details: { source: "playwright" } },
  });
  expect(postLogRes.ok()).toBeTruthy();

  // Fetch recent logs.
  const logsRes = await context.request.get("/api/logs?limit=10");
  expect(logsRes.ok()).toBeTruthy();
  const logs = await logsRes.json();
  expect(logs.success).toBe(true);
  expect(Array.isArray(logs.logs)).toBe(true);
});

