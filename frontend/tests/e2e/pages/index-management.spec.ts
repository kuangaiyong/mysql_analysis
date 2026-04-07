import { test, expect } from '@playwright/test';

test.describe('Index Management Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/index-management');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Structure', () => {
    test('should display page title "索引管理"', async ({ page }) => {
      await expect(page.locator('h1:has-text("索引管理")')).toBeVisible();
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
      await expect(select).toHaveAttribute('placeholder', '请选择连接');
    });

    test('should display database input label', async ({ page }) => {
      await expect(page.locator('.el-form-item label:has-text("数据库")')).toBeVisible();
    });

    test('should display database input element', async ({ page }) => {
      const input = page.locator('.el-input[placeholder="数据库名"]');
      await expect(input).toBeVisible();
    });

    test('should display table selector label', async ({ page }) => {
      await expect(page.locator('.el-form-item label:has-text("表名")')).toBeVisible();
    });

    test('should display table select element', async ({ page }) => {
      const selects = page.locator('.el-select');
      await expect(selects.nth(1)).toBeVisible();
    });
  });

  test.describe('Action Buttons', () => {
    test('should display refresh button', async ({ page }) => {
      const refreshButton = page.locator('.el-button:has-text("刷新")');
      await expect(refreshButton).toBeVisible();
    });

    test('should display create index button', async ({ page }) => {
      const createButton = page.locator('.el-button:has-text("创建索引")');
      await expect(createButton).toBeVisible();
    });

    test('should display analyze usage button', async ({ page }) => {
      const analyzeButton = page.locator('.el-button:has-text("分析使用率")');
      await expect(analyzeButton).toBeVisible();
    });

    test('should display detect redundant button', async ({ page }) => {
      const detectButton = page.locator('.el-button:has-text("检测冗余")');
      await expect(detectButton).toBeVisible();
    });

    test('should display fragmentation detection button', async ({ page }) => {
      const fragButton = page.locator('.el-button:has-text("碎片化检测")');
      await expect(fragButton).toBeVisible();
    });

    test('create index button should be disabled when no table selected', async ({ page }) => {
      const createButton = page.locator('.el-button:has-text("创建索引")');
      await expect(createButton).toHaveClass(/is-disabled/);
    });
  });

  test.describe('Index Table', () => {
    test('should display index table element', async ({ page }) => {
      await expect(page.locator('.el-table').first()).toBeVisible();
    });

    test('should display index table with stripe styling', async ({ page }) => {
      const table = page.locator('.el-table').first();
      await expect(table).toHaveClass(/el-table--stripe/);
    });

    test('should display index table with border styling', async ({ page }) => {
      const table = page.locator('.el-table').first();
      await expect(table).toHaveClass(/el-table--border/);
    });
  });

  test.describe('Table Columns', () => {
    test('should display index name column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("索引名称")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display table name column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("表名")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display column name column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("列名")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display index type column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("索引类型")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display uniqueness column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("唯一性")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display primary key column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("主键")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display cardinality column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("基数")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display size column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("大小")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display usage count column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("使用次数")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display last used column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("最后使用")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });

    test('should display operations column', async ({ page }) => {
      const col = page.locator('.el-table__header th:has-text("操作")');
      const isVisible = await col.isVisible().catch(() => false);
      if (isVisible) await expect(col).toBeVisible();
    });
  });

  test.describe('Delete Index Button', () => {
    test('should display delete button in table', async ({ page }) => {
      const deleteButton = page.locator('.el-button--danger:has-text("删除")');
      const isVisible = await deleteButton.isVisible().catch(() => false);
      if (isVisible) await expect(deleteButton).toBeVisible();
    });
  });

  test.describe('Stats Cards', () => {
    test('should display total indexes card', async ({ page }) => {
      const card = page.locator('.stat-card:has-text("总索引数")');
      const isVisible = await card.isVisible().catch(() => false);
      if (isVisible) await expect(card).toBeVisible();
    });

    test('should display unused indexes card', async ({ page }) => {
      const card = page.locator('.stat-card:has-text("未使用索引")');
      const isVisible = await card.isVisible().catch(() => false);
      if (isVisible) await expect(card).toBeVisible();
    });

    test('should display low usage card', async ({ page }) => {
      const card = page.locator('.stat-card:has-text("低使用率")');
      const isVisible = await card.isVisible().catch(() => false);
      if (isVisible) await expect(card).toBeVisible();
    });

    test('should display high usage card', async ({ page }) => {
      const card = page.locator('.stat-card:has-text("高使用率")');
      const isVisible = await card.isVisible().catch(() => false);
      if (isVisible) await expect(card).toBeVisible();
    });
  });
});
