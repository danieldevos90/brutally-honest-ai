const { expect } = require("@playwright/test");

async function loginAsAdmin(page) {
  await page.goto("/login");
  await page.locator("#email").fill("admin@brutallyhonest.io");
  await page.locator("#password").fill("brutallyhonest2024");
  await page.locator("#login-btn").click();
  await page.waitForURL("**/");
  await expect(page).toHaveTitle(/Home - Brutally Honest/);
}

module.exports = { loginAsAdmin };

