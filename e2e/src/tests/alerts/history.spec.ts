import { test, expect } from '../../fixtures/base.fixture';
import { AlertHistoryPage } from '../../pages/AlertHistoryPage';

/**
 * 告警历史页面的Playwright端到端测试
 * 
 * 测试范围：
 * - 告警历史页面加载
 * - 页面标题显示
 * - 告警历史表格显示
 * - 筛选表单显示
 * - 分页组件显示
 * - 时间范围筛选功能
 */

test.describe('Alert History', () => {
  let alertHistoryPage: AlertHistoryPage;

  test.beforeEach(async ({ page }) => {
    alertHistoryPage = new AlertHistoryPage(page);
    await alertHistoryPage.goto();
  });

  test.describe('页面加载', () => {
    test('应该正确加载告警历史页面', async ({ page }) => {
      await expect(page).toHaveURL(/.*alerts\/history/);
    });

    test('应该显示页面标题', async () => {
      const title = await alertHistoryPage.getTitle();
      expect(title).toBeTruthy();
    });

    test('应该显示告警历史表格', async () => {
      const isLoaded = await alertHistoryPage.isLoaded();
      expect(isLoaded).toBe(true);
    });

    test('应该显示筛选表单', async () => {
      const filterForm = alertHistoryPage.page.locator(alertHistoryPage.filterForm);
      await expect(filterForm).toBeVisible();
    });

    test('应该显示查询按钮', async () => {
      const searchButton = alertHistoryPage.page.locator(alertHistoryPage.searchButton);
      await expect(searchButton).toBeVisible();
    });

    test('应该显示重置按钮', async () => {
      const resetButton = alertHistoryPage.page.locator(alertHistoryPage.resetButton);
      await expect(resetButton).toBeVisible();
    });

    test('应该显示分页组件', async () => {
      const pagination = alertHistoryPage.page.locator('.el-pagination');
      await expect(pagination).toBeVisible();
    });
  });

  test.describe('筛选功能', () => {
    test('应该能够输入开始时间', async () => {
      const startTimeInput = alertHistoryPage.page.locator('input[placeholder*="开始时间"]');
      await expect(startTimeInput).toBeVisible();
    });

    test('应该能够输入结束时间', async () => {
      const endTimeInput = alertHistoryPage.page.locator('input[placeholder*="结束时间"]');
      await expect(endTimeInput).toBeVisible();
    });

    test('应该能够点击查询按钮', async () => {
      const searchButton = alertHistoryPage.page.locator(alertHistoryPage.searchButton);
      await searchButton.click();
    });

    test('应该能够点击重置按钮', async () => {
      const resetButton = alertHistoryPage.page.locator(alertHistoryPage.resetButton);
      await resetButton.click();
    });
  });

  test.describe('表格功能', () => {
    test('表格应该包含必要的列', async () => {
      const table = alertHistoryPage.page.locator(alertHistoryPage.historyTable);
      await expect(table).toBeVisible();
      
      // 检查表格是否有表头
      const tableHeader = table.locator('thead');
      await expect(tableHeader).toBeVisible();
    });

    test('表格应该包含数据行或空状态', async () => {
      const tableBody = alertHistoryPage.page.locator(`${alertHistoryPage.historyTable} tbody`);
      await expect(tableBody).toBeVisible();
    });
  });

  test.describe('批量操作', () => {
    test('应该显示批量解决按钮', async () => {
      const batchResolveButton = alertHistoryPage.page.locator(alertHistoryPage.batchResolveButton);
      await expect(batchResolveButton).toBeVisible();
    });
  });
});
