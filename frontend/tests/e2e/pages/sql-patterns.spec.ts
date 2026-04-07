import { test, expect } from '@playwright/test';

test.describe('SQL Patterns Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/sql-patterns');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Structure', () => {
    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display page title', async ({ page }) => {
      await expect(page.locator('text=SQL反模式检测')).toBeVisible();
    });

    test('should display SQL input card', async ({ page }) => {
      await expect(page.locator('.el-card').first()).toBeVisible();
    });

    test('should display form element', async ({ page }) => {
      await expect(page.locator('.el-form')).toBeVisible();
    });
  });

  test.describe('SQL Input Section', () => {
    test('should display SQL label', async ({ page }) => {
      await expect(page.locator('text=SQL语句')).toBeVisible();
    });

    test('should display SQL textarea', async ({ page }) => {
      await expect(page.locator('.el-textarea')).toBeVisible();
    });

    test('should have correct placeholder for SQL input', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await expect(textarea).toHaveAttribute('placeholder', /输入要检测的SQL语句/);
    });

    test('should display hint text', async ({ page }) => {
      await expect(page.locator('text=提示')).toBeVisible();
    });

    test('should display hint about common anti-patterns', async ({ page }) => {
      await expect(page.locator('text=检测 SELECT')).toBeVisible();
    });

    test('should display detect button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("检测反模式")')).toBeVisible();
    });

    test('should display clear button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("清空")')).toBeVisible();
    });

    test('should detect button be disabled without SQL', async ({ page }) => {
      const button = page.locator('.el-button:has-text("检测反模式")');
      await expect(button).toBeDisabled();
    });

    test('should enable detect button when SQL provided', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users WHERE id = 1');
      const button = page.locator('.el-button:has-text("检测反模式")');
      await expect(button).toBeEnabled();
    });

    test('should be able to type in textarea', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users');
      await expect(textarea).toHaveValue('SELECT * FROM users');
    });
  });

  test.describe('Results Section', () => {
    test('should display results card after detection', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users WHERE status = 1');
      const detectButton = page.locator('.el-button:has-text("检测反模式")');
      await detectButton.click();
      await page.waitForTimeout(1000);
      const resultsCard = page.locator('.el-card').nth(1);
      await expect(resultsCard).toBeVisible();
    });

    test('should display results header', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users WHERE status = 1');
      const detectButton = page.locator('.el-button:has-text("检测反模式")');
      await detectButton.click();
      await page.waitForTimeout(1000);
      await expect(page.locator('text=检测结果')).toBeVisible();
    });

    test('should display summary tag', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users WHERE status = 1');
      const detectButton = page.locator('.el-button:has-text("检测反模式")');
      await detectButton.click();
      await page.waitForTimeout(1000);
      await expect(page.locator('.el-tag')).toBeVisible();
    });

    test('should display pattern list component', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users WHERE status = 1');
      const detectButton = page.locator('.el-button:has-text("检测反模式")');
      await detectButton.click();
      await page.waitForTimeout(1000);
      await expect(page.locator('.pattern-list, .el-table')).toBeVisible();
    });
  });

  test.describe('Pattern Categories', () => {
    test('should display pattern severity tags', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users WHERE status = 1');
      const detectButton = page.locator('.el-button:has-text("检测反模式")');
      await detectButton.click();
      await page.waitForTimeout(1000);
      await expect(page.locator('.el-tag')).toBeVisible();
    });

    test('should display pattern descriptions', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users WHERE status = 1');
      const detectButton = page.locator('.el-button:has-text("检测反模式")');
      await detectButton.click();
      await page.waitForTimeout(1000);
      await expect(page.locator('.el-descriptions')).toBeVisible();
    });

    test('should display pattern fix suggestions', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users WHERE status = 1');
      const detectButton = page.locator('.el-button:has-text("检测反模式")');
      await detectButton.click();
      await page.waitForTimeout(1000);
      await expect(page.locator('text=修复建议')).toBeVisible();
    });
  });

  test.describe('Interactive Elements', () => {
    test('should clear button work', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users');
      const clearButton = page.locator('.el-button:has-text("清空")');
      await clearButton.click();
      await expect(textarea).toHaveValue('');
    });

    test('should loading state show during detection', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users WHERE status = 1');
      const detectButton = page.locator('.el-button:has-text("检测反模式")');
      await detectButton.click();
      await expect(page.locator('.el-button:has-text("检测反模式")')).toHaveClass(/is-loading/);
    });
  });

  test.describe('Layout and Styling', () => {
    test('should have proper card margin', async ({ page }) => {
      await expect(page.locator('.card-margin')).toBeVisible();
    });

    test('should have card header styling', async ({ page }) => {
      await expect(page.locator('.card-header')).toBeVisible();
    });

    test('should have form item styling', async ({ page }) => {
      await expect(page.locator('.el-form-item')).toBeVisible();
    });

    test('should display card header with flex layout', async ({ page }) => {
      await expect(page.locator('.card-header')).toHaveCSS('display', 'flex');
    });

    test('should responsive layout work', async ({ page }) => {
      await page.setViewportSize({ width: 1200, height: 800 });
      await page.waitForTimeout(300);
      await expect(page.locator('.el-textarea')).toBeVisible();

      await page.setViewportSize({ width: 768, height: 600 });
      await page.waitForTimeout(300);
      await expect(page.locator('.el-textarea')).toBeVisible();
    });
  });

  test.describe('Empty States', () => {
    test('should show empty state when no patterns detected', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT id, name FROM users WHERE id = 1');
      const detectButton = page.locator('.el-button:has-text("检测反模式")');
      await detectButton.click();
      await page.waitForTimeout(1000);
      await expect(page.locator('.el-empty')).toBeVisible();
    });
  });
});
