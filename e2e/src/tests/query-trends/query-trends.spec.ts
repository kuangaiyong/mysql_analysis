import { test, expect } from '../../fixtures/base.fixture';
import { QueryTrendsPage } from '../../pages/QueryTrendsPage';

/**
 * 查询指纹趋势页面的Playwright端到端测试
 * 
 * 测试范围：
 * - 页面加载和标题显示
 * - 连接选择器
 * - 时间范围筛选
 * - 表名筛选
 * - 查询指纹列表显示
 * - 分页功能
 * - 趋势图表和数据列表Tab切换
 * - 生成指纹功能
 * - 导出CSV功能
 */

test.describe('Query Trends Analysis', () => {
  let queryTrendsPage: QueryTrendsPage;

  test.beforeEach(async ({ page }) => {
    queryTrendsPage = new QueryTrendsPage(page);
    await queryTrendsPage.goto();
  });

  test.describe('页面加载', () => {
    test('应该显示页面标题"查询指纹趋势分析"', async () => {
      const title = await queryTrendsPage.getTitle();
      expect(title).toBe('查询指纹趋势分析');
    });

    test('应该显示搜索表单', async () => {
      const searchForm = queryTrendsPage.page.locator('.search-form');
      await expect(searchForm).toBeVisible();
    });

    test('应该显示连接选择器', async () => {
      const connectionSelect = queryTrendsPage.page.locator('input[placeholder="选择连接"]');
      await expect(connectionSelect).toBeVisible();
    });

    test('应该显示时间范围选择器', async () => {
      const timeRangeSelect = queryTrendsPage.page.locator('.el-select').nth(1);
      await expect(timeRangeSelect).toBeVisible();
    });

    test('应该显示表名输入框', async () => {
      const tableNameInput = queryTrendsPage.page.locator('input[placeholder="请输入表名"]');
      await expect(tableNameInput).toBeVisible();
    });

    test('应该显示查询和重置按钮', async () => {
      const searchButton = queryTrendsPage.page.getByRole('button', { name: '查询' });
      const resetButton = queryTrendsPage.page.getByRole('button', { name: '重置' });
      await expect(searchButton).toBeVisible();
      await expect(resetButton).toBeVisible();
    });

    test('应该显示生成指纹和导出CSV按钮', async () => {
      const generateButton = queryTrendsPage.page.getByRole('button', { name: '生成指纹' });
      const exportButton = queryTrendsPage.page.getByRole('button', { name: '导出CSV' });
      await expect(generateButton).toBeVisible();
      await expect(exportButton).toBeVisible();
    });
  });

  test.describe('Tab切换', () => {
    test('应该默认显示数据列表Tab', async () => {
      const tableTab = queryTrendsPage.page.locator('.el-tabs__item').filter({ hasText: '数据列表' });
      await expect(tableTab).toHaveClass(/is-active/);
    });

    test('应该可以切换到趋势图表Tab', async () => {
      await queryTrendsPage.switchToChartTab();
      const chartTab = queryTrendsPage.page.locator('.el-tabs__item').filter({ hasText: '趋势图表' });
      await expect(chartTab).toHaveClass(/is-active/);
    });

    test('应该可以切换回数据列表Tab', async () => {
      await queryTrendsPage.switchToChartTab();
      await queryTrendsPage.switchToTableTab();
      const tableTab = queryTrendsPage.page.locator('.el-tabs__item').filter({ hasText: '数据列表' });
      await expect(tableTab).toHaveClass(/is-active/);
    });
  });

  test.describe('搜索和筛选', () => {
    test('应该可以按表名筛选', async ({ page }) => {
      const tableNameInput = queryTrendsPage.page.locator('input[placeholder="请输入表名"]');
      await tableNameInput.fill('users');
      
      const searchButton = queryTrendsPage.page.getByRole('button', { name: '查询' });
      await searchButton.click();
      await page.waitForTimeout(1000);
      
      const table = queryTrendsPage.page.locator('.el-table');
      await expect(table).toBeVisible();
    });

    test('应该可以重置筛选条件', async ({ page }) => {
      const tableNameInput = queryTrendsPage.page.locator('input[placeholder="请输入表名"]');
      await tableNameInput.fill('test_table');
      
      const resetButton = queryTrendsPage.page.getByRole('button', { name: '重置' });
      await resetButton.click();
      await page.waitForTimeout(500);
      
      const value = await tableNameInput.inputValue();
      expect(value).toBe('');
    });

    test('应该可以切换时间范围', async ({ page }) => {
      await queryTrendsPage.page.locator('.el-select').nth(1).click();
      await queryTrendsPage.page.locator('.el-select-dropdown__item:has-text("最近7天")').click();
      await page.waitForTimeout(500);
    });
  });

  test.describe('查询指纹列表', () => {
    test('应该显示查询指纹表格', async () => {
      const table = queryTrendsPage.page.locator('.el-table');
      await expect(table).toBeVisible();
    });

    test('应该显示表格列标题', async () => {
      const table = queryTrendsPage.page.locator('.el-table');
      const headerText = await table.locator('.el-table__header').textContent();
      expect(headerText).toContain('指纹哈希');
      expect(headerText).toContain('规范化SQL');
      expect(headerText).toContain('表名');
      expect(headerText).toContain('数据库');
      expect(headerText).toContain('执行次数');
    });

    test('应该显示分页组件', async () => {
      const pagination = queryTrendsPage.page.locator('.el-pagination');
      await expect(pagination).toBeVisible();
    });
  });

  test.describe('分页功能', () => {
    test('应该显示分页总数', async () => {
      const paginationTotal = queryTrendsPage.page.locator('.el-pagination__total');
      await expect(paginationTotal).toBeVisible();
    });

    test('应该可以切换每页显示数量', async ({ page }) => {
      const sizeSelect = queryTrendsPage.page.locator('.el-select').last();
      await sizeSelect.click();
      await queryTrendsPage.page.locator('.el-select-dropdown__item:has-text("50")').click();
      await page.waitForTimeout(500);
    });

    test('应该可以点击下一页', async ({ page }) => {
      const nextButton = queryTrendsPage.page.locator('.el-pagination button.btn-next');
      const isDisabled = await nextButton.getAttribute('disabled');
      if (!isDisabled) {
        await nextButton.click();
        await page.waitForTimeout(500);
      }
    });
  });
});
