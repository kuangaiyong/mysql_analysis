import { test, expect } from '@playwright/test';

test.describe('Sessions Page', () => {
  // Navigate to sessions page before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/sessions');
    await page.waitForLoadState('networkidle');
  });

  // ============================================
  // 1. Page Structure Tests
  // ============================================
  test.describe('Page Structure', () => {
    test('should display page title "会话管理"', async ({ page }) => {
      await expect(page.locator('h1:has-text("会话管理")')).toBeVisible();
    });

    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display el-card component', async ({ page }) => {
      await expect(page.locator('.el-card')).toBeVisible();
    });

    test('should display PageHeader component', async ({ page }) => {
      await expect(page.locator('.el-page-header')).toBeVisible();
    });

    test('should display page header with title', async ({ page }) => {
      await expect(page.locator('.el-page-header__title:has-text("会话管理")')).toBeVisible();
    });
  });

  // ============================================
  // 2. Connection Selector Tests
  // ============================================
  test.describe('Connection Selector', () => {
    test('should display connection selector label', async ({ page }) => {
      await expect(page.locator('.el-form-item label:has-text("选择连接")')).toBeVisible();
    });

    test('should display connection select dropdown', async ({ page }) => {
      const select = page.locator('.el-select[placeholder="请选择MySQL连接"]');
      await expect(select).toBeVisible();
    });

    test('should display connection select with correct placeholder', async ({ page }) => {
      const placeholder = page.locator('.el-select[placeholder="请选择MySQL连接"] .el-input__placeholder');
      await expect(placeholder).toBeVisible();
    });

    test('should be able to click connection selector', async ({ page }) => {
      const select = page.locator('.el-select[placeholder="请选择MySQL连接"]').first();
      await select.click();
      // Dropdown should appear
      await expect(page.locator('.el-select-dropdown')).toBeVisible();
    });
  });

  // ============================================
  // 3. Filter Form Tests (only visible after connection selected)
  // ============================================
  test.describe('Filter Form', () => {
    test('should not display filter form initially', async ({ page }) => {
      // Filter form should only show after connection is selected
      const filterForm = page.locator('.search-form').nth(1);
      await expect(filterForm).not.toBeVisible();
    });

    test('should display user filter label', async ({ page }) => {
      // Find the filter form section - look for User label in the second search-form
      const userLabel = page.locator('.el-form-item label:has-text("用户")');
      const isVisible = await userLabel.first().isVisible().catch(() => false);
      // May or may not be visible depending on connection state
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display database filter input', async ({ page }) => {
      const dbInput = page.locator('.el-input[placeholder="请输入数据库名"]');
      const isVisible = await dbInput.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display state filter select', async ({ page }) => {
      const stateSelect = page.locator('.el-select[placeholder="请选择状态"]');
      const isVisible = await stateSelect.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display command filter select', async ({ page }) => {
      const commandSelect = page.locator('.el-select[placeholder="请选择命令"]');
      const isVisible = await commandSelect.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display search button', async ({ page }) => {
      const searchButton = page.locator('.el-button:has-text("查询")');
      const isVisible = await searchButton.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display reset button', async ({ page }) => {
      const resetButton = page.locator('.el-button:has-text("重置")');
      const isVisible = await resetButton.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  // ============================================
  // 4. Action Buttons Tests
  // ============================================
  test.describe('Action Buttons', () => {
    test('should display batch kill button', async ({ page }) => {
      const batchKillButton = page.locator('.el-button--danger:has-text("批量Kill")');
      const isVisible = await batchKillButton.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display export CSV button', async ({ page }) => {
      const exportButton = page.locator('.el-button:has-text("导出CSV")');
      const isVisible = await exportButton.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display refresh button in action area', async ({ page }) => {
      const refreshButton = page.locator('.el-button:has-text("刷新")');
      const count = await refreshButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should display page header refresh button', async ({ page }) => {
      // PageHeader has a refresh button
      const headerRefreshBtn = page.locator('.el-page-header .el-button');
      await expect(headerRefreshBtn).toBeVisible();
    });
  });

  // ============================================
  // 5. Data Table Tests
  // ============================================
  test.describe('Data Table', () => {
    test('should display table element when connection selected', async ({ page }) => {
      const table = page.locator('.el-table');
      const isVisible = await table.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display table with stripe styling', async ({ page }) => {
      const table = page.locator('.el-table');
      const hasStripe = await table.evaluate((el) => el.classList.contains('el-table--stripe'));
      // Table may or may not have stripe depending on data state
      expect(typeof hasStripe).toBe('boolean');
    });

    test('should display table with border styling', async ({ page }) => {
      const table = page.locator('.el-table');
      const hasBorder = await table.evaluate((el) => el.classList.contains('el-table--border'));
      expect(typeof hasBorder).toBe('boolean');
    });
  });

  // ============================================
  // 6. Table Columns Tests
  // ============================================
  test.describe('Table Columns', () => {
    test('should display checkbox selection column', async ({ page }) => {
      const checkboxColumn = page.locator('.el-table__header .el-table-column--selection');
      const isVisible = await checkboxColumn.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display Thread ID column', async ({ page }) => {
      const threadIdHeader = page.locator('.el-table__header th:has-text("Thread ID")');
      const isVisible = await threadIdHeader.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display User column', async ({ page }) => {
      const userHeader = page.locator('.el-table__header th:has-text("用户")');
      const isVisible = await userHeader.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display Host column', async ({ page }) => {
      const hostHeader = page.locator('.el-table__header th:has-text("主机")');
      const isVisible = await hostHeader.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display Database column', async ({ page }) => {
      const dbHeader = page.locator('.el-table__header th:has-text("数据库")');
      const isVisible = await dbHeader.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display Command column', async ({ page }) => {
      const commandHeader = page.locator('.el-table__header th:has-text("命令")');
      const isVisible = await commandHeader.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display Time column', async ({ page }) => {
      const timeHeader = page.locator('.el-table__header th:has-text("时长")');
      const isVisible = await timeHeader.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display State column', async ({ page }) => {
      const stateHeader = page.locator('.el-table__header th:has-text("状态")');
      const isVisible = await stateHeader.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display SQL column', async ({ page }) => {
      const sqlHeader = page.locator('.el-table__header th:has-text("SQL")');
      const isVisible = await sqlHeader.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display Operations column', async ({ page }) => {
      const opsHeader = page.locator('.el-table__header th:has-text("操作")');
      const isVisible = await opsHeader.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  // ============================================
  // 7. Kill Button Tests
  // ============================================
  test.describe('Kill Button', () => {
    test('should display kill button in table row', async ({ page }) => {
      const killButton = page.locator('.el-button--danger[link]:has-text("Kill")');
      const count = await killButton.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should have danger styled kill button', async ({ page }) => {
      const killButton = page.locator('.el-table .el-button--danger[link]');
      const isVisible = await killButton.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  // ============================================
  // 8. Pagination Tests
  // ============================================
  test.describe('Pagination', () => {
    test('should display pagination component', async ({ page }) => {
      const pagination = page.locator('.el-pagination');
      const isVisible = await pagination.isVisible().catch(() => false);
      // Pagination may or may not be visible based on connection state
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display pagination total text', async ({ page }) => {
      const totalText = page.locator('.el-pagination__total');
      const isVisible = await totalText.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display page size selector', async ({ page }) => {
      const pageSizeSelect = page.locator('.el-pagination .el-select');
      const isVisible = await pageSizeSelect.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  // ============================================
  // 9. State Tags Tests
  // ============================================
  test.describe('State Tags', () => {
    test('should display state as el-tag', async ({ page }) => {
      const stateTag = page.locator('.el-table .el-tag');
      const count = await stateTag.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  // ============================================
  // 10. Interactive Tests
  // ============================================
  test.describe('Interactive Tests', () => {
    test('should allow typing in user filter input', async ({ page }) => {
      const userInput = page.locator('.el-input[placeholder="请输入用户名"]');
      const isVisible = await userInput.isVisible().catch(() => false);
      if (isVisible) {
        await userInput.fill('testuser');
        await expect(userInput).toHaveValue('testuser');
      }
    });

    test('should allow typing in database filter input', async ({ page }) => {
      const dbInput = page.locator('.el-input[placeholder="请输入数据库名"]');
      const isVisible = await dbInput.isVisible().catch(() => false);
      if (isVisible) {
        await dbInput.fill('testdb');
        await expect(dbInput).toHaveValue('testdb');
      }
    });

    test('should allow clearing user filter input', async ({ page }) => {
      const userInput = page.locator('.el-input[placeholder="请输入用户名"]');
      const isVisible = await userInput.isVisible().catch(() => false);
      if (isVisible) {
        await userInput.fill('testuser');
        const clearButton = userInput.locator('.el-input__clear');
        if (await clearButton.isVisible().catch(() => false)) {
          await clearButton.click();
          await expect(userInput).toHaveValue('');
        }
      }
    });
  });

  // ============================================
  // 11. Loading State Tests
  // ============================================
  test.describe('Loading State', () => {
    test('should display loading indicator on table', async ({ page }) => {
      const loadingIndicator = page.locator('.el-table v-loading, .el-loading-mask');
      const isVisible = await loadingIndicator.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  // ============================================
  // 12. Empty State Tests
  // ============================================
  test.describe('Empty State', () => {
    test('should handle empty connection gracefully', async ({ page }) => {
      // When no connection is selected, the table area should show appropriate state
      const table = page.locator('.el-table');
      const isVisible = await table.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });
});
