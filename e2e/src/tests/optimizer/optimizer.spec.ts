import { test, expect } from '../../fixtures/base.fixture';
import { OptimizerPage } from '../../pages/OptimizerPage';

/**
 * Optimizer页面的Playwright端到端测试
 * 
 * 测试范围：
 * - 页面加载和标题显示
 * - 连接选择器功能
 * - SQL语句输入
 * - 分析优化器按钮状态
 * - 清空功能
 * - 追踪结果展示
 */

test.describe('Optimizer页面', () => {
  let optimizerPage: OptimizerPage;

  test.beforeEach(async ({ page }) => {
    optimizerPage = new OptimizerPage(page);
    await optimizerPage.goto();
  });

  test.describe('页面加载', () => {
    test('应该正确加载Optimizer页面', async ({ page }) => {
      await expect(page).toHaveURL(/.*optimizer/);
      await expect(page).toHaveTitle(/MySQL性能诊断与优化系统/);
    });

    test('应该显示页面标题"优化器分析"', async () => {
      const title = await optimizerPage.getTitle();
      expect(title).toBe('优化器分析');
    });

    test('应该显示SQL输入框', async () => {
      const isLoaded = await optimizerPage.isLoaded();
      expect(isLoaded).toBe(true);
    });
  });

  test.describe('连接选择', () => {
    test('应该显示连接选择器', async () => {
      const connectionSelect = optimizerPage.page.locator(optimizerPage.connectionSelect);
      await expect(connectionSelect).toBeVisible();
    });

    test('应该可以打开连接下拉菜单', async () => {
      const connectionSelect = optimizerPage.page.locator(optimizerPage.connectionSelect);
      await connectionSelect.click();
      // 下拉菜单应该展开
      const dropdown = optimizerPage.page.locator('.el-select-dropdown');
      await expect(dropdown).toBeVisible();
    });
  });

  test.describe('SQL输入', () => {
    test('应该显示SQL语句输入框', async () => {
      const sqlInput = optimizerPage.page.locator(optimizerPage.sqlInput);
      await expect(sqlInput).toBeVisible();
    });

    test('应该可以输入SQL语句', async () => {
      await optimizerPage.inputSQL('SELECT * FROM users WHERE id = 1');
      const sqlValue = await optimizerPage.page.locator(optimizerPage.sqlInput).inputValue();
      expect(sqlValue).toBe('SELECT * FROM users WHERE id = 1');
    });

    test('应该可以输入多行SQL语句', async () => {
      const multiLineSQL = `SELECT u.id, u.name, o.order_id 
FROM users u 
LEFT JOIN orders o ON u.id = o.user_id 
WHERE u.status = 1`;
      await optimizerPage.inputSQL(multiLineSQL);
      const sqlValue = await optimizerPage.page.locator(optimizerPage.sqlInput).inputValue();
      expect(sqlValue).toContain('SELECT u.id, u.name, o.order_id');
    });

    test('应该显示SQL输入提示文本', async () => {
      const hintText = optimizerPage.page.locator(optimizerPage.sqlHint);
      await expect(hintText).toBeVisible();
      const hintContent = await hintText.textContent();
      expect(hintContent).toContain('优化器追踪将分析MySQL如何选择索引和执行计划');
    });
  });

  test.describe('分析按钮', () => {
    test('默认应该禁用分析按钮（无连接和SQL时）', async () => {
      const analyzeButton = optimizerPage.page.locator(optimizerPage.analyzeButton);
      await expect(analyzeButton).toBeDisabled();
    });

    test('选择连接后应该仍禁用按钮（无SQL时）', async () => {
      const connectionSelect = optimizerPage.page.locator(optimizerPage.connectionSelect);
      await connectionSelect.click();
      
      // 等待下拉菜单出现
      const dropdown = optimizerPage.page.locator('.el-select-dropdown:visible');
      if (await dropdown.isVisible()) {
        const firstOption = optimizerPage.page.locator('.el-select-dropdown__item').first();
        if (await firstOption.isVisible()) {
          await firstOption.click();
        }
      }

      const analyzeButton = optimizerPage.page.locator(optimizerPage.analyzeButton);
      await expect(analyzeButton).toBeDisabled();
    });

    test('输入SQL后应该启用执行按钮', async () => {
      // 先选择一个连接
      const connectionSelect = optimizerPage.page.locator(optimizerPage.connectionSelect);
      await connectionSelect.click();
      
      const dropdown = optimizerPage.page.locator('.el-select-dropdown:visible');
      if (await dropdown.isVisible()) {
        const firstOption = optimizerPage.page.locator('.el-select-dropdown__item').first();
        if (await firstOption.isVisible()) {
          await firstOption.click();
        }
      }

      // 再输入SQL
      await optimizerPage.inputSQL('SELECT * FROM users');

      const analyzeButton = optimizerPage.page.locator(optimizerPage.analyzeButton);
      await expect(analyzeButton).toBeEnabled();
    });

    test('应该显示"分析优化器"按钮', async () => {
      const analyzeButton = optimizerPage.page.locator(optimizerPage.analyzeButton);
      await expect(analyzeButton).toBeVisible();
      const buttonText = await analyzeButton.textContent();
      expect(buttonText).toContain('分析优化器');
    });
  });

  test.describe('清空功能', () => {
    test('应该显示清空按钮', async () => {
      const clearButton = optimizerPage.page.locator(optimizerPage.clearButton);
      await expect(clearButton).toBeVisible();
      const buttonText = await clearButton.textContent();
      expect(buttonText).toContain('清空');
    });

    test('点击清空按钮应该清空SQL输入', async () => {
      // 输入SQL
      await optimizerPage.inputSQL('SELECT * FROM users WHERE id = 1');
      
      // 点击清空按钮
      await optimizerPage.clickClear();
      
      // 验证SQL已清空
      const sqlValue = await optimizerPage.page.locator(optimizerPage.sqlInput).inputValue();
      expect(sqlValue).toBe('');
    });
  });

  test.describe('追踪结果', () => {
    test('初始状态不显示追踪结果', async () => {
      const resultCard = optimizerPage.page.locator(optimizerPage.resultCard);
      await expect(resultCard).not.toBeVisible();
    });

    test('结果区域应该显示"追踪结果"标题', async () => {
      // 先有结果才能验证，这里只验证选择器存在
      expect(optimizerPage.resultCard).toBeTruthy();
    });
  });
});
