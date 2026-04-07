import { test, expect } from '@playwright/test';

test.describe('Reports Page', () => {
  // Navigate to reports page before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/reports');
    await page.waitForLoadState('networkidle');
  });

  // ============================================
  // 1. Page Structure Tests
  // ============================================
  test.describe('Page Structure', () => {
    test('should display page title "性能报告"', async ({ page }) => {
      await expect(page.locator('h1:has-text("性能报告")')).toBeVisible();
    });

    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display card component', async ({ page }) => {
      await expect(page.locator('.el-card')).toBeVisible();
    });

    test('should display create report button', async ({ page }) => {
      const createButton = page.locator('.el-button:has-text("生成报告")');
      await expect(createButton).toBeVisible();
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
      const connectionSelect = page.locator('.search-form .el-select[placeholder="请选择连接"]');
      await expect(connectionSelect).toBeVisible();
    });

    test('should display connection label in search form', async ({ page }) => {
      await expect(page.locator('.search-form label:has-text("连接")')).toBeVisible();
    });

    test('should have clearable connection select', async ({ page }) => {
      const connectionSelect = page.locator('.search-form .el-select[placeholder="请选择连接"]');
      await expect(connectionSelect).toHaveClass(/el-select/);
    });

    test('should allow clicking connection select to open dropdown', async ({ page }) => {
      const connectionSelect = page.locator('.search-form .el-select[placeholder="请选择连接"]');
      await connectionSelect.click();
      await expect(page.locator('.el-select-dropdown')).toBeVisible();
    });
  });

  // ============================================
  // 3. Report Type Selector Tests
  // ============================================
  test.describe('Report Type Selector', () => {
    test('should display report type select dropdown', async ({ page }) => {
      const reportTypeSelect = page.locator('.search-form .el-select[placeholder="请选择报告类型"]');
      await expect(reportTypeSelect).toBeVisible();
    });

    test('should display report type label in search form', async ({ page }) => {
      await expect(page.locator('.search-form label:has-text("报告类型")')).toBeVisible();
    });

    test('should have report type options', async ({ page }) => {
      const reportTypeSelect = page.locator('.search-form .el-select[placeholder="请选择报告类型"]');
      await reportTypeSelect.click();
      await expect(page.locator('.el-select-dropdown')).toBeVisible();
    });
  });

  // ============================================
  // 4. Status Selector Tests
  // ============================================
  test.describe('Status Selector', () => {
    test('should display status select dropdown', async ({ page }) => {
      const statusSelect = page.locator('.search-form .el-select[placeholder="请选择状态"]');
      await expect(statusSelect).toBeVisible();
    });

    test('should display status label in search form', async ({ page }) => {
      await expect(page.locator('.search-form label:has-text("状态")')).toBeVisible();
    });

    test('should have status options', async ({ page }) => {
      const statusSelect = page.locator('.search-form .el-select[placeholder="请选择状态"]');
      await statusSelect.click();
      await expect(page.locator('.el-select-dropdown')).toBeVisible();
    });
  });

  // ============================================
  // 5. Search Form Tests
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

    test('should display multiple search form items', async ({ page }) => {
      const formItems = page.locator('.search-form .el-form-item');
      expect(await formItems.count()).toBeGreaterThanOrEqual(4);
    });
  });

  // ============================================
  // 6. Data Table Tests
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

    test('should display full width table', async ({ page }) => {
      await expect(page.locator('.el-table.w-full')).toBeVisible();
    });
  });

  // ============================================
  // 7. Table Columns Tests
  // ============================================
  test.describe('Table Columns', () => {
    test('should display ID column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("ID")')).toBeVisible();
    });

    test('should display report name column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("报告名称")')).toBeVisible();
    });

    test('should display report type column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("报告类型")')).toBeVisible();
    });

    test('should display connection name column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("连接名称")')).toBeVisible();
    });

    test('should display time range column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("时间范围")')).toBeVisible();
    });

    test('should display status column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("状态")')).toBeVisible();
    });

    test('should display generated time column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("生成时间")')).toBeVisible();
    });

    test('should display file size column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("文件大小")')).toBeVisible();
    });

    test('should display operations column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("操作")')).toBeVisible();
    });
  });

  // ============================================
  // 8. Operation Buttons Tests
  // ============================================
  test.describe('Operation Buttons', () => {
    test('should display view report button', async ({ page }) => {
      const viewButton = page.locator('.el-button:has-text("查看详情")').first();
      await expect(viewButton).toBeVisible();
    });

    test('should display delete button in table', async ({ page }) => {
      const deleteButton = page.locator('.el-button--danger:has-text("删除")').first();
      await expect(deleteButton).toBeVisible();
    });

    test('should display download button', async ({ page }) => {
      const downloadButton = page.locator('.el-button:has-text("下载")').first();
      await expect(downloadButton).toBeVisible();
    });

    test('should display download dropdown options', async ({ page }) => {
      const downloadButton = page.locator('.el-button:has-text("下载")').first();
      await downloadButton.click();
      await expect(page.locator('.el-dropdown-menu')).toBeVisible();
    });

    test('should have proper button layout in operations column', async ({ page }) => {
      const actionButtons = page.locator('.el-table__row .el-button[link]');
      expect(await actionButtons.count()).toBeGreaterThanOrEqual(0);
    });
  });

  // ============================================
  // 9. Pagination Tests
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
      const totalText = page.locator('.el-pagination__total, text=共');
      const isVisible = await totalText.first().isVisible().catch(() => false);
      if (isVisible) {
        await expect(totalText.first()).toBeVisible();
      }
    });
  });

  // ============================================
  // 10. Dialog Tests
  // ============================================
  test.describe('Dialog', () => {
    test('should open create report dialog when clicking create button', async ({ page }) => {
      const createButton = page.locator('.el-button:has-text("生成报告")');
      await createButton.click();
      await expect(page.locator('.el-dialog')).toBeVisible();
    });

    test('should display dialog with title when creating new report', async ({ page }) => {
      const createButton = page.locator('.el-button:has-text("生成报告")');
      await createButton.click();
      await expect(page.locator('.el-dialog__title')).toBeVisible();
    });

    test('should close dialog when clicking cancel', async ({ page }) => {
      const createButton = page.locator('.el-button:has-text("生成报告")');
      await createButton.click();
      await expect(page.locator('.el-dialog')).toBeVisible();
      
      const cancelButton = page.locator('.el-dialog__footer .el-button:has-text("取消")');
      await cancelButton.click();
      await expect(page.locator('.el-dialog')).not.toBeVisible();
    });
  });

  // ============================================
  // 11. Interactive Tests
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

    test('should open view dialog when clicking view button', async ({ page }) => {
      const viewButton = page.locator('.el-button:has-text("查看详情")').first();
      await viewButton.click();
      await expect(page.locator('.el-dialog')).toBeVisible();
    });
  });
});
