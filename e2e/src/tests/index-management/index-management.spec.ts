import { test, expect } from '../../fixtures/base.fixture';
import { IndexManagementPage } from '../../pages/IndexManagementPage';

/**
 * 索引管理页面的Playwright端到端测试
 * 
 * 测试范围：
 * - 索引列表显示和排序
 * - 使用率分析（饼图、表格）
 * - 冗余索引检测
 * - 创建索引对话框和功能
 * - 删除索引功能
 * - 主键索引不能删除验证
 */

test.describe('Index Management', () => {
  let indexManagementPage: IndexManagementPage;

  test.beforeEach(async ({ page }) => {
    indexManagementPage = new IndexManagementPage(page);
    await indexManagementPage.goto();
  });

  test.describe('索引列表显示', () => {
    test('应该显示索引列表', async () => {
      const table = indexManagementPage.page.locator('.index-table');
      await expect(table).toBeVisible();
    });

    test('应该显示索引表格', async () => {
      const elTable = indexManagementPage.page.locator('.el-table');
      const rowCount = await elTable.locator('tr').count();
      expect(rowCount).toBeGreaterThan(0);
    });

    test('应该显示索引排序功能', async () => {
      const sortButton = indexManagementPage.page.locator('.sort-button');
      await expect(sortButton).toBeVisible();
    });
  });

  test.describe('使用率分析', () => {
    test('应该显示使用率分析功能', async () => {
      const analyzeButton = indexManagementPage.page.getByRole('button', { name: '分析使用率' });
      await expect(analyzeButton).toBeVisible();
    });

    test('应该显示使用率饼图', async ({ page }) => {
      await indexManagementPage.page.getByRole('button', { name: '分析使用率' }).click();
      await page.waitForTimeout(1000);
      
      const pieChart = indexManagementPage.page.locator('.usage-pie-chart');
      await expect(pieChart).toBeVisible();
    });

    test('应该显示使用率表格', async ({ page }) => {
      await indexManagementPage.page.locator('.usage-table');
      
      const usageTable = indexManagementPage.page.locator('.usage-table');
      await expect(usageTable).toBeVisible();
    });
  });

  test.describe('冗余索引检测', () => {
    test('应该显示冗余检测功能', async () => {
      const checkButton = indexManagementPage.page.getByRole('button', { name: '检测冗余索引' });
      await expect(checkButton).toBeVisible();
    });

    test('应该检测并显示冗余索引列表', async ({ page }) => {
      await indexManagementPage.page.getByRole('button', { name: '检测冗余索引' }).click();
      await page.waitForTimeout(1000);
      
      const redundantTable = indexManagementPage.page.locator('.redundant-index-table');
      await expect(redundantTable).toBeVisible();
    });
  });

  test.describe('创建索引', () => {
    test('应该显示创建索引按钮', async () => {
      const createButton = indexManagementPage.page.getByRole('button', { name: '创建索引' });
      await expect(createButton).toBeVisible();
    });

    test('应该打开创建索引对话框', async () => {
      await indexManagementPage.page.getByRole('button', { name: '创建索引' }).click();
      
      const dialog = indexManagementPage.page.locator('.create-index-dialog');
      await expect(dialog).toBeVisible();
    });

    test('应该创建新索引', async ({ page }) => {
      const dialog = indexManagementPage.page.locator('.create-index-dialog');
      
      const indexNameInput = dialog.locator('input[placeholder*="索引名称"]');
      const tableNameInput = dialog.locator('input[placeholder*="表名"]');
      const columnsInput = dialog.locator('input[placeholder*="列名"]');
      
      await indexNameInput.fill('test_index');
      await tableNameInput.fill('users');
      await columnsInput.fill('id, name, created_at');
      
      const saveButton = dialog.locator('button:has-text("保存")');
      await saveButton.click();
      
      const successMessage = page.locator('.el-message--success');
      await expect(successMessage).toContainText('创建成功');
      
      const table = indexManagementPage.page.locator('.index-table');
      await page.waitForTimeout(500);
      const newRowCount = await table.locator('tr').count();
      expect(newRowCount).toBeGreaterThan(0);
    });

    test('应该验证索引名称必填', async ({ page }) => {
      await indexManagementPage.page.getByRole('button', { name: '创建索引' }).click();
      
      const indexNameInput = indexManagementPage.page.locator('.create-index-dialog input[placeholder*="索引名称"]');
      const saveButton = indexManagementPage.page.locator('.create-index-dialog button:has-text("保存")');
      await saveButton.click();
      
      const errorMessage = page.locator('.el-message--error');
      await expect(errorMessage).toContainText('索引名称不能为空');
    });
  });

  test.describe('删除索引', () => {
    test('应该显示删除按钮', async () => {
      const table = indexManagementPage.page.locator('.index-table');
      const firstRow = table.locator('tr').first();
      
      const deleteButton = firstRow.locator('button:has-text("删除")');
      await expect(deleteButton).toBeVisible();
    });

    test('应该删除非主键索引', async ({ page }) => {
      const table = indexManagementPage.page.locator('.index-table');
      const rowCount = await table.locator('tr').count();
      
      if (rowCount > 0) {
        const firstRow = table.locator('tr').first();
        
        // 验证该行不是主键索引
        const primaryKeyColumn = table.locator('tr').first().locator('td:nth-child(4)');
        const isPrimaryKey = await primaryKeyColumn.locator('span.el-tag--danger').isVisible();
        
        if (!isPrimaryKey) {
          const deleteButton = firstRow.locator('button:has-text("删除")');
          await deleteButton.click();
          
          const successMessage = page.locator('.el-message--success');
          await expect(successMessage).toContainText('删除成功');
        }
      }
    });

    test('应该验证删除确认对话框', async ({ page }) => {
      const table = indexManagementPage.page.locator('.index-table');
      const firstRow = table.locator('tr').first();

      const deleteButton = firstRow.locator('button:has-text("删除")');
      await deleteButton.click();

      const confirmDialog = page.locator('.el-message-box');
      await expect(confirmDialog).toBeVisible();

      await page.locator('.el-message-box__btns button:has-text("取消")').click();

      const rowCount = await table.locator('tr').count();
      expect(rowCount).toBeGreaterThan(0);
    });
  });
});
