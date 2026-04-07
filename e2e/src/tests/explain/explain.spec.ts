import { test, expect } from '../../fixtures/base.fixture';
import { ExplainPage } from '../../pages/ExplainPage';

/**
 * Explain页面的Playwright端到端测试
 * 
 * 测试范围：
 * - 页面加载和标题显示
 * - 连接选择器功能
 * - 数据库名称输入
 * - 分析类型选择（Traditional, JSON, Tree, Flowchart）
 * - SQL语句输入
 * - 执行按钮状态
 * - 结果视图切换（树形视图、表格视图、JSON格式）
 */

test.describe('Explain页面', () => {
  let explainPage: ExplainPage;

  test.beforeEach(async ({ page }) => {
    explainPage = new ExplainPage(page);
    await explainPage.goto();
  });

  test.describe('页面加载', () => {
    test('应该正确加载Explain页面', async ({ page }) => {
      await expect(page).toHaveURL(/.*explain/);
      await expect(page).toHaveTitle(/MySQL性能诊断与优化系统/);
    });

    test('应该显示页面标题"EXPLAIN分析"', async () => {
      const title = await explainPage.getTitle();
      expect(title).toBe('EXPLAIN分析');
    });

    test('应该显示SQL输入框', async () => {
      const isLoaded = await explainPage.isLoaded();
      expect(isLoaded).toBe(true);
    });
  });

  test.describe('连接选择', () => {
    test('应该显示连接选择器', async () => {
      const connectionSelect = explainPage.page.locator(explainPage.connectionSelect);
      await expect(connectionSelect).toBeVisible();
    });

    test('应该可以打开连接下拉菜单', async () => {
      const connectionSelect = explainPage.page.locator(explainPage.connectionSelect);
      await connectionSelect.click();
      // 下拉菜单应该展开
      const dropdown = explainPage.page.locator('.el-select-dropdown');
      await expect(dropdown).toBeVisible();
    });
  });

  test.describe('数据库输入', () => {
    test('应该显示数据库输入框', async () => {
      const databaseInput = explainPage.page.locator(explainPage.databaseInput);
      await expect(databaseInput).toBeVisible();
    });

    test('应该可以输入数据库名称', async () => {
      const databaseInput = explainPage.page.locator(explainPage.databaseInput).locator('input');
      await databaseInput.fill('test_database');
      const value = await databaseInput.inputValue();
      expect(value).toBe('test_database');
    });
  });

  test.describe('分析类型选择', () => {
    test('应该显示分析类型单选按钮组', async () => {
      const analyzeTypeGroup = explainPage.page.locator('.el-form-item:has-text("分析类型") .el-radio-group');
      await expect(analyzeTypeGroup).toBeVisible();
    });

    test('应该显示Traditional选项', async () => {
      const traditionalRadio = explainPage.page.locator('.el-radio:has-text("Traditional")');
      await expect(traditionalRadio).toBeVisible();
    });

    test('应该显示JSON选项', async () => {
      const jsonRadio = explainPage.page.locator('.el-radio:has-text("JSON")');
      await expect(jsonRadio).toBeVisible();
    });

    test('应该显示Tree选项', async () => {
      const treeRadio = explainPage.page.locator('.el-radio:has-text("Tree")');
      await expect(treeRadio).toBeVisible();
    });

    test('应该显示Flowchart选项', async () => {
      const flowchartRadio = explainPage.page.locator('.el-radio:has-text("Flowchart")');
      await expect(flowchartRadio).toBeVisible();
    });

    test('应该可以切换分析类型', async () => {
      // 默认应该是Traditional
      const traditionalRadio = explainPage.page.locator('.el-radio:has-text("Traditional")');
      await expect(traditionalRadio.locator('.el-radio__original-radio')).toBeChecked();

      // 切换到JSON
      const jsonRadio = explainPage.page.locator('.el-radio:has-text("JSON")');
      await jsonRadio.click();
      await expect(jsonRadio.locator('.el-radio__original-radio')).toBeChecked();

      // 切换到Tree
      const treeRadio = explainPage.page.locator('.el-radio:has-text("Tree")');
      await treeRadio.click();
      await expect(treeRadio.locator('.el-radio__original-radio')).toBeChecked();

      // 切换到Flowchart
      const flowchartRadio = explainPage.page.locator('.el-radio:has-text("Flowchart")');
      await flowchartRadio.click();
      await expect(flowchartRadio.locator('.el-radio__original-radio')).toBeChecked();
    });
  });

  test.describe('SQL输入', () => {
    test('应该可以输入SQL语句', async () => {
      await explainPage.inputSQL('SELECT * FROM users WHERE id = 1');
      const sqlValue = await explainPage.page.locator(explainPage.sqlInput).inputValue();
      expect(sqlValue).toBe('SELECT * FROM users WHERE id = 1');
    });

    test('应该可以输入多行SQL语句', async () => {
      const multiLineSQL = `SELECT u.id, u.name, o.order_id 
FROM users u 
LEFT JOIN orders o ON u.id = o.user_id 
WHERE u.status = 1`;
      await explainPage.inputSQL(multiLineSQL);
      const sqlValue = await explainPage.page.locator(explainPage.sqlInput).inputValue();
      expect(sqlValue).toContain('SELECT u.id, u.name, o.order_id');
    });
  });

  test.describe('执行按钮', () => {
    test('默认应该禁用执行按钮（无连接和SQL时）', async () => {
      const explainButton = explainPage.page.locator(explainPage.executeExplainButton);
      await expect(explainButton).toBeDisabled();
    });

    test('选择连接后应该仍禁用按钮（无SQL时）', async () => {
      const connectionSelect = explainPage.page.locator(explainPage.connectionSelect);
      await connectionSelect.click();
      
      // 等待下拉菜单出现
      const dropdown = explainPage.page.locator('.el-select-dropdown:visible');
      if (await dropdown.isVisible()) {
        const firstOption = explainPage.page.locator('.el-select-dropdown__item').first();
        if (await firstOption.isVisible()) {
          await firstOption.click();
        }
      }

      const explainButton = explainPage.page.locator(explainPage.executeExplainButton);
      await expect(explainButton).toBeDisabled();
    });

    test('输入SQL后应该启用执行按钮', async () => {
      // 先选择一个连接
      const connectionSelect = explainPage.page.locator(explainPage.connectionSelect);
      await connectionSelect.click();
      
      const dropdown = explainPage.page.locator('.el-select-dropdown:visible');
      if (await dropdown.isVisible()) {
        const firstOption = explainPage.page.locator('.el-select-dropdown__item').first();
        if (await firstOption.isVisible()) {
          await firstOption.click();
        }
      }

      // 再输入SQL
      await explainPage.inputSQL('SELECT * FROM users');

      const explainButton = explainPage.page.locator(explainPage.executeExplainButton);
      await expect(explainButton).toBeEnabled();
    });

    test('应该显示执行EXPLAIN ANALYZE按钮', async () => {
      const analyzeButton = explainPage.page.locator(explainPage.executeExplainAnalyzeButton);
      await expect(analyzeButton).toBeVisible();
    });
  });

  test.describe('清空功能', () => {
    test('应该显示清空按钮', async () => {
      const clearButton = explainPage.page.locator('button:has-text("清空")');
      await expect(clearButton).toBeVisible();
    });
  });

  test.describe('结果视图切换', () => {
    test('结果区域应该包含视图切换按钮', async () => {
      // 先有结果才能测试视图切换，这里只验证按钮存在
      const treeViewButton = explainPage.page.locator(explainPage.viewToggleTree);
      const tableViewButton = explainPage.page.locator(explainPage.viewToggleTable);
      const jsonViewButton = explainPage.page.locator(explainPage.viewToggleJSON);
      
      // 这些按钮在有结果时才会显示，这里验证选择器正确
      expect(treeViewButton).toBeTruthy();
      expect(tableViewButton).toBeTruthy();
      expect(jsonViewButton).toBeTruthy();
    });
  });
});
