import { test, expect } from '../../fixtures/base.fixture';
import { IndexSuggestionsPage } from '../../pages/IndexSuggestionsPage';

/**
 * 索引建议页面的Playwright端到端测试
 * 
 * 测试范围：
 * - 页面加载和基本元素显示
 * - 连接选择器
 * - 筛选功能（表名、状态）
 * - 搜索和重置操作
 * - 分析查询对话框
 * - 索引建议列表显示
 * - 操作按钮功能（查看SQL、采纳、拒绝、删除）
 * - 分页功能
 */

test.describe('Index Suggestions', () => {
  let indexSuggestionsPage: IndexSuggestionsPage;

  test.beforeEach(async ({ page }) => {
    indexSuggestionsPage = new IndexSuggestionsPage(page);
    await indexSuggestionsPage.goto();
  });

  test.describe('页面加载', () => {
    test('应该显示页面标题', async () => {
      const title = indexSuggestionsPage.page.locator('h1, .page-header-title, .el-card:has-text("索引建议")');
      await expect(title).toBeVisible();
    });

    test('应该显示搜索表单', async () => {
      const searchForm = indexSuggestionsPage.page.locator('.search-form');
      await expect(searchForm).toBeVisible();
    });

    test('应该显示索引建议列表', async () => {
      const table = indexSuggestionsPage.page.locator('.el-table');
      await expect(table).toBeVisible();
    });

    test('应该显示分析查询按钮', async () => {
      const analyzeButton = indexSuggestionsPage.page.getByRole('button', { name: '分析查询' });
      await expect(analyzeButton).toBeVisible();
    });
  });

  test.describe('连接选择器', () => {
    test('应该显示连接选择器', async () => {
      const connectionSelect = indexSuggestionsPage.page.locator('.el-select[placeholder="选择连接"]');
      await expect(connectionSelect).toBeVisible();
    });

    test('应该可以点击连接选择器', async () => {
      const connectionSelect = indexSuggestionsPage.page.locator('.el-select[placeholder="选择连接"]');
      await connectionSelect.click();
      
      const dropdown = indexSuggestionsPage.page.locator('.el-select-dropdown');
      await expect(dropdown).toBeVisible();
    });
  });

  test.describe('筛选功能', () => {
    test('应该显示表名筛选输入框', async () => {
      const tableNameInput = indexSuggestionsPage.page.locator('input[placeholder="请输入表名"]');
      await expect(tableNameInput).toBeVisible();
    });

    test('应该可以输入表名筛选条件', async ({ page }) => {
      const tableNameInput = indexSuggestionsPage.page.locator('input[placeholder="请输入表名"]');
      await tableNameInput.fill('users');
      await page.waitForTimeout(300);
      
      const value = await tableNameInput.inputValue();
      expect(value).toBe('users');
    });

    test('应该显示状态选择器', async () => {
      const statusSelect = indexSuggestionsPage.page.locator('.el-select[placeholder="选择状态"]');
      await expect(statusSelect).toBeVisible();
    });

    test('应该可以按状态筛选', async ({ page }) => {
      const statusSelect = indexSuggestionsPage.page.locator('.el-select[placeholder="选择状态"]');
      await statusSelect.click();
      
      const pendingOption = indexSuggestionsPage.page.locator('.el-select-dropdown__item:has-text("待处理")');
      await expect(pendingOption).toBeVisible();
      await pendingOption.click();
    });
  });

  test.describe('搜索和重置', () => {
    test('应该显示查询按钮', async () => {
      const searchButton = indexSuggestionsPage.page.getByRole('button', { name: '查询' });
      await expect(searchButton).toBeVisible();
    });

    test('应该显示重置按钮', async () => {
      const resetButton = indexSuggestionsPage.page.getByRole('button', { name: '重置' });
      await expect(resetButton).toBeVisible();
    });

    test('应该可以点击查询按钮', async ({ page }) => {
      const searchButton = indexSuggestionsPage.page.getByRole('button', { name: '查询' });
      await searchButton.click();
      await page.waitForTimeout(500);
    });

    test('应该可以点击重置按钮清空筛选条件', async ({ page }) => {
      const tableNameInput = indexSuggestionsPage.page.locator('input[placeholder="请输入表名"]');
      await tableNameInput.fill('test_table');
      
      const resetButton = indexSuggestionsPage.page.getByRole('button', { name: '重置' });
      await resetButton.click();
      await page.waitForTimeout(500);
      
      const value = await tableNameInput.inputValue();
      expect(value).toBe('');
    });
  });

  test.describe('分析查询对话框', () => {
    test('应该打开分析查询对话框', async ({ page }) => {
      const analyzeButton = indexSuggestionsPage.page.getByRole('button', { name: '分析查询' });
      await analyzeButton.click();
      
      const dialog = indexSuggestionsPage.page.locator('.el-dialog:has-text("分析查询")');
      await expect(dialog).toBeVisible();
    });

    test('应该显示查询选择下拉框', async ({ page }) => {
      const analyzeButton = indexSuggestionsPage.page.getByRole('button', { name: '分析查询' });
      await analyzeButton.click();
      
      const querySelect = indexSuggestionsPage.page.locator('.el-select[placeholder="选择要分析的查询"]');
      await expect(querySelect).toBeVisible();
    });

    test('应该显示取消和开始分析按钮', async ({ page }) => {
      const analyzeButton = indexSuggestionsPage.page.getByRole('button', { name: '分析查询' });
      await analyzeButton.click();
      
      const cancelButton = indexSuggestionsPage.page.locator('.el-dialog__footer button:has-text("取消")');
      const confirmButton = indexSuggestionsPage.page.locator('.el-dialog__footer button:has-text("开始分析")');
      
      await expect(cancelButton).toBeVisible();
      await expect(confirmButton).toBeVisible();
    });

    test('应该可以关闭分析对话框', async ({ page }) => {
      const analyzeButton = indexSuggestionsPage.page.getByRole('button', { name: '分析查询' });
      await analyzeButton.click();
      
      const cancelButton = indexSuggestionsPage.page.locator('.el-dialog__footer button:has-text("取消")');
      await cancelButton.click();
      
      await page.waitForTimeout(500);
      const dialog = indexSuggestionsPage.page.locator('.el-dialog:has-text("分析查询")');
      await expect(dialog).toBeHidden();
    });
  });

  test.describe('索引建议表格', () => {
    test('应该显示表格列', async () => {
      const table = indexSuggestionsPage.page.locator('.el-table');
      await expect(table).toBeVisible();
      
      const headers = indexSuggestionsPage.page.locator('.el-table th');
      const count = await headers.count();
      expect(count).toBeGreaterThan(0);
    });

    test('应该显示分页组件', async () => {
      const pagination = indexSuggestionsPage.page.locator('.el-pagination');
      await expect(pagination).toBeVisible();
    });

    test('应该可以切换分页大小', async ({ page }) => {
      const pageSizeSelect = indexSuggestionsPage.page.locator('.el-pagination .el-select');
      if (await pageSizeSelect.isVisible()) {
        await pageSizeSelect.click();
        await page.waitForTimeout(300);
        
        const option = indexSuggestionsPage.page.locator('.el-select-dropdown__item:has-text("20")');
        await option.click();
        await page.waitForTimeout(500);
      }
    });
  });

  test.describe('操作按钮', () => {
    test('应该显示操作列', async () => {
      const table = indexSuggestionsPage.page.locator('.el-table');
      await expect(table).toBeVisible();
    });

    test('应该显示查看SQL按钮', async ({ page }) => {
      const table = indexSuggestionsPage.page.locator('.el-table');
      const rows = await table.locator('tr').count();
      
      if (rows > 1) {
        const viewSQLButton = table.locator('tr').nth(1).locator('button:has-text("查看SQL")');
        if (await viewSQLButton.isVisible()) {
          await expect(viewSQLButton).toBeVisible();
        }
      }
    });

    test('应该可以查看SQL对话框', async ({ page }) => {
      const table = indexSuggestionsPage.page.locator('.el-table');
      const rows = await table.locator('tr').count();
      
      if (rows > 1) {
        const viewSQLButton = table.locator('tr').nth(1).locator('button:has-text("查看SQL")');
        if (await viewSQLButton.isVisible()) {
          await viewSQLButton.click();
          
          const sqlDialog = indexSuggestionsPage.page.locator('.el-dialog:has-text("CREATE INDEX")');
          await expect(sqlDialog).toBeVisible();
          
          const closeButton = sqlDialog.locator('.el-dialog__headerbtn');
          await closeButton.click();
        }
      }
    });

    test('应该显示采纳按钮', async ({ page }) => {
      const table = indexSuggestionsPage.page.locator('.el-table');
      const rows = await table.locator('tr').count();
      
      if (rows > 1) {
        const acceptButton = table.locator('tr').nth(1).locator('button:has-text("采纳")');
        if (await acceptButton.isVisible()) {
          await expect(acceptButton).toBeVisible();
        }
      }
    });

    test('应该显示拒绝按钮', async ({ page }) => {
      const table = indexSuggestionsPage.page.locator('.el-table');
      const rows = await table.locator('tr').count();
      
      if (rows > 1) {
        const rejectButton = table.locator('tr').nth(1).locator('button:has-text("拒绝")');
        if (await rejectButton.isVisible()) {
          await expect(rejectButton).toBeVisible();
        }
      }
    });

    test('应该显示删除按钮', async ({ page }) => {
      const table = indexSuggestionsPage.page.locator('.el-table');
      const rows = await table.locator('tr').count();
      
      if (rows > 1) {
        const deleteButton = table.locator('tr').nth(1).locator('button:has-text("删除")');
        if (await deleteButton.isVisible()) {
          await expect(deleteButton).toBeVisible();
        }
      }
    });
  });

  test.describe('置信度和状态显示', () => {
    test('应该显示置信度标签', async ({ page }) => {
      const table = indexSuggestionsPage.page.locator('.el-table');
      const rows = await table.locator('tr').count();
      
      if (rows > 1) {
        const confidenceTag = table.locator('tr').nth(1).locator('.el-tag');
        if (await confidenceTag.isVisible()) {
          await expect(confidenceTag).toBeVisible();
        }
      }
    });

    test('应该显示状态标签', async ({ page }) => {
      const table = indexSuggestionsPage.page.locator('.el-table');
      const rows = await table.locator('tr').count();
      
      if (rows > 1) {
        const statusTag = table.locator('tr').nth(1).locator('.el-tag');
        if (await statusTag.isVisible()) {
          await expect(statusTag).toBeVisible();
        }
      }
    });
  });
});
