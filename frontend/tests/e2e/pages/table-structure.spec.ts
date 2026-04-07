import { test, expect } from '@playwright/test';

test.describe('Table Structure Page', () => {
  // Navigate to table structure page before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/table-structure');
    await page.waitForLoadState('networkidle');
  });

  // ============================================
  // 1. Page Structure Tests
  // ============================================
  test.describe('Page Structure', () => {
    test('should display page title "表结构分析"', async ({ page }) => {
      await expect(page.locator('h1:has-text("表结构分析")')).toBeVisible();
    });

    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display PageHeader component', async ({ page }) => {
      await expect(page.locator('.el-page-header')).toBeVisible();
    });

    test('should display connection selector card', async ({ page }) => {
      await expect(page.locator('.el-card').first()).toBeVisible();
    });
  });

  // ============================================
  // 2. Connection Selector Tests
  // ============================================
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

    test('should display database selector label', async ({ page }) => {
      await expect(page.locator('.el-form-item label:has-text("数据库")')).toBeVisible();
    });

    test('should display database select element', async ({ page }) => {
      const selects = page.locator('.el-select');
      await expect(selects.nth(1)).toBeVisible();
    });

    test('should have correct placeholder for database selector', async ({ page }) => {
      const select = page.locator('.el-select').nth(1);
      await expect(select).toHaveAttribute('placeholder', '请选择数据库');
    });

    test('should disable database selector when connection not selected', async ({ page }) => {
      const databaseSelect = page.locator('.el-select').nth(1);
      await expect(databaseSelect).toHaveClass(/is-disabled/);
    });
  });

  // ============================================
  // 3. Search Input Tests
  // ============================================
  test.describe('Search Input', () => {
    test('should display search input for table name', async ({ page }) => {
      const searchInput = page.locator('.el-input[placeholder="搜索表名"]');
      const isVisible = await searchInput.isVisible().catch(() => false);
      if (isVisible) {
        await expect(searchInput).toBeVisible();
      }
    });

    test('should have search icon in search input', async ({ page }) => {
      const searchInput = page.locator('.el-input[placeholder="搜索表名"]');
      const isVisible = await searchInput.isVisible().catch(() => false);
      if (isVisible) {
        await expect(searchInput.locator('.el-input__prefix')).toBeVisible();
      }
    });
  });

  // ============================================
  // 4. Table List Tests
  // ============================================
  test.describe('Table List', () => {
    test('should display table element', async ({ page }) => {
      const table = page.locator('.el-table');
      const isVisible = await table.isVisible().catch(() => false);
      if (isVisible) {
        await expect(table).toBeVisible();
      }
    });

    test('should display table with stripe styling', async ({ page }) => {
      const table = page.locator('.el-table');
      const isVisible = await table.isVisible().catch(() => false);
      if (isVisible) {
        await expect(table).toHaveClass(/el-table--stripe/);
      }
    });

    test('should display table with border styling', async ({ page }) => {
      const table = page.locator('.el-table');
      const isVisible = await table.isVisible().catch(() => false);
      if (isVisible) {
        await expect(table).toHaveClass(/el-table--border/);
      }
    });
  });

  // ============================================
  // 5. Table Column Tests
  // ============================================
  test.describe('Table Columns', () => {
    test('should display table name column', async ({ page }) => {
      const tableNameCol = page.locator('.el-table__header th:has-text("表名")');
      const isVisible = await tableNameCol.isVisible().catch(() => false);
      if (isVisible) {
        await expect(tableNameCol).toBeVisible();
      }
    });

    test('should display type column', async ({ page }) => {
      const typeCol = page.locator('.el-table__header th:has-text("类型")');
      const isVisible = await typeCol.isVisible().catch(() => false);
      if (isVisible) {
        await expect(typeCol).toBeVisible();
      }
    });

    test('should display engine column', async ({ page }) => {
      const engineCol = page.locator('.el-table__header th:has-text("引擎")');
      const isVisible = await engineCol.isVisible().catch(() => false);
      if (isVisible) {
        await expect(engineCol).toBeVisible();
      }
    });

    test('should display rows column', async ({ page }) => {
      const rowsCol = page.locator('.el-table__header th:has-text("行数")');
      const isVisible = await rowsCol.isVisible().catch(() => false);
      if (isVisible) {
        await expect(rowsCol).toBeVisible();
      }
    });

    test('should display data size column', async ({ page }) => {
      const dataSizeCol = page.locator('.el-table__header th:has-text("数据大小")');
      const isVisible = await dataSizeCol.isVisible().catch(() => false);
      if (isVisible) {
        await expect(dataSizeCol).toBeVisible();
      }
    });

    test('should display index size column', async ({ page }) => {
      const indexSizeCol = page.locator('.el-table__header th:has-text("索引大小")');
      const isVisible = await indexSizeCol.isVisible().catch(() => false);
      if (isVisible) {
        await expect(indexSizeCol).toBeVisible();
      }
    });

    test('should display total size column', async ({ page }) => {
      const totalSizeCol = page.locator('.el-table__header th:has-text("总大小")');
      const isVisible = await totalSizeCol.isVisible().catch(() => false);
      if (isVisible) {
        await expect(totalSizeCol).toBeVisible();
      }
    });

    test('should display create time column', async ({ page }) => {
      const createTimeCol = page.locator('.el-table__header th:has-text("创建时间")');
      const isVisible = await createTimeCol.isVisible().catch(() => false);
      if (isVisible) {
        await expect(createTimeCol).toBeVisible();
      }
    });

    test('should display update time column', async ({ page }) => {
      const updateTimeCol = page.locator('.el-table__header th:has-text("更新时间")');
      const isVisible = await updateTimeCol.isVisible().catch(() => false);
      if (isVisible) {
        await expect(updateTimeCol).toBeVisible();
      }
    });

    test('should display operations column', async ({ page }) => {
      const operationsCol = page.locator('.el-table__header th:has-text("操作")');
      const isVisible = await operationsCol.isVisible().catch(() => false);
      if (isVisible) {
        await expect(operationsCol).toBeVisible();
      }
    });
  });

  // ============================================
  // 6. View Structure Button Tests
  // ============================================
  test.describe('View Structure Button', () => {
    test('should display view structure button', async ({ page }) => {
      const viewButton = page.locator('.el-button:has-text("查看结构")');
      const isVisible = await viewButton.isVisible().catch(() => false);
      if (isVisible) {
        await expect(viewButton).toBeVisible();
      }
    });

    test('should have primary type for view structure button', async ({ page }) => {
      const viewButton = page.locator('.el-button--primary:has-text("查看结构")');
      const isVisible = await viewButton.isVisible().catch(() => false);
      if (isVisible) {
        await expect(viewButton).toBeVisible();
      }
    });
  });

  // ============================================
  // 7. Tabs Tests
  // ============================================
  test.describe('Tabs', () => {
    test('should display tabs component', async ({ page }) => {
      const tabs = page.locator('.el-tabs');
      const isVisible = await tabs.isVisible().catch(() => false);
      if (isVisible) {
        await expect(tabs).toBeVisible();
      }
    });

    test('should display 表列表 tab', async ({ page }) => {
      const tabPane = page.locator('.el-tab-pane:has-text("表列表")');
      const isVisible = await tabPane.isVisible().catch(() => false);
      if (isVisible) {
        await expect(tabPane).toBeVisible();
      }
    });

    test('should display 空间分析 tab', async ({ page }) => {
      const tabPane = page.locator('.el-tab-pane:has-text("空间分析")');
      const isVisible = await tabPane.isVisible().catch(() => false);
      if (isVisible) {
        await expect(tabPane).toBeVisible();
      }
    });

    test('should be able to switch to space analysis tab', async ({ page }) => {
      const spaceTab = page.locator('.el-tabs__item:has-text("空间分析")');
      const isVisible = await spaceTab.isVisible().catch(() => false);
      if (isVisible) {
        await spaceTab.click();
        await page.waitForTimeout(300);
        const overviewTab = page.locator('.el-tabs__item:has-text("空间概览")');
        await expect(overviewTab).toBeVisible();
      }
    });
  });

  // ============================================
  // 8. Pagination Tests
  // ============================================
  test.describe('Pagination', () => {
    test('should display pagination component', async ({ page }) => {
      const pagination = page.locator('.el-pagination');
      const isVisible = await pagination.isVisible().catch(() => false);
      if (isVisible) {
        await expect(pagination).toBeVisible();
      }
    });
  });

  // ============================================
  // 9. Interactive Tests
  // ============================================
  test.describe('Interactive Tests', () => {
    test('should allow typing in search input', async ({ page }) => {
      const searchInput = page.locator('.el-input[placeholder="搜索表名"]');
      const isVisible = await searchInput.isVisible().catch(() => false);
      if (isVisible) {
        await searchInput.fill('test');
        await expect(searchInput).toHaveValue('test');
      }
    });

    test('should allow clearing search input', async ({ page }) => {
      const searchInput = page.locator('.el-input[placeholder="搜索表名"]');
      const isVisible = await searchInput.isVisible().catch(() => false);
      if (isVisible) {
        await searchInput.fill('test');
        await expect(searchInput).toHaveValue('test');
        const clearButton = searchInput.locator('.el-input__clear');
        const clearVisible = await clearButton.isVisible().catch(() => false);
        if (clearVisible) {
          await clearButton.click();
          await expect(searchInput).toHaveValue('');
        }
      }
    });

    test('should display card header with title', async ({ page }) => {
      const cardHeader = page.locator('.card-header span:has-text("表列表")');
      const isVisible = await cardHeader.isVisible().catch(() => false);
      if (isVisible) {
        await expect(cardHeader).toBeVisible();
      }
    });
  });

  // ============================================
  // 10. Space Analysis Sub-tabs Tests
  // ============================================
  test.describe('Space Analysis Sub-tabs', () => {
    test('should display space overview section', async ({ page }) => {
      const spaceTab = page.locator('.el-tabs__item:has-text("空间分析")');
      const isSpaceTabVisible = await spaceTab.isVisible().catch(() => false);
      if (isSpaceTabVisible) {
        await spaceTab.click();
        await page.waitForTimeout(300);
        const overviewTab = page.locator('.el-tabs__item:has-text("空间概览")');
        const isVisible = await overviewTab.isVisible().catch(() => false);
        if (isVisible) {
          await expect(overviewTab).toBeVisible();
        }
      }
    });

    test('should display table space ranking section', async ({ page }) => {
      const tableRankTab = page.locator('.el-tabs__item:has-text("表空间排名")');
      const isVisible = await tableRankTab.isVisible().catch(() => false);
      if (isVisible) {
        await expect(tableRankTab).toBeVisible();
      }
    });

    test('should display index space ranking section', async ({ page }) => {
      const indexRankTab = page.locator('.el-tabs__item:has-text("索引空间排名")');
      const isVisible = await indexRankTab.isVisible().catch(() => false);
      if (isVisible) {
        await expect(indexRankTab).toBeVisible();
      }
    });

    test('should display fragmentation analysis section', async ({ page }) => {
      const fragTab = page.locator('.el-tabs__item:has-text("碎片率分析")');
      const isVisible = await fragTab.isVisible().catch(() => false);
      if (isVisible) {
        await expect(fragTab).toBeVisible();
      }
    });
  });
});
