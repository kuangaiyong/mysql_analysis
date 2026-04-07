import { test, expect } from '../../fixtures/base.fixture';
import { ConnectionsPage } from '../../pages/ConnectionsPage';

test.describe('Connections Management', () => {
  let connectionsPage: ConnectionsPage;

  test.beforeEach(async ({ page }) => {
    connectionsPage = new ConnectionsPage(page);
    await connectionsPage.goto();
  });

  test.describe('连接列表加载', () => {
    test('应该显示页面标题"连接管理"', async () => {
      const title = await connectionsPage.getTitle();
      expect(title).toBe('连接管理');
    });

    test('应该显示连接表格', async () => {
      const isLoaded = await connectionsPage.isLoaded();
      expect(isLoaded).toBe(true);
    });

    test('应该显示添加连接按钮', async () => {
      const isButtonVisible = await connectionsPage.page.locator(connectionsPage.addButton).isVisible();
      expect(isButtonVisible).toBe(true);
    });

    test('应该显示分页组件', async () => {
      const pagination = connectionsPage.page.locator('.el-pagination');
      await expect(pagination).toBeVisible();
    });
  });
});
