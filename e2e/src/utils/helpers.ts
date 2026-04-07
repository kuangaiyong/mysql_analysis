import { type Page, expect } from '@playwright/test';

export async function checkSuccessMessage(page: Page, message?: string): Promise<void> {
  const successMessage = page.locator('.el-message--success');
  await expect(successMessage).toBeVisible({ timeout: 5000 });
  if (message) {
    await expect(successMessage).toContainText(message);
  }
}

export async function checkErrorMessage(page: Page, message?: string): Promise<void> {
  const errorMessage = page.locator('.el-message--error');
  await expect(errorMessage).toBeVisible({ timeout: 5000 });
  if (message) {
    await expect(errorMessage).toContainText(message);
  }
}

export async function waitForLoadingComplete(page: Page): Promise<void> {
  await page.waitForSelector('.el-loading-mask', { state: 'hidden', timeout: 10000 });
}

export async function fillForm(page: Page, fields: Record<string, string>): Promise<void> {
  for (const [selector, value] of Object.entries(fields)) {
    await page.fill(selector, value);
  }
}

export async function confirmDialog(page: Page): Promise<void> {
  await page.click('.el-message-box__btns button.el-button--primary');
}

export async function cancelDialog(page: Page): Promise<void> {
  await page.click('.el-message-box__btns button.el-button--default');
}
