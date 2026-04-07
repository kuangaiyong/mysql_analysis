import { test, expect } from '../../fixtures/base.fixture';
import { LocksPage } from '../../pages/LocksPage';

test.describe('Locks Page', () => {
  let locksPage: LocksPage;

  test.beforeEach(async ({ page }) => {
    locksPage = new LocksPage(page);
    await locksPage.goto();
  });

  test.describe('Page Load', () => {
    test('should display page title "锁分析"', async () => {
      const title = await locksPage.getTitle();
      expect(title).toBe('锁分析');
    });

    test('should display connection selector', async () => {
      const isLoaded = await locksPage.isLoaded();
      expect(isLoaded).toBe(true);
    });

    test('should display connection select dropdown', async () => {
      const isSelectVisible = await locksPage.page.locator(locksPage.connectionSelect).isVisible();
      expect(isSelectVisible).toBe(true);
    });

    test('should show empty state before connection selected', async () => {
      const isEmptyVisible = await locksPage.isConnectionEmptyStateVisible();
      expect(isEmptyVisible).toBe(true);
    });
  });

  test.describe('Connection Selection', () => {
    test('should display tabs after connection selected', async () => {
      await locksPage.page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });

      await locksPage.selectConnection('Test Connection');
      await locksPage.waitForLoadingComplete();

      const isTabsVisible = await locksPage.isTabsVisible();
      expect(isTabsVisible).toBe(true);
    });

    test('should show empty state for lock waits when no data', async () => {
      await locksPage.page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });

      await locksPage.page.route('**/api/locks/*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      });

      await locksPage.selectConnection('Test Connection');
      await locksPage.waitForLoadingComplete();

      const emptyText = await locksPage.getEmptyStateText();
      expect(emptyText).toContain('无锁等待');
    });
  });

  test.describe('Tab Navigation', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });

      await page.route('**/api/locks/*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      });

      await locksPage.selectConnection('Test Connection');
      await locksPage.waitForLoadingComplete();
    });

    test('should switch to deadlocks tab', async () => {
      await locksPage.clickDeadlocksTab();
      const isTimeRangeVisible = await locksPage.isTimeRangeSelectVisible();
      expect(isTimeRangeVisible).toBe(true);
    });

    test('should switch to lock graph tab', async () => {
      await locksPage.clickLockGraphTab();
      const isAutoRefreshVisible = await locksPage.isAutoRefreshCheckboxVisible();
      expect(isAutoRefreshVisible).toBe(true);
    });
  });

  test.describe('Lock Waits Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });

      await page.route('**/api/locks/*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      });

      await locksPage.selectConnection('Test Connection');
      await locksPage.waitForLoadingComplete();
    });

    test('should display refresh button', async () => {
      const isRefreshVisible = await locksPage.isRefreshButtonVisible();
      expect(isRefreshVisible).toBe(true);
    });

    test('should display table headers when data exists', async ({ page }) => {
      await page.route('**/api/locks/waits/1', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              requesting_trx_id: '12345',
              requested_lock_id: 'lock1',
              blocking_trx_id: '67890',
              blocking_lock_id: 'lock2',
              request_type: 'SHARED',
              lock_mode: 'SHARED',
              lock_type: 'RECORD',
              table_name: 'test_table',
              index_name: 'PRIMARY',
              lock_data: '1'
            }
          ])
        });
      });

      await locksPage.clickRefreshButton();

      const headers = await locksPage.getTableHeaders();
      expect(headers).toContain('请求事务ID');
      expect(headers).toContain('表名');
    });
  });

  test.describe('Deadlocks Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });

      await page.route('**/api/locks/*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      });

      await locksPage.selectConnection('Test Connection');
      await locksPage.waitForLoadingComplete();
      await locksPage.clickDeadlocksTab();
    });

    test('should display time range selector', async () => {
      const isTimeRangeVisible = await locksPage.isTimeRangeSelectVisible();
      expect(isTimeRangeVisible).toBe(true);
    });

    test('should change time range and reload data', async ({ page }) => {
      let requestCount = 0;
      await page.route('**/api/locks/deadlocks/1**', async (route) => {
        requestCount++;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      });

      await locksPage.selectTimeRange(12);

      expect(requestCount).toBeGreaterThan(0);
    });

    test('should display empty state when no deadlocks', async () => {
      const emptyText = await locksPage.getEmptyStateText();
      expect(emptyText).toContain('死锁');
    });
  });

  test.describe('Lock Graph Tab', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });

      await page.route('**/api/locks/*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ nodes: [], edges: [] })
        });
      });

      await locksPage.selectConnection('Test Connection');
      await locksPage.waitForLoadingComplete();
      await locksPage.clickLockGraphTab();
    });

    test('should display auto-refresh checkbox', async () => {
      const isCheckboxVisible = await locksPage.isAutoRefreshCheckboxVisible();
      expect(isCheckboxVisible).toBe(true);
    });

    test('should display graph container', async () => {
      const isChartVisible = await locksPage.isLockGraphChartVisible();
      expect(isChartVisible).toBe(true);
    });

    test('should display empty state when no graph data', async () => {
      const isEmptyVisible = await locksPage.isLockGraphEmptyVisible();
      expect(isEmptyVisible).toBe(true);
    });

    test('should refresh graph data', async ({ page }) => {
      let requestCount = 0;
      await page.route('**/api/locks/graph/**', async (route) => {
        requestCount++;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ nodes: [], edges: [] })
        });
      });

      await locksPage.clickRefreshButton();

      expect(requestCount).toBeGreaterThan(0);
    });
  });
});
