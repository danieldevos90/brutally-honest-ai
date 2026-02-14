const { test, expect } = require("@playwright/test");
const { loginAsAdmin } = require("./helpers");

test("login + navigate main pages", async ({ page }) => {
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  await loginAsAdmin(page);

  // Home renders.
  await expect(page).toHaveTitle(/Home - Brutally Honest/);
  const desktopNav = page.locator("nav.nav-menu");
  await expect(desktopNav).toBeVisible();

  // Documents
  await desktopNav.getByRole("link", { name: "Documents" }).click();
  await expect(page).toHaveURL(/\/documents$/);
  await expect(page).toHaveTitle(/Documents - Brutally Honest/);

  // Profiles
  await desktopNav.getByRole("link", { name: "Profiles" }).click();
  await expect(page).toHaveURL(/\/profiles$/);
  await expect(page).toHaveTitle(/Profiles - Brutally Honest/);

  // Validation
  await desktopNav.getByRole("link", { name: "Validation" }).click();
  await expect(page).toHaveURL(/\/validation$/);
  await expect(page).toHaveTitle(/Validation - Brutally Honest/);

  // Documentation
  await desktopNav.getByRole("link", { name: "Documentation" }).click();
  await expect(page).toHaveURL(/\/documentation$/);
  await expect(page).toHaveTitle(/Documentation - Brutally Honest/);

  // Settings is accessible via user dropdown.
  await page.locator(".user-btn").click();
  await page.locator("#user-dropdown").getByRole("link", { name: "Settings" }).click();
  await expect(page).toHaveURL(/\/settings$/);
  await expect(page).toHaveTitle(/Settings - Brutally Honest/);

  // We allow backend-unreachable errors from proxy calls, but not JS crashes.
  // Keep this strict and adjust only when you see a legitimate expected error pattern.
  const unexpected = consoleErrors.filter((e) => !/Failed to fetch|NetworkError|ECONNREFUSED/i.test(e));
  expect(unexpected).toEqual([]);
});

