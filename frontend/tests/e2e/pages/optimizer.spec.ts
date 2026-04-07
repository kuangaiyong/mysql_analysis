import { test, expect } from '@playwright/test';

test.describe('Optimizer Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/optimizer');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Structure', () => {
    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display page title', async ({ page }) => {
      await expect(page.locator('text=优化器分析')).toBeVisible();
    });

    test('should display connection and SQL input card', async ({ page }) => {
      await expect(page.locator('.el-card').first()).toBeVisible();
    });

    test('should display form element', async ({ page }) => {
      await expect(page.locator('.el-form')).toBeVisible();
    });

    test('should display form with model', async ({ page }) => {
      await expect(page.locator('.el-form')).toHaveAttribute('style', /display: block/);
    });
  });

  test.describe('Connection Section', () => {
    test('should display connection label', async ({ page }) => {
      await expect(page.locator('text=连接')).toBeVisible();
    });

    test('should display connection selector', async ({ page }) => {
      await expect(page.locator('.el-select')).toBeVisible();
    });

    test('should have correct placeholder for connection selector', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await expect(select).toHaveAttribute('placeholder', '请选择连接');
    });

    test('should display connection option with host info', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      await expect(page.locator('.connection-option')).toBeVisible();
    });

    test('should display connection info in option', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      await expect(page.locator('.connection-info')).toBeVisible();
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
      await expect(textarea).toHaveAttribute('placeholder', /输入要分析的SQL语句/);
    });

    test('should display hint text', async ({ page }) => {
      await expect(page.locator('.sql-hint')).toBeVisible();
    });

    test('should display hint about optimizer trace', async ({ page }) => {
      await expect(page.locator('text=优化器追踪')).toBeVisible();
    });

    test('should be able to type in textarea', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM users WHERE id = 1');
      await expect(textarea).toHaveValue('SELECT * FROM users WHERE id = 1');
    });
  });

  test.describe('Action Buttons', () => {
    test('should display analyze button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("分析优化器")')).toBeVisible();
    });

    test('should display clear button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("清空")')).toBeVisible();
    });

    test('should analyze button be disabled without connection', async ({ page }) => {
      const button = page.locator('.el-button:has-text("分析优化器")');
      await expect(button).toBeDisabled();
    });

    test('should analyze button be disabled without SQL', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      const options = page.locator('.el-select-dropdown__item');
      const count = await options.count();
      if (count > 0) {
        await options.first().click();
        const button = page.locator('.el-button:has-text("分析优化器")');
        await expect(button).toBeDisabled();
      }
    });

    test('should enable analyze button when connection and SQL provided', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      const options = page.locator('.el-select-dropdown__item');
      const count = await options.count();
      if (count > 0) {
        await options.first().click();
        const textarea = page.locator('.el-textarea textarea');
        await textarea.fill('SELECT * FROM users WHERE id = 1');
        const button = page.locator('.el-button:has-text("分析优化器")');
        await expect(button).toBeEnabled();
      }
    });
  });

  test.describe('Results Section', () => {
    test('should display results card after analysis', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      const options = page.locator('.el-select-dropdown__item');
      const count = await options.count();
      if (count > 0) {
        await options.first().click();
        const textarea = page.locator('.el-textarea textarea');
        await textarea.fill('SELECT * FROM users WHERE id = 1');
        const analyzeButton = page.locator('.el-button:has-text("分析优化器")');
        await analyzeButton.click();
        await page.waitForTimeout(1000);
        const resultsCard = page.locator('.el-card').nth(1);
        await expect(resultsCard).toBeVisible();
      }
    });

    test('should display results header', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      const options = page.locator('.el-select-dropdown__item');
      const count = await options.count();
      if (count > 0) {
        await options.first().click();
        const textarea = page.locator('.el-textarea textarea');
        await textarea.fill('SELECT * FROM users WHERE id = 1');
        const analyzeButton = page.locator('.el-button:has-text("分析优化器")');
        await analyzeButton.click();
        await page.waitForTimeout(1000);
        await expect(page.locator('.card-header')).toBeVisible();
      }
    });

    test('should display trace results label', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      const options = page.locator('.el-select-dropdown__item');
      const count = await options.count();
      if (count > 0) {
        await options.first().click();
        const textarea = page.locator('.el-textarea textarea');
        await textarea.fill('SELECT * FROM users WHERE id = 1');
        const analyzeButton = page.locator('.el-button:has-text("分析优化器")');
        await analyzeButton.click();
        await page.waitForTimeout(1000);
        await expect(page.locator('text=追踪结果')).toBeVisible();
      }
    });

    test('should display trace viewer component', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      const options = page.locator('.el-select-dropdown__item');
      const count = await options.count();
      if (count > 0) {
        await options.first().click();
        const textarea = page.locator('.el-textarea textarea');
        await textarea.fill('SELECT * FROM users WHERE id = 1');
        const analyzeButton = page.locator('.el-button:has-text("分析优化器")');
        await analyzeButton.click();
        await page.waitForTimeout(1000);
        await expect(page.locator('.trace-viewer, .el-table')).toBeVisible();
      }
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

    test('should loading state show during analysis', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      const options = page.locator('.el-select-dropdown__item');
      const count = await options.count();
      if (count > 0) {
        await options.first().click();
        const textarea = page.locator('.el-textarea textarea');
        await textarea.fill('SELECT * FROM users WHERE id = 1');
        const analyzeButton = page.locator('.el-button:has-text("分析优化器")');
        await analyzeButton.click();
        await expect(page.locator('.el-button:has-text("分析优化器")')).toHaveClass(/is-loading/);
      }
    });
  });

  test.describe('Layout and Styling', () => {
    test('should have card margin styling', async ({ page }) => {
      await expect(page.locator('.card-margin')).toBeVisible();
    });

    test('should have connection option styling', async ({ page }) => {
      await expect(page.locator('.connection-option')).toBeVisible();
    });

    test('should have sql hint styling', async ({ page }) => {
      await expect(page.locator('.sql-hint')).toBeVisible();
    });

    test('should have card header styling', async ({ page }) => {
      await expect(page.locator('.card-header')).toHaveCSS('display', 'flex');
    });

    test('should have proper form layout', async ({ page }) => {
      await expect(page.locator('.el-form-item')).toBeVisible();
    });

    test('should have el-row layout', async ({ page }) => {
      await expect(page.locator('.el-row')).toBeVisible();
    });

    test('should have el-col layout', async ({ page }) => {
      await expect(page.locator('.el-col')).toBeVisible();
    });

    test('should responsive layout work', async ({ page }) => {
      await page.setViewportSize({ width: 1200, height: 800 });
      await page.waitForTimeout(300);
      await expect(page.locator('.el-col')).toBeVisible();

      await page.setViewportSize({ width: 768, height: 600 });
      await page.waitForTimeout(300);
      await expect(page.locator('.el-col')).toBeVisible();
    });
  });
});
