const { test, expect } = require("@playwright/test");
const { loginAsAdmin } = require("./helpers");

test("documents: upload -> appears in library -> delete", async ({ page }) => {
  await loginAsAdmin(page);

  await page.goto("/documents");
  await expect(page).toHaveTitle(/Documents - Brutally Honest/);

  // Upload tab is default; attach a small text file.
  const fileContent = "Brutally Honest AI test document. Fish can swim.";
  await page.setInputFiles("#file-input", {
    name: "e2e_test_doc.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(fileContent, "utf8"),
  });

  // Upload button should appear in selected-files section.
  await expect(page.locator("#selected-files")).toBeVisible();
  await page.locator("#selected-files").getByRole("button", { name: /Upload/i }).click();

  // Wait until progress shows Done for the one item.
  const progressItem = page.locator("#upload-progress-list .upload-item").first();
  await expect(progressItem).toBeVisible();
  await expect(progressItem.locator(".upload-status")).toContainText(/Done/i, { timeout: 30_000 });

  // Go to library tab and ensure the uploaded doc is listed.
  await page.locator("#tab-library").click();
  await expect(page.locator("#tab-content-library")).toBeVisible();
  await page.getByRole("button", { name: "Refresh" }).click();

  const docRow = page.locator(".document-item", { hasText: "e2e_test_doc.txt" });
  await expect(docRow).toBeVisible({ timeout: 15_000 });

  // Delete it.
  page.once("dialog", (dialog) => dialog.accept());
  await docRow.getByRole("button", { name: "Delete" }).click();

  // It should disappear after refresh.
  await page.getByRole("button", { name: "Refresh" }).click();
  await expect(docRow).toHaveCount(0);
});

