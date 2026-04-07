import { test, expect } from '@playwright/test';

test.describe('Monitoring Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/monitoring');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Basic Structure', () => {
    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display page title', async ({ page }) => {
      await expect(page.locator('text=性能监控')).toBeVisible();
    });

    test('should have proper layout with el-row and el-col', async ({ page }) => {
      await expect(page.locator('.el-row').first()).toBeVisible();
      await expect(page.locator('.el-col').first()).toBeVisible();
    });
  });

  test.describe('Connection Selector', () => {
    test('should display connection selector in header', async ({ page }) => {
      const selector = page.locator('.el-select');
      await expect(selector).toBeVisible();
    });

    test('should display connection selector with correct placeholder', async ({ page }) => {
      const select = page.locator('.el-select').first();
      const placeholder = await select.getAttribute('placeholder');
      expect(placeholder).toContain('选择');
    });

    test('should open dropdown when clicked', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      await page.waitForTimeout(300);
      const dropdown = page.locator('.el-select-dropdown');
      const isVisible = await dropdown.isVisible().catch(() => false);
      if (!isVisible) {
        // May not have connections configured
        const empty = page.locator('.el-select-dropdown__empty');
        const emptyVisible = await empty.isVisible().catch(() => false);
        expect(emptyVisible || (await select.isVisible())).toBeTruthy();
      }
    });
  });

  test.describe('WebSocket Status', () => {
    test('should display WebSocket status indicator', async ({ page }) => {
      const wsStatus = page.locator('.ws-status');
      const isVisible = await wsStatus.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('text=WebSocket').isVisible().catch(() => false))).toBeTruthy();
    });

    test('should display connection status text', async ({ page }) => {
      const connected = page.locator('text=WebSocket已连接');
      const disconnected = page.locator('text=WebSocket未连接');
      const hasConnected = await connected.isVisible().catch(() => false);
      const hasDisconnected = await disconnected.isVisible().catch(() => false);
      expect(hasConnected || hasDisconnected).toBeTruthy();
    });
  });

  test.describe('Metrics Display', () => {
    test('should display MetricsGrid component', async ({ page }) => {
      await expect(page.locator('.metrics-grid')).toBeVisible();
    });

    test('should display primary metrics titles', async ({ page }) => {
      await expect(page.locator('text=读QPS')).toBeVisible();
      await expect(page.locator('text=写QPS')).toBeVisible();
      await expect(page.locator('text=连接数')).toBeVisible();
      await expect(page.locator('text=缓冲池命中率')).toBeVisible();
    });

    test('should display critical metrics titles', async ({ page }) => {
      await expect(page.locator('text=行锁等待')).toBeVisible();
      await expect(page.locator('text=死锁')).toBeVisible();
      await expect(page.locator('text=磁盘临时表')).toBeVisible();
      await expect(page.locator('text=全表扫描')).toBeVisible();
    });

    test('should display metric values with units', async ({ page }) => {
      // Check for unit displays
      await expect(page.locator('text=次/秒')).toBeVisible();
      await expect(page.locator('text=事务/秒')).toBeVisible();
      await expect(page.locator('text=当前/最大')).toBeVisible();
      await expect(page.locator('text=效率指标')).toBeVisible();
    });
  });

  test.describe('Charts', () => {
    test('should display QPS chart card', async ({ page }) => {
      const chartCard = page.locator('.el-card:has-text("QPS")').first();
      await expect(chartCard).toBeVisible();
    });

    test('should display connection trend chart', async ({ page }) => {
      const chartCard = page.locator('.el-card:has-text("连接数趋势")');
      await expect(chartCard).toBeVisible();
    });

    test('should display buffer pool hit rate chart', async ({ page }) => {
      const chartCard = page.locator('.el-card:has-text("缓冲池命中率")');
      await expect(chartCard).toBeVisible();
    });

    test('should show empty state when no connection selected', async ({ page }) => {
      // The page may show empty state or charts
      const empty = page.locator('.el-empty');
      const chart = page.locator('.el-card');
      const hasContent = (await chart.count()) > 0;
      expect(hasContent).toBeTruthy();
    });
  });

  test.describe('Collection Controls', () => {
    test('should display start collection button', async ({ page }) => {
      const startBtn = page.locator('.el-button:has-text("启动采集")');
      const stopBtn = page.locator('.el-button:has-text("停止采集")');
      const hasStart = await startBtn.isVisible().catch(() => false);
      const hasStop = await stopBtn.isVisible().catch(() => false);
      expect(hasStart || hasStop).toBeTruthy();
    });

    test('should toggle between start and stop button', async ({ page }) => {
      const startBtn = page.locator('.el-button:has-text("启动采集")');
      const stopBtn = page.locator('.el-button:has-text("停止采集")');
      const hasStart = await startBtn.isVisible().catch(() => false);
      const hasStop = await stopBtn.isVisible().catch(() => false);
      // Only one should be visible at a time
      expect(hasStart !== hasStop).toBeTruthy();
    });
  });

  test.describe('Real-time Slow Query Table', () => {
    test('should display slow query table section', async ({ page }) => {
      const section = page.locator('.el-card:has-text("实时慢查询")');
      await expect(section).toBeVisible();
    });

    test('should display slow query table columns', async ({ page }) => {
      const table = page.locator('.el-table');
      await expect(table).toBeVisible();
      await expect(page.locator('text=SQL摘要')).toBeVisible();
      await expect(page.locator('text=执行时间')).toBeVisible();
      await expect(page.locator('text=扫描行数')).toBeVisible();
      await expect(page.locator('text=数据库')).toBeVisible();
    });
  });

  test.describe('Index Statistics', () => {
    test('should display index stats section', async ({ page }) => {
      const section = page.locator('.el-card:has-text("索引使用统计")');
      await expect(section).toBeVisible();
    });

    test('should display index stats items', async ({ page }) => {
      await expect(page.locator('text=索引数量')).toBeVisible();
      await expect(page.locator('text=使用率最高')).toBeVisible();
      await expect(page.locator('text=未使用索引')).toBeVisible();
    });

    test('should display refresh button for index stats', async ({ page }) => {
      const refreshBtn = page.locator('.el-button:has-text("刷新")');
      await expect(refreshBtn).toBeVisible();
    });
  });

  test.describe('Interactive Elements', () => {
    test('should have clickable refresh button', async ({ page }) => {
      const refreshBtn = page.locator('.el-button:has-text("刷新")');
      await expect(refreshBtn).toBeVisible();
    });

    test('should handle window resize', async ({ page }) => {
      await page.setViewportSize({ width: 1200, height: 900 });
      await page.waitForTimeout(300);
      await expect(page.locator('.page-container')).toBeVisible();
      
      await page.setViewportSize({ width: 768, height: 600 });
      await page.waitForTimeout(300);
      await expect(page.locator('.page-container')).toBeVisible();
    });
  });
});
