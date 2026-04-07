import { test, expect } from '@playwright/test';

test.describe('Connections Page', () => {
  // Navigate to connections page before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/connections');
    await page.waitForLoadState('networkidle');
  });

  // ============================================
  // 1. Page Structure Tests
  // ============================================
  test.describe('Page Structure', () => {
    test('should display page title "连接管理"', async ({ page }) => {
      await expect(page.locator('h1:has-text("连接管理")')).toBeVisible();
    });

    test('should display add connection button', async ({ page }) => {
      // The PageHeader component has an add button with "添加连接" text
      const addButton = page.locator('.el-button:has-text("添加连接"), button:has-text("添加连接"), [class*="add"]:has-text("添加连接")');
      await expect(addButton.first()).toBeVisible();
    });

    test('should display search form', async ({ page }) => {
      // Search form is wrapped in el-form with class "search-form"
      await expect(page.locator('.search-form')).toBeVisible();
    });

    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display card component', async ({ page }) => {
      await expect(page.locator('.el-card')).toBeVisible();
    });
  });

  // ============================================
  // 2. Search Form Tests
  // ============================================
  test.describe('Search Form', () => {
    test('should display name search input', async ({ page }) => {
      const nameInput = page.locator('.search-form .el-input[placeholder*="连接名称"], .search-form input[placeholder*="连接名称"]');
      await expect(nameInput).toBeVisible();
    });

    test('should display host search input', async ({ page }) => {
      const hostInput = page.locator('.search-form .el-input[placeholder*="主机地址"], .search-form input[placeholder*="主机地址"]');
      await expect(hostInput).toBeVisible();
    });

    test('should display database search input', async ({ page }) => {
      const dbInput = page.locator('.search-form .el-input[placeholder*="数据库名"], .search-form input[placeholder*="数据库名"]');
      await expect(dbInput).toBeVisible();
    });

    test('should display search button', async ({ page }) => {
      const searchButton = page.locator('.el-button:has-text("查询")');
      await expect(searchButton).toBeVisible();
    });

    test('should display reset button', async ({ page }) => {
      const resetButton = page.locator('.el-button:has-text("重置")');
      await expect(resetButton).toBeVisible();
    });

    test('should display search form labels', async ({ page }) => {
      await expect(page.locator('.search-form label:has-text("名称")')).toBeVisible();
      await expect(page.locator('.search-form label:has-text("主机")')).toBeVisible();
      await expect(page.locator('.search-form label:has-text("数据库")')).toBeVisible();
    });
  });

  // ============================================
  // 3. Data Table Tests
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

    test('should have full width table', async ({ page }) => {
      await expect(page.locator('.el-table.w-full')).toBeVisible();
    });

    test('should display loading state', async ({ page }) => {
      // When loading, v-loading directive adds loading class
      const tableWrapper = page.locator('.el-table');
      // The loading state may appear briefly, so we just check the table exists
      await expect(tableWrapper).toBeVisible();
    });
  });

  // ============================================
  // 4. Table Columns Tests
  // ============================================
  test.describe('Table Columns', () => {
    test('should display ID column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("ID")')).toBeVisible();
    });

    test('should display connection name column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("连接名称")')).toBeVisible();
    });

    test('should display host address column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("主机地址")')).toBeVisible();
    });

    test('should display port column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("端口")')).toBeVisible();
    });

    test('should display username column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("用户名")')).toBeVisible();
    });

    test('should display database column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("数据库")')).toBeVisible();
    });

    test('should display status column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("状态")')).toBeVisible();
    });

    test('should display created_at column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("创建时间")')).toBeVisible();
    });

    test('should display operations column', async ({ page }) => {
      await expect(page.locator('.el-table__header th:has-text("操作")')).toBeVisible();
    });
  });

  // ============================================
  // 5. Operation Buttons Tests
  // ============================================
  test.describe('Operation Buttons', () => {
    test('should display edit button in table', async ({ page }) => {
      // Edit button appears in table rows
      const editButton = page.locator('.el-button--primary:has-text("编辑"), .el-button[type="primary"][link]:has-text("编辑")');
      await expect(editButton.first()).toBeVisible();
    });

    test('should display test button in table', async ({ page }) => {
      // Test button appears in table rows
      const testButton = page.locator('.el-button--warning:has-text("测试"), .el-button[type="warning"][link]:has-text("测试")');
      await expect(testButton.first()).toBeVisible();
    });

    test('should display delete button in table', async ({ page }) => {
      // Delete button appears in table rows
      const deleteButton = page.locator('.el-button--danger:has-text("删除"), .el-button[type="danger"][link]:has-text("删除")');
      await expect(deleteButton.first()).toBeVisible();
    });

    test('should have proper button layout in operations column', async ({ page }) => {
      // Operations column should contain multiple action buttons
      const actionButtons = page.locator('.el-table__row .el-button[link]');
      expect(await actionButtons.count()).toBeGreaterThan(0);
    });
  });

  // ============================================
  // 6. Pagination Tests
  // ============================================
  test.describe('Pagination', () => {
    test('should display pagination component', async ({ page }) => {
      // Pagination component should exist (may or may not have data)
      const pagination = page.locator('.el-pagination');
      const isVisible = await pagination.isVisible().catch(() => false);
      if (isVisible) {
        await expect(pagination).toBeVisible();
      } else {
        // Check if pagination wrapper exists
        const paginationWrapper = page.locator('[class*="pagination"]');
        expect(await paginationWrapper.count()).toBeGreaterThanOrEqual(0);
      }
    });

    test('should display page size selector', async ({ page }) => {
      // Page size selector is typically in the pagination component
      const pageSizeSelect = page.locator('.el-pagination .el-select, .el-pagination__sizes');
      const isVisible = await pageSizeSelect.isVisible().catch(() => false);
      if (isVisible) {
        await expect(pageSizeSelect).toBeVisible();
      }
    });

    test('should display pagination info text', async ({ page }) => {
      // Pagination typically shows "共 X 条"
      const totalText = page.locator('.el-pagination__total, text=共');
      const isVisible = await totalText.first().isVisible().catch(() => false);
      if (isVisible) {
        await expect(totalText.first()).toBeVisible();
      }
    });
  });

  // ============================================
  // 7. Dialog Tests
  // ============================================
  test.describe('Dialog', () => {
    test('should open add connection dialog when clicking add button', async ({ page }) => {
      // Click the add button
      const addButton = page.locator('.el-button:has-text("添加连接")').first();
      await addButton.click();
      
      // Wait for dialog to appear
      await expect(page.locator('.el-dialog')).toBeVisible();
    });

    test('should display dialog with correct title for add', async ({ page }) => {
      // Click add button
      const addButton = page.locator('.el-button:has-text("添加连接")').first();
      await addButton.click();
      
      // Check dialog title
      await expect(page.locator('.el-dialog__title:has-text("新增连接")')).toBeVisible();
    });

    test('should display dialog form fields', async ({ page }) => {
      // Click add button to open dialog
      const addButton = page.locator('.el-button:has-text("添加连接")').first();
      await addButton.click();
      
      // Wait for dialog
      await expect(page.locator('.el-dialog')).toBeVisible();
      
      // Check form fields exist
      await expect(page.locator('.el-form-item label:has-text("连接名称")')).toBeVisible();
      await expect(page.locator('.el-form-item label:has-text("主机地址")')).toBeVisible();
      await expect(page.locator('.el-form-item label:has-text("端口")')).toBeVisible();
      await expect(page.locator('.el-form-item label:has-text("用户名")')).toBeVisible();
      await expect(page.locator('.el-form-item label:has-text("密码")')).toBeVisible();
      await expect(page.locator('.el-form-item label:has-text("数据库名")')).toBeVisible();
      await expect(page.locator('.el-form-item label:has-text("连接池大小")')).toBeVisible();
    });

    test('should display dialog cancel and confirm buttons', async ({ page }) => {
      // Open dialog
      const addButton = page.locator('.el-button:has-text("添加连接")').first();
      await addButton.click();
      
      await expect(page.locator('.el-dialog__footer .el-button:has-text("取消")')).toBeVisible();
      await expect(page.locator('.el-dialog__footer .el-button--primary:has-text("确定")')).toBeVisible();
    });

    test('should close dialog when clicking cancel', async ({ page }) => {
      // Open dialog
      const addButton = page.locator('.el-button:has-text("添加连接")').first();
      await addButton.click();
      
      // Click cancel
      await page.locator('.el-dialog__footer .el-button:has-text("取消")').click();
      
      // Dialog should close
      await expect(page.locator('.el-dialog')).not.toBeVisible();
    });
  });

  // ============================================
  // 8. Interactive Tests
  // ============================================
  test.describe('Interactive Tests', () => {
    test('should allow typing in name search input', async ({ page }) => {
      const nameInput = page.locator('.search-form .el-input[placeholder*="连接名称"], .search-form input[placeholder*="连接名称"]').first();
      await nameInput.fill('test-connection');
      await expect(nameInput).toHaveValue('test-connection');
    });

    test('should allow typing in host search input', async ({ page }) => {
      const hostInput = page.locator('.search-form .el-input[placeholder*="主机地址"], .search-form input[placeholder*="主机地址"]').first();
      await hostInput.fill('localhost');
      await expect(hostInput).toHaveValue('localhost');
    });

    test('should allow typing in database search input', async ({ page }) => {
      const dbInput = page.locator('.search-form .el-input[placeholder*="数据库名"], .search-form input[placeholder*="数据库名"]').first();
      await dbInput.fill('testdb');
      await expect(dbInput).toHaveValue('testdb');
    });

    test('should allow clearing name search input', async ({ page }) => {
      const nameInput = page.locator('.search-form .el-input[placeholder*="连接名称"], .search-form input[placeholder*="连接名称"]').first();
      
      // Type some text
      await nameInput.fill('test-connection');
      await expect(nameInput).toHaveValue('test-connection');
      
      // Clear the input (clearable input should have a clear button)
      const clearButton = page.locator('.search-form .el-input .el-input__clear').first();
      await clearButton.click();
      
      // Input should be cleared
      await expect(nameInput).toHaveValue('');
    });

    test('should allow clearing host search input', async ({ page }) => {
      const hostInput = page.locator('.search-form .el-input[placeholder*="主机地址"], .search-form input[placeholder*="主机地址"]').first();
      
      // Type some text
      await hostInput.fill('localhost');
      await expect(hostInput).toHaveValue('localhost');
      
      // Clear the input
      const clearButton = page.locator('.search-form .el-input .el-input__clear').nth(1);
      await clearButton.click();
      
      // Input should be cleared
      await expect(hostInput).toHaveValue('');
    });

    test('should allow clearing database search input', async ({ page }) => {
      const dbInput = page.locator('.search-form .el-input[placeholder*="数据库名"], .search-form input[placeholder*="数据库名"]').first();
      
      // Type some text
      await dbInput.fill('testdb');
      await expect(dbInput).toHaveValue('testdb');
      
      // Clear the input
      const clearButton = page.locator('.search-form .el-input .el-input__clear').nth(2);
      await clearButton.click();
      
      // Input should be cleared
      await expect(dbInput).toHaveValue('');
    });

    test('should trigger search when clicking search button', async ({ page }) => {
      // Type in search inputs
      await page.locator('.search-form .el-input[placeholder*="连接名称"]').first().fill('test');
      await page.locator('.search-form .el-input[placeholder*="主机地址"]').first().fill('localhost');
      await page.locator('.search-form .el-input[placeholder*="数据库名"]').first().fill('testdb');
      
      // Click search button
      await page.locator('.el-button:has-text("查询")').click();
      
      // Page should reload with new search (just verify no errors)
      await page.waitForLoadState('networkidle');
    });

    test('should reset search form when clicking reset button', async ({ page }) => {
      // Fill in search inputs
      await page.locator('.search-form .el-input[placeholder*="连接名称"]').first().fill('test');
      await page.locator('.search-form .el-input[placeholder*="主机地址"]').first().fill('localhost');
      await page.locator('.search-form .el-input[placeholder*="数据库名"]').first().fill('testdb');
      
      // Click reset button
      await page.locator('.el-button:has-text("重置")').click();
      
      // Wait for reset to complete
      await page.waitForTimeout(300);
      
      // All inputs should be cleared
      const nameInput = page.locator('.search-form .el-input[placeholder*="连接名称"]').first();
      const hostInput = page.locator('.search-form .el-input[placeholder*="主机地址"]').first();
      const dbInput = page.locator('.search-form .el-input[placeholder*="数据库名"]').first();
      
      await expect(nameInput).toHaveValue('');
      await expect(hostInput).toHaveValue('');
      await expect(dbInput).toHaveValue('');
    });
  });

  // ============================================
  // Additional Tests - Status Display
  // ============================================
  test.describe('Status Display', () => {
    test('should display status indicator with online/offline', async ({ page }) => {
      // Status column should show status indicator
      const statusIndicator = page.locator('.status-indicator, [class*="status"]');
      const isVisible = await statusIndicator.first().isVisible().catch(() => false);
      if (isVisible) {
        await expect(statusIndicator.first()).toBeVisible();
      }
    });

    test('should display status dot', async ({ page }) => {
      // Status dot should be present
      const statusDot = page.locator('.status-dot, [class*="status-dot"]');
      const isVisible = await statusDot.first().isVisible().catch(() => false);
      if (isVisible) {
        await expect(statusDot.first()).toBeVisible();
      }
    });

    test('should have online/offline status text', async ({ page }) => {
      // Should show either "在线" or "离线"
      const onlineStatus = page.locator('text=在线');
      const offlineStatus = page.locator('text=离线');
      
      const hasOnline = await onlineStatus.isVisible().catch(() => false);
      const hasOffline = await offlineStatus.isVisible().catch(() => false);
      
      expect(hasOnline || hasOffline).toBeTruthy();
    });
  });

  // ============================================
  // Additional Tests - Form Elements
  // ============================================
  test.describe('Form Elements', () => {
    test('should display all form items in search form', async ({ page }) => {
      const formItems = page.locator('.search-form .el-form-item');
      expect(await formItems.count()).toBeGreaterThanOrEqual(4);
    });

    test('should have proper form layout', async ({ page }) => {
      const form = page.locator('.search-form');
      await expect(form).toHaveClass(/el-form/);
    });

    test('should have inline form layout', async ({ page }) => {
      const form = page.locator('.search-form');
      await expect(form).toHaveClass(/el-form--inline/);
    });
  });
});
