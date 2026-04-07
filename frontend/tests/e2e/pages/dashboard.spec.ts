import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  // Navigate to dashboard before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Structure', () => {
    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display dashboard page title', async ({ page }) => {
      // Verify dashboard title/header exists
      await expect(page.locator('text=仪表盘').first()).toBeVisible();
    });

    test('should display connection selector card', async ({ page }) => {
      // Verify connection selector card exists
      await expect(page.locator('.connection-selector-card')).toBeVisible();
      await expect(page.locator('text=当前连接：')).toBeVisible();
    });

    test('should have proper layout structure', async ({ page }) => {
      // Verify el-row and el-col layout elements exist
      await expect(page.locator('.el-row').first()).toBeVisible();
      await expect(page.locator('.el-col').first()).toBeVisible();
    });
  });

  test.describe('Connection Selector', () => {
    test('should display connection selector', async ({ page }) => {
      await expect(page.locator('.el-select')).toBeVisible();
    });

    test('should show connection status', async ({ page }) => {
      // Check if connection status tag exists
      const connectedTag = page.locator('.el-tag:has-text("已连接")');
      const notSelectedTag = page.locator('.el-tag:has-text("未选择连接")');
      
      // Either "已连接" or "未选择连接" should be visible
      const hasConnectedStatus = await connectedTag.isVisible().catch(() => false);
      const hasNotSelectedStatus = await notSelectedTag.isVisible().catch(() => false);
      
      expect(hasConnectedStatus || hasNotSelectedStatus).toBeTruthy();
    });

    test('should open connection dropdown', async ({ page }) => {
      const select = page.locator('.el-select');
      await expect(select).toBeVisible();
      
      // Click to open dropdown
      await select.click();
      
      // Dropdown should appear
      await expect(page.locator('.el-select-dropdown')).toBeVisible();
    });
  });

  test.describe('Quick Actions', () => {
    test('should display quick actions section', async ({ page }) => {
      await expect(page.locator('text=快速操作')).toBeVisible();
    });

    test('should display view details button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("查看详细报告")')).toBeVisible();
    });

    test('should display export button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("导出报告")')).toBeVisible();
    });
  });

  test.describe('Charts Containers', () => {
    test('should display QPS chart container', async ({ page }) => {
      // Verify QPS chart container exists (even if empty)
      await expect(page.locator('.chart-card:has-text("QPS监控")')).toBeVisible();
    });

    test('should display TPS chart container', async ({ page }) => {
      // Verify TPS chart container exists (even if empty)
      await expect(page.locator('.chart-card:has-text("TPS监控")')).toBeVisible();
    });

    test('should handle window resize', async ({ page }) => {
      // Resize viewport
      await page.setViewportSize({ width: 1200, height: 800 });
      await page.waitForTimeout(300);
      
      // Verify chart containers remain visible after resize
      await expect(page.locator('.chart-card:has-text("QPS监控")')).toBeVisible();
      await expect(page.locator('.chart-card:has-text("TPS监控")')).toBeVisible();
      
      // Resize to smaller viewport
      await page.setViewportSize({ width: 768, height: 600 });
      await page.waitForTimeout(300);
      
      // Verify chart containers still visible
      await expect(page.locator('.chart-card:has-text("QPS监控")')).toBeVisible();
      await expect(page.locator('.chart-card:has-text("TPS监控")')).toBeVisible();
    });
  });

  test.describe('Config Health Section', () => {
    test('should display config health card', async ({ page }) => {
      await expect(page.locator('.config-health-card')).toBeVisible();
    });

    test('should display config health header', async ({ page }) => {
      await expect(page.locator('text=配置健康')).toBeVisible();
    });

    test('should display start analysis button', async ({ page }) => {
      await expect(page.locator('.el-button:has-text("开始分析")')).toBeVisible();
    });
  });
});
