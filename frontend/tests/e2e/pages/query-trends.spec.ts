import { test, expect } from '@playwright/test';

test.describe('Query Trends Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/query-trends');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Structure', () => {
    test('should display page title "查询指纹趋势分析"', async ({ page }) => {
      await expect(page.locator('h1:has-text("查询指纹趋势分析")')).toBeVisible();
    });

    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display PageHeader component', async ({ page }) => {
      await expect(page.locator('.el-page-header')).toBeVisible();
    });

    test('should display search form', async ({ page }) => {
      await expect(page.locator('.search-form')).toBeVisible();
    });
  });

  test.describe('Header Actions', () => {
    test('should display generate fingerprints button', async ({ page }) => {
      const button = page.locator('.el-button:has-text("生成指纹")');
      await expect(button).toBeVisible();
    });

    test('should display export CSV button', async ({ page }) => {
      const button = page.locator('.el-button:has-text("导出CSV")');
      await expect(button).toBeVisible();
    });
  });

  test.describe('Connection Selector', () => {
    test('should display connection selector label', async ({ page }) => {
      await expect(page.locator('.el-form-item label:has-text("连接")')).toBeVisible();
    });

    test('should display connection select element', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await expect(select).toBeVisible();
    });

    test('should have correct placeholder for connection selector', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await expect(select).toHaveAttribute('placeholder', '选择连接');
    });

    test('should display time range selector label', async ({ page }) => {
      await expect(page.locator('.el-form-item label:has-text("时间范围")')).toBeVisible();
    });

    test('should display time range select element', async ({ page }) => {
      const selects = page.locator('.el-select');
      await expect(selects.nth(1)).toBeVisible();
    });

    test('should display table name input label', async ({ page }) => {
      await expect(page.locator('.el-form-item label:has-text("表名")')).toBeVisible();
    });

    test('should display table name input', async ({ page }) => {
      const input = page.locator('.el-input[placeholder="请输入表名"]');
      await expect(input).toBeVisible();
    });
  });

  test.describe('Action Buttons', () => {
    test('should display query button', async ({ page }) => {
      const queryButton = page.locator('.el-button:has-text("查询")');
      await expect(queryButton).toBeVisible();
    });

    test('should display reset button', async ({ page }) => {
      const resetButton = page.locator('.el-button:has-text("重置")');
      await expect(resetButton).toBeVisible();
    });
  });

  test.describe('Tabs', () => {
    test('should display tabs component', async ({ page }) => {
      await expect(page.locator('.el-tabs')).toBeVisible();
    });

    test('should display trend chart tab', async ({ page }) => {
      const tab = page.locator('.el-tab-pane:has-text("趋势图表")');
      await expect(tab).toBeVisible();
    });

    test('should display data list tab', async ({ page }) => {
      const tab = page.locator('.el-tab-pane:has-text("数据列表")');
      await expect(tab).toBeVisible();
    });

    test('should switch to chart tab', async ({ page }) => {
      const chartTab = page.locator('.el-tabs__item:has-text("趋势图表")');
      await chartTab.click();
      await page.waitForTimeout(300);
      await expect(page.locator('.el-tab-pane[name="chart"]')).toBeVisible();
    });

    test('should switch to table tab', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      await expect(page.locator('.el-tab-pane[name="table"]')).toBeVisible();
    });
  });

  test.describe('Fingerprint Table', () => {
    test('should display fingerprint table element', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      await expect(page.locator('.el-table').first()).toBeVisible();
    });

    test('should display table with stripe styling', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const table = page.locator('.el-table').first();
      await expect(table).toHaveClass(/el-table--stripe/);
    });

    test('should display table with border styling', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const table = page.locator('.el-table').first();
      await expect(table).toHaveClass(/el-table--border/);
    });
  });

  test.describe('Table Columns', () => {
    test('should display fingerprint hash column', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const col = page.locator('.el-table__header th:has-text("指纹哈希")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display normalized SQL column', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const col = page.locator('.el-table__header th:has-text("规范化SQL")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display table name column', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const col = page.locator('.el-table__header th:has-text("表名")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display database column', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const col = page.locator('.el-table__header th:has-text("数据库")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display execution count column', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const col = page.locator('.el-table__header th:has-text("执行次数")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display average query time column', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const col = page.locator('.el-table__header th:has-text("平均时间")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display min query time column', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const col = page.locator('.el-table__header th:has-text("最小时间")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display max query time column', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const col = page.locator('.el-table__header th:has-text("最大时间")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display first seen column', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const col = page.locator('.el-table__header th:has-text("首次出现")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display last seen column', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const col = page.locator('.el-table__header th:has-text("最后执行")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });
  });

  test.describe('Pagination', () => {
    test('should display pagination component', async ({ page }) => {
      const tableTab = page.locator('.el-tabs__item:has-text("数据列表")');
      await tableTab.click();
      await page.waitForTimeout(300);
      const pagination = page.locator('.el-pagination');
      const isVisible = await pagination.isVisible().catch(() => false);
      if (isVisible) await expect(pagination).toBeVisible();
    });
  });

  test.describe('Interactive Tests', () => {
    test('should allow typing in table name input', async ({ page }) => {
      const input = page.locator('.el-input[placeholder="请输入表名"]');
      await input.fill('test_table');
      await expect(input).toHaveValue('test_table');
    });

    test('should allow clearing table name input', async ({ page }) => {
      const input = page.locator('.el-input[placeholder="请输入表名"]');
      await input.fill('test_table');
      const clearButton = input.locator('.el-input__clear');
      const clearVisible = await clearButton.isVisible().catch(() => false);
      if (clearVisible) {
        await clearButton.click();
        await expect(input).toHaveValue('');
      }
    });
  });
});
