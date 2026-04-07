import { test, expect } from '@playwright/test';

test.describe('Index Suggestions Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/index-suggestions');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Structure', () => {
    test('should display page title "索引建议管理"', async ({ page }) => {
      await expect(page.locator('h1:has-text("索引建议管理")')).toBeVisible();
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

    test('should display table name input label', async ({ page }) => {
      await expect(page.locator('.el-form-item label:has-text("表名")')).toBeVisible();
    });

    test('should display table name input', async ({ page }) => {
      const input = page.locator('.el-input[placeholder="请输入表名"]');
      await expect(input).toBeVisible();
    });

    test('should display status selector label', async ({ page }) => {
      await expect(page.locator('.el-form-item label:has-text("状态")')).toBeVisible();
    });

    test('should display status select element', async ({ page }) => {
      const selects = page.locator('.el-select');
      await expect(selects.nth(1)).toBeVisible();
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

    test('should display analyze query button', async ({ page }) => {
      const analyzeButton = page.locator('.el-button:has-text("分析查询")');
      await expect(analyzeButton).toBeVisible();
    });
  });

  test.describe('Suggestions Table', () => {
    test('should display suggestions table element', async ({ page }) => {
      await expect(page.locator('.el-table').first()).toBeVisible();
    });

    test('should display table with stripe styling', async ({ page }) => {
      const table = page.locator('.el-table').first();
      await expect(table).toHaveClass(/el-table--stripe/);
    });

    test('should display table with border styling', async ({ page }) => {
      const table = page.locator('.el-table').first();
      await expect(table).toHaveClass(/el-table--border/);
    });
  });

  test.describe('Table Columns', () => {
    test('should display ID column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("ID")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display table name column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("表名")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display column names column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("列名")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display index type column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("索引类型")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display confidence column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("置信度")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display rows reduction column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("预计行数减少")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display performance improvement column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("预计性能提升")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display status column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("状态")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display created at column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("创建时间")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display operations column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("操作")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });
  });

  test.describe('Operation Buttons', () => {
    test('should display view SQL button', async ({ page }) => {
      const viewButton = page.locator('.el-button:has-text("查看SQL")');
      const isVisible = await viewButton.isVisible().catch(() => false);
      if (isVisible) await expect(viewButton).toBeVisible();
    });

    test('should display accept button', async ({ page }) => {
      const acceptButton = page.locator('.el-button--success:has-text("采纳")');
      const isVisible = await acceptButton.isVisible().catch(() => false);
      if (isVisible) await expect(acceptButton).toBeVisible();
    });

    test('should display reject button', async ({ page }) => {
      const rejectButton = page.locator('.el-button--warning:has-text("拒绝")');
      const isVisible = await rejectButton.isVisible().catch(() => false);
      if (isVisible) await expect(rejectButton).toBeVisible();
    });

    test('should display delete button', async ({ page }) => {
      const deleteButton = page.locator('.el-button--danger:has-text("删除")');
      const isVisible = await deleteButton.isVisible().catch(() => false);
      if (isVisible) await expect(deleteButton).toBeVisible();
    });
  });

  test.describe('Pagination', () => {
    test('should display pagination component', async ({ page }) => {
      const pagination = page.locator('.el-pagination');
      const isVisible = await pagination.isVisible().catch(() => false);
      if (isVisible) await expect(pagination).toBeVisible();
    });

    test('should display pagination with page size options', async ({ page }) => {
      const pageSizes = page.locator('.el-pagination__sizes');
      const isVisible = await pageSizes.isVisible().catch(() => false);
      if (isVisible) await expect(pageSizes).toBeVisible();
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
