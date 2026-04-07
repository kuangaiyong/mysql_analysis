import { test, expect } from '../../fixtures/base.fixture';
import { SlowQueryPage } from '../../pages/SlowQueryPage';

/**
 * 慢查询页面的Playwright端到端测试
 * 
 * 测试范围：
 * - SQL搜索和筛选（摘要、时间范围、数据库、最小执行时间）
 * - 慢查询列表显示
 * - 跳转到慢查询详情页
 * - 优化建议功能
 * - 批量操作（标记已解决、删除）
 * - WebSocket实时推送新慢查询
 */

test.describe('Slow Query Analysis', () => {
  let slowQueryPage: SlowQueryPage;

  test.beforeEach(async ({ page }) => {
    slowQueryPage = new SlowQueryPage(page);
    await slowQueryPage.goto();
  });

  test.describe('搜索和筛选', () => {
    test('应该显示搜索表单', async () => {
      const searchForm = slowQueryPage.page.locator('.search-form');
      await expect(searchForm).toBeVisible();
    });

    test('应该执行SQL摘要搜索', async ({ page }) => {
      const sqlInput = slowQueryPage.page.locator('input[placeholder*="SQL摘要"]');
      await sqlInput.fill('SELECT * FROM users WHERE id = 1');
      
      const searchButton = slowQueryPage.page.getByRole('button', { name: '查询' });
      await searchButton.click();
      await page.waitForTimeout(1000);

      const table = slowQueryPage.page.locator('.el-table');
      await expect(table).toBeVisible();
    });

    test('应该按时间范围筛选', async ({ page }) => {
      const startTimeInput = slowQueryPage.page.locator('input[placeholder*="开始时间"]');
      const endTimeInput = slowQueryPage.page.locator('input[placeholder*="结束时间"]');
      
      await startTimeInput.fill('2024-01-01 00:00:00');
      await endTimeInput.fill('2024-01-01 23:59:59');
      
      const searchButton = slowQueryPage.page.getByRole('button', { name: '查询' });
      await searchButton.click();
      await page.waitForTimeout(1000);
    });

    test('应该按数据库筛选', async ({ page }) => {
      const databaseSelect = slowQueryPage.page.locator('.database-select');
      await databaseSelect.click();
      await slowQueryPage.page.locator('.el-select-dropdown__item:has-text("test_db")').click();
      
      const searchButton = slowQueryPage.page.getByRole('button', { name: '查询' });
      await searchButton.click();
      await page.waitForTimeout(1000);
    });

    test('应该按最小执行时间筛选', async ({ page }) => {
      const minTimeInput = slowQueryPage.page.locator('input[placeholder*="最小执行时间(秒)"]');
      await minTimeInput.fill('5');
      
      const searchButton = slowQueryPage.page.getByRole('button', { name: '查询' });
      await searchButton.click();
      await page.waitForTimeout(1000);
    });

    test('应该重置所有筛选条件', async ({ page }) => {
      const resetButton = slowQueryPage.page.getByRole('button', { name: '重置' });
      await resetButton.click();
      await page.waitForTimeout(500);
      
      // 验证搜索条件已清空
      const sqlInput = slowQueryPage.page.locator('input[placeholder*="SQL摘要"]');
      const value = await sqlInput.inputValue();
      expect(value).toBe('');
    });
  });

  test.describe('慢查询列表', () => {
    test('应该显示慢查询列表', async () => {
      const table = slowQueryPage.page.locator('.el-table');
      await expect(table).toBeVisible();
    });

    test('应该显示慢查询表格', async () => {
      const table = slowQueryPage.page.locator('.el-table');
      const rowCount = await table.locator('tr').count();
      expect(rowCount).toBeGreaterThan(0);
    });

    test('应该显示慢查询分页', async () => {
      const pagination = slowQueryPage.page.locator('.el-pagination');
      await expect(pagination).toBeVisible();
    });
  });

  test.describe('查看详情和优化建议', () => {
    test('应该跳转到慢查询详情页', async ({ page }) => {
      const table = slowQueryPage.page.locator('.el-table');
      const firstRow = table.locator('tr').first();
      
      const detailButton = firstRow.locator('button:has-text("详情")');
      await detailButton.click();
      
      await page.waitForURL(/.*slow-query\/detail/);
    });

    test('应该显示优化建议', async ({ page }) => {
      const optimizeButton = slowQueryPage.page.locator('button:has-text("优化建议")');
      await optimizeButton.click();
      
      const dialog = slowQueryPage.page.locator('.optimize-dialog');
      await expect(dialog).toBeVisible();
    });
  });

  test.describe('批量操作', () => {
    test('应该执行批量标记已解决', async ({ page }) => {
      const table = slowQueryPage.page.locator('.el-table');
      const checkboxes = table.locator('input[type="checkbox"]');
      
      const count = await checkboxes.count();
      if (count > 0) {
        await checkboxes.first().check();
        
        const batchResolveButton = slowQueryPage.page.getByRole('button', { name: '批量标记已解决' });
        await batchResolveButton.click();
        await slowQueryPage.page.locator('.el-message-box__btns button:has-text("确定")').click();
        
        const successMessage = slowQueryPage.page.locator('.el-message--success');
        await expect(successMessage).toContainText('已批量标记');
      }
    });

    test('应该执行批量删除慢查询', async ({ page }) => {
      const table = slowQueryPage.page.locator('.el-table');
      const checkboxes = table.locator('input[type="checkbox"]');
      
      const count = await checkboxes.count();
      if (count > 0) {
        await checkboxes.first().check();
        
        const batchDeleteButton = slowQueryPage.page.getByRole('button', { name: '批量删除' });
        await batchDeleteButton.click();
        await slowQueryPage.page.locator('.el-message-box__btns button:has-text("确定")').click();
        
        const successMessage = slowQueryPage.page.locator('.el-message--success');
        await expect(successMessage).toContainText('已批量删除');
      }
    });
  });

  test.describe('WebSocket实时推送', () => {
    test('应该接收新慢查询并更新列表', async ({ page }) => {
      const initialCount = await slowQueryPage.page.locator('tr').count();
      
      await page.evaluate(() => {
        (window as any).__testPushSlowQuery({
          query_hash: 'abc123',
          sql_digest: 'SELECT * FROM users WHERE id = 1',
          query_time: 2.5,
          timestamp: Date.now()
        });
      });

      await page.waitForTimeout(500);
      
      const newCount = await slowQueryPage.page.locator('tr').count();
      expect(newCount).toBeGreaterThan(initialCount);
    });

    test('应该显示新慢查询通知', async ({ page }) => {
      await page.evaluate(() => {
        (window as any).__testPushSlowQuery({
          query_hash: 'def456',
          sql_digest: 'UPDATE users SET name = ?',
          query_time: 5.2,
          timestamp: Date.now()
        });
      });

      await page.waitForTimeout(500);
      
      const notification = page.locator('.el-notification');
      await expect(notification).toBeVisible();
    });
  });
});
