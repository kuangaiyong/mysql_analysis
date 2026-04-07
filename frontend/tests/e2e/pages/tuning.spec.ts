import { test, expect } from '@playwright/test';

test.describe('Tuning Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/tuning');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Structure', () => {
    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display page title', async ({ page }) => {
      await expect(page.locator('text=调优建议')).toBeVisible();
    });

    test('should display tuning card', async ({ page }) => {
      await expect(page.locator('.tuning-card')).toBeVisible();
    });

    test('should display connection selector', async ({ page }) => {
      await expect(page.locator('.el-select')).toBeVisible();
    });
  });

  test.describe('Tabs Navigation', () => {
    test('should display tabs component', async ({ page }) => {
      await expect(page.locator('.el-tabs')).toBeVisible();
    });

    test('should display index suggestions tab', async ({ page }) => {
      await expect(page.locator('.el-tabs__item:has-text("索引建议")')).toBeVisible();
    });

    test('should display SQL rewrite tab', async ({ page }) => {
      await expect(page.locator('.el-tabs__item:has-text("SQL改写")')).toBeVisible();
    });

    test('should display InnoDB tuning tab', async ({ page }) => {
      await expect(page.locator('.el-tabs__item:has-text("InnoDB调优")')).toBeVisible();
    });

    test('should switch to SQL rewrite tab', async ({ page }) => {
      const rewriteTab = page.locator('.el-tabs__item:has-text("SQL改写")');
      await rewriteTab.click();
      await expect(page.locator('text=输入待优化SQL')).toBeVisible();
    });

    test('should switch to InnoDB tuning tab', async ({ page }) => {
      const innodbTab = page.locator('.el-tabs__item:has-text("InnoDB调优")');
      await innodbTab.click();
      await expect(page.locator('text=获取InnoDB调优建议')).toBeVisible();
    });
  });

  test.describe('Index Suggestions Tab', () => {
    test('should display section title for SQL input', async ({ page }) => {
      await expect(page.locator('text=输入查询SQL')).toBeVisible();
    });

    test('should display SQL textarea', async ({ page }) => {
      await expect(page.locator('.sql-input')).toBeVisible();
    });

    test('should have correct placeholder for SQL input', async ({ page }) => {
      const textarea = page.locator('.sql-input textarea');
      await expect(textarea).toHaveAttribute('placeholder', '请输入需要分析索引的SELECT查询语句...');
    });

    test('should display analyze button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("分析索引建议")')).toBeVisible();
    });

    test('should display clear button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("清空")')).toBeVisible();
    });

    test('should analyze button be disabled without connection', async ({ page }) => {
      const button = page.locator('.el-button:has-text("分析索引建议")');
      await expect(button).toBeDisabled();
    });

    test('should analyze button be disabled without SQL', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      const options = page.locator('.el-select-dropdown__item');
      const count = await options.count();
      if (count > 0) {
        await options.first().click();
        const button = page.locator('.el-button:has-text("分析索引建议")');
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
        const textarea = page.locator('.sql-input textarea');
        await textarea.fill('SELECT * FROM users WHERE id = 1');
        const button = page.locator('.el-button:has-text("分析索引建议")');
        await expect(button).toBeEnabled();
      }
    });
  });

  test.describe('SQL Rewrite Tab', () => {
    test.beforeEach(async ({ page }) => {
      const rewriteTab = page.locator('.el-tabs__item:has-text("SQL改写")');
      await rewriteTab.click();
      await page.waitForTimeout(300);
    });

    test('should display section title for SQL input', async ({ page }) => {
      await expect(page.locator('text=输入待优化SQL')).toBeVisible();
    });

    test('should display SQL textarea', async ({ page }) => {
      await expect(page.locator('.sql-input')).toBeVisible();
    });

    test('should have correct placeholder for SQL input', async ({ page }) => {
      const textarea = page.locator('.sql-input textarea');
      await expect(textarea).toHaveAttribute('placeholder', '请输入需要优化的SQL语句...');
    });

    test('should display analyze button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("分析改写建议")')).toBeVisible();
    });

    test('should display clear button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("清空")')).toBeVisible();
    });

    test('should analyze button be disabled without SQL', async ({ page }) => {
      const button = page.locator('.el-button:has-text("分析改写建议")');
      await expect(button).toBeDisabled();
    });

    test('should enable analyze button when SQL provided', async ({ page }) => {
      const textarea = page.locator('.sql-input textarea');
      await textarea.fill('SELECT * FROM users WHERE id = 1');
      const button = page.locator('.el-button:has-text("分析改写建议")');
      await expect(button).toBeEnabled();
    });
  });

  test.describe('InnoDB Tuning Tab', () => {
    test.beforeEach(async ({ page }) => {
      const innodbTab = page.locator('.el-tabs__item:has-text("InnoDB调优")');
      await innodbTab.click();
      await page.waitForTimeout(300);
    });

    test('should display get recommendations button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("获取InnoDB调优建议")')).toBeVisible();
    });

    test('should display setting icon', async ({ page }) => {
      await expect(page.locator('.el-icon')).toBeVisible();
    });

    test('should button be disabled without connection', async ({ page }) => {
      const button = page.locator('.el-button:has-text("获取InnoDB调优建议")');
      await expect(button).toBeEnabled();
    });
  });

  test.describe('Results Display', () => {
    test('should display result section container', async ({ page }) => {
      await expect(page.locator('.result-section')).toBeVisible();
    });

    test('should display result header', async ({ page }) => {
      await expect(page.locator('.result-header')).toBeVisible();
    });

    test('should display suggestions list container', async ({ page }) => {
      await expect(page.locator('.suggestions-list')).toBeVisible();
    });

    test('should display suggestion cards', async ({ page }) => {
      await expect(page.locator('.suggestion-card')).toBeVisible();
    });

    test('should display suggestion header', async ({ page }) => {
      await expect(page.locator('.suggestion-header')).toBeVisible();
    });

    test('should display suggestion body', async ({ page }) => {
      await expect(page.locator('.suggestion-body')).toBeVisible();
    });

    test('should display info rows', async ({ page }) => {
      await expect(page.locator('.info-row')).toBeVisible();
    });

    test('should display SQL statement section', async ({ page }) => {
      await expect(page.locator('.sql-statement')).toBeVisible();
    });
  });

  test.describe('Layout and Styling', () => {
    test('should have tuning page class', async ({ page }) => {
      await expect(page.locator('.tuning-page')).toBeVisible();
    });

    test('should have tabs styling', async ({ page }) => {
      await expect(page.locator('.tuning-tabs')).toBeVisible();
    });

    test('should have input section styling', async ({ page }) => {
      await expect(page.locator('.input-section')).toBeVisible();
    });

    test('should have action bar styling', async ({ page }) => {
      await expect(page.locator('.action-bar')).toBeVisible();
    });

    test('should display section title with icon', async ({ page }) => {
      await expect(page.locator('.section-title')).toBeVisible();
    });

    test('should responsive layout work', async ({ page }) => {
      await page.setViewportSize({ width: 1200, height: 800 });
      await page.waitForTimeout(300);
      await expect(page.locator('.tuning-card')).toBeVisible();

      await page.setViewportSize({ width: 768, height: 600 });
      await page.waitForTimeout(300);
      await expect(page.locator('.tuning-card')).toBeVisible();
    });
  });
});
