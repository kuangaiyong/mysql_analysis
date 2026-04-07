import { test, expect } from '../../fixtures/base.fixture';
import { SessionsPage } from '../../pages/SessionsPage';

test.describe('Sessions Management', () => {
  let sessionsPage: SessionsPage;

  test.beforeEach(async ({ page }) => {
    sessionsPage = new SessionsPage(page);
    await sessionsPage.goto();
  });

  test.describe('Session List Page Load', () => {
    test('should display page title "会话管理"', async () => {
      const title = await sessionsPage.getTitle();
      expect(title).toBe('会话管理');
    });

    test('should display connection selector', async () => {
      const isLoaded = await sessionsPage.isLoaded();
      expect(isLoaded).toBe(true);
    });

    test('should display connection select dropdown', async () => {
      const isSelectVisible = await sessionsPage.page.locator(sessionsPage.connectionSelect).isVisible();
      expect(isSelectVisible).toBe(true);
    });
  });

  test.describe('Filter Form Display', () => {
    test('should display filter form inputs after connection selected', async () => {
      await sessionsPage.page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });
      await sessionsPage.selectConnection('Test Connection');
      await sessionsPage.waitForLoadingComplete();
      const isFilterVisible = await sessionsPage.isFilterFormVisible();
      expect(isFilterVisible).toBe(true);
    });
  });

  test.describe('Table Display', () => {
    test('should display table after connection selected and data loaded', async () => {
      await sessionsPage.page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });

      await sessionsPage.page.route('**/api/sessions/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              thread_id: 1,
              user: 'root',
              host: 'localhost',
              database: 'test',
              command: 'Query',
              time: 0,
              state: 'executing',
              info: 'SELECT 1'
            }
          ])
        });
      });

      await sessionsPage.selectConnection('Test Connection');
      await sessionsPage.waitForLoadingComplete();

      const isTableVisible = await sessionsPage.isTableVisible();
      expect(isTableVisible).toBe(true);
    });

    test('should display table headers', async () => {
      await sessionsPage.page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });

      await sessionsPage.page.route('**/api/sessions/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              thread_id: 1,
              user: 'root',
              host: 'localhost',
              database: 'test',
              command: 'Query',
              time: 0,
              state: 'executing',
              info: 'SELECT 1'
            }
          ])
        });
      });

      await sessionsPage.selectConnection('Test Connection');
      await sessionsPage.waitForLoadingComplete();

      const headers = await sessionsPage.getTableHeaders();
      expect(headers).toContain('Thread ID');
      expect(headers).toContain('用户');
    });
  });

  test.describe('Action Buttons', () => {
    test('should display refresh button', async () => {
      await sessionsPage.page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });

      await sessionsPage.page.route('**/api/sessions/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              thread_id: 1,
              user: 'root',
              host: 'localhost',
              database: 'test',
              command: 'Query',
              time: 0,
              state: 'executing',
              info: 'SELECT 1'
            }
          ])
        });
      });

      await sessionsPage.selectConnection('Test Connection');
      await sessionsPage.waitForLoadingComplete();

      const isRefreshVisible = await sessionsPage.page.locator(sessionsPage.refreshButton).isVisible();
      expect(isRefreshVisible).toBe(true);
    });

    test('should display export button', async () => {
      await sessionsPage.page.route('**/api/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
          ])
        });
      });

      await sessionsPage.page.route('**/api/sessions/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              thread_id: 1,
              user: 'root',
              host: 'localhost',
              database: 'test',
              command: 'Query',
              time: 0,
              state: 'executing',
              info: 'SELECT 1'
            }
          ])
        });
      });

      await sessionsPage.selectConnection('Test Connection');
      await sessionsPage.waitForLoadingComplete();

      const isExportVisible = await sessionsPage.page.locator(sessionsPage.exportButton).isVisible();
      expect(isExportVisible).toBe(true);
    });
  });
});
