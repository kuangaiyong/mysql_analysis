import { test, expect } from '../../fixtures/base.fixture';
import { TableStructurePage } from '../../pages/TableStructurePage';

/**
 * 表结构页面的Playwright端到端测试
 * 
 * 测试范围：
 * - 表列表显示和搜索
 * - 多Tab页面切换（表结构、统计信息、外键关系、DDL查看）
 * - DDL复制功能
 */

test.describe('Table Structure', () => {
  let tableStructurePage: TableStructurePage;

  test.beforeEach(async ({ page }) => {
    tableStructurePage = new TableStructurePage(page);
    await tableStructurePage.goto();
  });

  test.describe('表列表显示', () => {
    test('应该显示表列表', async () => {
      const table = tableStructurePage.page.locator('.table-list');
      await expect(table).toBeVisible();
    });

    test('应该显示表数量', async () => {
      const tableCount = tableStructurePage.page.locator('.table-count');
      await expect(tableCount).toBeVisible();
    });

    test('应该显示搜索框', async () => {
      const searchInput = tableStructurePage.page.locator('.search-input');
      await expect(searchInput).toBeVisible();
    });
  });

  test.describe('表搜索功能', () => {
    test('应该按表名搜索', async ({ page }) => {
      const searchInput = tableStructurePage.page.locator('.search-input');
      const searchButton = tableStructurePage.page.getByRole('button', { name: '搜索' });
      
      await searchInput.fill('users');
      await searchButton.click();
      await page.waitForTimeout(1000);
      
      const table = tableStructurePage.page.locator('.table-list');
      const filteredRows = await table.locator('tr').count();
      expect(filteredRows).toBeGreaterThan(0);
    });

    test('应该重置搜索条件', async ({ page }) => {
      const resetButton = tableStructurePage.page.getByRole('button', { name: '重置' });
      await resetButton.click();
      await page.waitForTimeout(500);
      
      const searchInput = tableStructurePage.page.locator('.search-input');
      const value = await searchInput.inputValue();
      expect(value).toBe('');
    });
  });

  test.describe('多Tab页面', () => {
    test('应该默认显示表结构Tab', async () => {
      const structureTab = tableStructurePage.page.locator('.tab-item:has-text("表结构")');
      await expect(structureTab).toHaveClass(/is-active/);
    });

    test('应该点击统计信息Tab', async ({ page }) => {
      const statsTab = tableStructurePage.page.locator('.tab-item:has-text("统计信息")');
      await statsTab.click();
      
      const statsContent = tableStructurePage.page.locator('.stats-content');
      await expect(statsContent).toBeVisible();
    });

    test('应该点击外键关系Tab', async ({ page }) => {
      const foreignKeysTab = tableStructurePage.page.locator('.tab-item:has-text("外键关系")');
      await foreignKeysTab.click();
      
      const foreignKeysContent = tableStructurePage.page.locator('.foreign-keys-content');
      await expect(foreignKeysContent).toBeVisible();
    });
  });

  test.describe('DDL查看和复制', () => {
    test('应该点击DDL查看Tab', async ({ page }) => {
      const ddlTab = tableStructurePage.page.locator('.tab-item:has-text("DDL查看")');
      await ddlTab.click();
      
      const ddlContent = tableStructurePage.page.locator('.ddl-content');
      await expect(ddlContent).toBeVisible();
    });

    test('应该显示DDL复制按钮', async () => {
      const ddlContent = tableStructurePage.page.locator('.ddl-content');
      const copyButton = ddlContent.locator('button:has-text("复制DDL")');
      await expect(copyButton).toBeVisible();
    });

    test('应该复制DDL到剪贴板', async ({ page }) => {
      const ddlContent = tableStructurePage.page.locator('.ddl-content');
      const copyButton = ddlContent.locator('button:has-text("复制DDL")');
      await copyButton.click();
      
      const successMessage = page.locator('.el-message--success');
      await expect(successMessage).toContainText('已复制到剪贴板');
      
      const ddlText = await ddlContent.locator('pre').textContent();
      expect(ddlText.length).toBeGreaterThan(0);
    });

    test('应该显示DDL内容', async () => {
      const ddlTab = tableStructurePage.page.locator('.tab-item:has-text("DDL查看")');
      await ddlTab.click();
      
      const ddlContent = tableStructurePage.page.locator('.ddl-content');
      await expect(ddlContent).toBeVisible();
    });
  });
});
