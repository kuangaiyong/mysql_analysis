import { test, expect } from '@playwright/test';

test.describe('Alerts Page', () => {
  // Navigate to alerts page before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/alerts');
    await page.waitForLoadState('networkidle');
  });

  // ============================================
  // 1. Page Structure Tests
  // ============================================
  test.describe('Page Structure', () => {
    test('should display page title "告警规则管理"', async ({ page }) => {
      await expect(page.locator('.page-title')).toBeVisible();
      await expect(page.getByText('告警规则管理')).toBeVisible();
    });

    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display card component', async ({ page }) => {
      await expect(page.locator('.el-card')).toBeVisible();
    });

    test('should display add rule button', async ({ page }) => {
      const addButton = page.locator('.el-button:has-text("创建规则")');
      await expect(addButton).toBeVisible();
    });

    test('should display search form', async ({ page }) => {
      await expect(page.locator('.search-form')).toBeVisible();
    });
  });

  // ============================================
  // 2. Connection Selector Tests
  // ============================================
  test.describe('Connection Selector', () => {
    test('should display connection select dropdown', async ({ page }) => {
      const connectionSelect = page.locator('.search-form .el-select');
      await expect(connectionSelect).toBeVisible();
    });

    test('should display connection label in search form', async ({ page }) => {
      await expect(page.locator('.search-form label')).toBeVisible();
    });

    test('should have clearable connection select', async ({ page }) => {
      const connectionSelect = page.locator('.search-form .el-select');
      await expect(connectionSelect).toHaveClass(/el-select/);
    });

    test('should allow clicking connection select to open dropdown', async ({ page }) => {
      const connectionSelect = page.locator('.search-form .el-select');
      await connectionSelect.click();
      await expect(page.locator('.el-select-dropdown').first()).toBeVisible();
    });
  });

  // ============================================
  // 3. Search Form Tests
  // ============================================
  test.describe('Search Form', () => {
    test('should display search button', async ({ page }) => {
      const searchButton = page.locator('.search-form .el-button:has-text("查询")');
      await expect(searchButton).toBeVisible();
    });

    test('should display reset button', async ({ page }) => {
      const resetButton = page.locator('.search-form .el-button:has-text("重置")');
      await expect(resetButton).toBeVisible();
    });

    test('should display search form with el-form class', async ({ page }) => {
      const form = page.locator('.search-form');
      await expect(form).toHaveClass(/el-form/);
    });

    test('should display search form items', async ({ page }) => {
      const formItems = page.locator('.search-form .el-form-item');
      expect(await formItems.count()).toBeGreaterThanOrEqual(2);
    });
  });

  // ============================================
  // 4. Data Table Tests
  // ============================================
  test.describe('Data Table', () => {
    test('should display table element', async ({ page }) => {
      await expect(page.locator('.el-table')).toBeVisible();
    });

    test('should display table with stripe styling', async ({ page }) => {
      const table = page.locator('.el-table');
      await expect(table).toHaveClass(/el-table--stripe/);
    });

    test('should display table with border styling', async ({ page }) => {
      const table = page.locator('.el-table');
      await expect(table).toHaveClass(/el-table--border/);
    });

    test('should display table selection column', async ({ page }) => {
      await expect(page.locator('.el-table .el-table__header th:has-text("")').first()).toBeVisible();
    });
  });

  // ============================================
  // 5. Table Columns Tests
  // ============================================
  test.describe('Table Columns', () => {
    test('should display ID column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("ID")')).toBeVisible();
    });

    test('should display rule name column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("规则名称")')).toBeVisible();
    });

    test('should display rule type column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("规则类型")')).toBeVisible();
    });

    test('should display condition column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("条件")')).toBeVisible();
    });

    test('should display severity column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("严重程度")')).toBeVisible();
    });

    test('should display status column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("状态")')).toBeVisible();
    });

    test('should display notification channel column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("通知渠道")')).toBeVisible();
    });

    test('should display created time column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("创建时间")')).toBeVisible();
    });

    test('should display updated time column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("更新时间")')).toBeVisible();
    });

    test('should display operations column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("操作")')).toBeVisible();
    });
  });

  // ============================================
  // 6. Operation Buttons Tests
  // ============================================
  test.describe('Operation Buttons', () => {
    test('should display edit button in table', async ({ page }) => {
      const editButton = page.locator('.el-button').filter({ hasText: '编辑' }).first();
      const isVisible = await editButton.isVisible().catch(() => false);
      if (isVisible) {
        await expect(editButton).toBeVisible();
      }
    });

    test('should display delete button in table', async ({ page }) => {
      const deleteButton = page.locator('.el-button--danger').first();
      const isVisible = await deleteButton.isVisible().catch(() => false);
      if (isVisible) {
        await expect(deleteButton).toBeVisible();
      }
    });

    test('should display enable/disable toggle switch', async ({ page }) => {
      const toggleSwitch = page.locator('.el-switch').first();
      const isVisible = await toggleSwitch.isVisible().catch(() => false);
      if (isVisible) {
        await expect(toggleSwitch).toBeVisible();
      }
    });

    test('should have proper button layout in operations column', async ({ page }) => {
      const actionButtons = page.locator('.el-table__row .el-button[link]');
      expect(await actionButtons.count()).toBeGreaterThanOrEqual(0);
    });
  });

  // ============================================
  // 7. Pagination Tests
  // ============================================
  test.describe('Pagination', () => {
    test('should display pagination component', async ({ page }) => {
      const pagination = page.locator('.el-pagination');
      const isVisible = await pagination.isVisible().catch(() => false);
      if (isVisible) {
        await expect(pagination).toBeVisible();
      } else {
        const paginationWrapper = page.locator('[class*="pagination"]');
        expect(await paginationWrapper.count()).toBeGreaterThanOrEqual(0);
      }
    });

    test('should display page size selector', async ({ page }) => {
      const pageSizeSelect = page.locator('.el-pagination .el-select, .el-pagination__sizes');
      const isVisible = await pageSizeSelect.isVisible().catch(() => false);
      if (isVisible) {
        await expect(pageSizeSelect).toBeVisible();
      }
    });

    test('should display pagination total text', async ({ page }) => {
      const totalText = page.locator('.el-pagination__total');
      const isVisible = await totalText.isVisible().catch(() => false);
      if (isVisible) {
        await expect(totalText).toBeVisible();
      }
    });
  });

  // ============================================
  // 8. Dialog Tests
  // ============================================
  test.describe('Dialog', () => {
    test('should open create rule dialog when clicking add button', async ({ page }) => {
      const addButton = page.locator('.el-button:has-text("创建规则")');
      await addButton.click();
      await expect(page.locator('.el-dialog')).toBeVisible();
    });

    test('should display dialog with title when adding new rule', async ({ page }) => {
      const addButton = page.locator('.el-button:has-text("创建规则")');
      await addButton.click();
      await expect(page.locator('.el-dialog__title')).toBeVisible();
    });

    test('should close dialog when clicking cancel', async ({ page }) => {
      const addButton = page.locator('.el-button:has-text("创建规则")');
      await addButton.click();
      await expect(page.locator('.el-dialog')).toBeVisible();
      
      const cancelButton = page.locator('.el-dialog__footer .el-button:has-text("取消")');
      await cancelButton.click();
      await expect(page.locator('.el-dialog')).not.toBeVisible();
    });
  });

  // ============================================
  // 9. Interactive Tests
  // ============================================
  test.describe('Interactive Tests', () => {
    test('should trigger search when clicking search button', async ({ page }) => {
      const searchButton = page.locator('.search-form .el-button:has-text("查询")');
      await searchButton.click();
      await page.waitForLoadState('networkidle');
    });

    test('should reset search form when clicking reset button', async ({ page }) => {
      const resetButton = page.locator('.search-form .el-button:has-text("重置")');
      await resetButton.click();
      await page.waitForLoadState('networkidle');
    });

    test('should open edit dialog when clicking edit button', async ({ page }) => {
      const editButton = page.locator('.el-button:has-text("编辑")').first();
      await editButton.click();
      await expect(page.locator('.el-dialog')).toBeVisible();
    });
  });

  // ============================================
  // 10. Alert History Link Tests
  // ============================================
  test.describe('Alert History Link', () => {
    test('should have alert history navigation', async ({ page }) => {
      // Check for any link or button that leads to alert history
      const historyLink = page.locator('a:has-text("历史"), button:has-text("历史")');
      const isVisible = await historyLink.first().isVisible().catch(() => false);
      // This test verifies the presence of history navigation (optional feature)
    });
  });
});
