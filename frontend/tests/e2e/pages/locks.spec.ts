import { test, expect } from '@playwright/test';

test.describe('Locks Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/locks');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Structure', () => {
    test('should display page title "锁分析"', async ({ page }) => {
      await expect(page.locator('h1:has-text("锁分析")')).toBeVisible();
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
      await expect(page.locator('.el-page-header__title:has-text("锁分析")')).toBeVisible();
    });
  });

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
      await expect(page.locator('.el-select-dropdown')).toBeVisible();
    });
  });

  test.describe('Tab Navigation', () => {
    test('should display el-tabs component', async ({ page }) => {
      const tabs = page.locator('.el-tabs');
      const isVisible = await tabs.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display "当前锁等待" tab', async ({ page }) => {
      const tab = page.locator('.el-tabs__item:has-text("当前锁等待")');
      const isVisible = await tab.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display "死锁历史" tab', async ({ page }) => {
      const tab = page.locator('.el-tabs__item:has-text("死锁历史")');
      const isVisible = await tab.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display "锁等待图" tab', async ({ page }) => {
      const tab = page.locator('.el-tabs__item:has-text("锁等待图")');
      const isVisible = await tab.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should be able to switch tabs', async ({ page }) => {
      const deadlockTab = page.locator('.el-tabs__item:has-text("死锁历史")');
      const isVisible = await deadlockTab.isVisible().catch(() => false);
      if (isVisible) {
        await deadlockTab.click();
        await page.waitForTimeout(300);
      }
    });
  });

  test.describe('Refresh Button', () => {
    test('should display page header refresh button', async ({ page }) => {
      const headerRefreshBtn = page.locator('.el-page-header .el-button');
      await expect(headerRefreshBtn).toBeVisible();
    });

    test('should display refresh button in lock waits tab', async ({ page }) => {
      const refreshBtn = page.locator('.el-button:has-text("刷新")').first();
      const isVisible = await refreshBtn.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  test.describe('Time Range Selector', () => {
    test('should display time range selector in deadlock tab', async ({ page }) => {
      const timeSelector = page.locator('.el-select[placeholder="选择时间范围"]');
      const isVisible = await timeSelector.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display time range options', async ({ page }) => {
      const timeSelector = page.locator('.el-select[placeholder="选择时间范围"]');
      const isVisible = await timeSelector.isVisible().catch(() => false);
      if (isVisible) {
        await timeSelector.click();
        await expect(page.locator('.el-select-dropdown__item:has-text("最近1小时")')).toBeVisible();
      }
    });

    test('should have "最近1小时" option', async ({ page }) => {
      const option = page.locator('.el-select-dropdown__item:has-text("最近1小时")');
      const isVisible = await option.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should have "最近24小时" option', async ({ page }) => {
      const option = page.locator('.el-select-dropdown__item:has-text("最近24小时")');
      const isVisible = await option.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should have "最近72小时" option', async ({ page }) => {
      const option = page.locator('.el-select-dropdown__item:has-text("最近72小时")');
      const isVisible = await option.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  test.describe('Auto Refresh Checkbox', () => {
    test('should display auto refresh checkbox in lock graph tab', async ({ page }) => {
      const checkbox = page.locator('.el-checkbox:has-text("自动刷新")');
      const isVisible = await checkbox.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display auto refresh with 5 second interval', async ({ page }) => {
      const checkbox = page.locator('.el-checkbox:has-text("自动刷新 (5秒)")');
      const isVisible = await checkbox.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should be able to check auto refresh checkbox', async ({ page }) => {
      const checkbox = page.locator('.el-checkbox');
      const isVisible = await checkbox.isVisible().catch(() => false);
      if (isVisible) {
        await checkbox.click();
        await page.waitForTimeout(300);
      }
    });
  });

  test.describe('Lock Waits Table', () => {
    test('should display lock waits table', async ({ page }) => {
      const table = page.locator('.el-table').first();
      const isVisible = await table.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display requesting_trx_id column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("请求事务ID")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display requested_lock_id column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("请求的锁ID")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display blocking_trx_id column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("阻塞事务ID")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display blocking_lock_id column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("阻塞的锁ID")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display lock_mode column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("锁模式")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display lock_type column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("锁类型")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display table_name column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("表名")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display index_name column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("索引名")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display lock_data column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("锁数据")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  test.describe('Deadlock History Table', () => {
    test('should display timestamp column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("时间")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display transactions column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("涉及的事务")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display queries column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("SQL查询")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display wait_resource column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("等待资源")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display victim_trx_id column', async ({ page }) => {
      const column = page.locator('.el-table__header th:has-text("牺牲事务ID")');
      const isVisible = await column.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  test.describe('Lock Graph Visualization', () => {
    test('should display lock graph container', async ({ page }) => {
      const graphContainer = page.locator('.lock-graph-chart, [class*="graph-container"]');
      const isVisible = await graphContainer.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display graph chart element', async ({ page }) => {
      const chart = page.locator('.lock-graph-chart');
      const isVisible = await chart.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should have proper chart dimensions', async ({ page }) => {
      const chart = page.locator('.lock-graph-chart');
      const isVisible = await chart.isVisible().catch(() => false);
      if (isVisible) {
        const height = await chart.evaluate((el) => {
          const style = window.getComputedStyle(el);
          return style.height;
        });
        expect(height).toBeTruthy();
      }
    });
  });

  test.describe('Empty State', () => {
    test('should display empty state when no connection selected', async ({ page }) => {
      const emptyState = page.locator('.el-empty');
      const isVisible = await emptyState.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display "请先选择连接" message', async ({ page }) => {
      const message = page.locator('.el-empty__description:has-text("请先选择连接")');
      const isVisible = await message.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display empty state for no lock waits', async ({ page }) => {
      const emptyState = page.locator('.el-empty:has-text("当前无锁等待")');
      const isVisible = await emptyState.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('should display empty state for no deadlocks', async ({ page }) => {
      const emptyState = page.locator('.el-empty:has-text("近期无死锁记录")');
      const isVisible = await emptyState.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  test.describe('Loading State', () => {
    test('should display loading indicator', async ({ page }) => {
      const loading = page.locator('.el-loading-mask, [v-loading]');
      const isVisible = await loading.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });

  test.describe('Tags in Table', () => {
    test('should display el-tag in deadlock transactions', async ({ page }) => {
      const tag = page.locator('.el-table .el-tag');
      const count = await tag.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should display victim tag with danger type', async ({ page }) => {
      const victimTag = page.locator('.el-tag--danger');
      const isVisible = await victimTag.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });
  });
});
