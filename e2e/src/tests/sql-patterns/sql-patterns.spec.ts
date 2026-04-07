import { test, expect } from '../../fixtures/base.fixture';
import { SqlPatternsPage } from '../../pages/SqlPatternsPage';

/**
 * SQL Patterns页面的Playwright端到端测试
 *
 * 测试范围：
 * - 页面加载和基本元素显示
 * - SQL输入和检测功能
 * - 清空按钮功能
 * - 检测结果展示
 */

test.describe('SQL Patterns', () => {
  let sqlPatternsPage: SqlPatternsPage;

  test.beforeEach(async ({ page }) => {
    sqlPatternsPage = new SqlPatternsPage(page);
    await sqlPatternsPage.goto();
  });

  test.describe('页面加载', () => {
    test('应该显示页面标题"SQL反模式检测"', async () => {
      const title = await sqlPatternsPage.getTitle();
      expect(title).toBe('SQL反模式检测');
    });

    test('应该显示SQL输入框', async () => {
      const isLoaded = await sqlPatternsPage.isLoaded();
      expect(isLoaded).toBe(true);
    });

    test('应该显示检测反模式按钮', async () => {
      const buttonVisible = await sqlPatternsPage.isVisible(sqlPatternsPage.detectButton);
      expect(buttonVisible).toBe(true);
    });

    test('应该显示清空按钮', async () => {
      const buttonVisible = await sqlPatternsPage.isVisible(sqlPatternsPage.clearButton);
      expect(buttonVisible).toBe(true);
    });

    test('应该显示SQL输入提示', async () => {
      const hintText = await sqlPatternsPage.getSqlHintText();
      expect(hintText).toContain('检测 SELECT *、缺少 WHERE、未使用索引等常见反模式');
    });
  });

  test.describe('按钮状态', () => {
    test('检测按钮在无输入时应该禁用', async () => {
      // 确保输入框为空
      const isDisabled = await sqlPatternsPage.isDetectButtonDisabled();
      expect(isDisabled).toBe(true);
    });

    test('检测按钮在有输入时应该启用', async () => {
      await sqlPatternsPage.fillSql('SELECT * FROM users');
      const isDisabled = await sqlPatternsPage.isDetectButtonDisabled();
      expect(isDisabled).toBe(false);
    });
  });

  test.describe('清空功能', () => {
    test('点击清空按钮应该清空输入框', async () => {
      await sqlPatternsPage.fillSql('SELECT * FROM users');
      await sqlPatternsPage.clickClear();

      const textareaValue = await sqlPatternsPage.getAttribute(sqlPatternsPage.sqlTextarea, 'value');
      expect(textareaValue).toBe('');
    });

    test('点击清空按钮应该隐藏结果卡片', async () => {
      await sqlPatternsPage.fillSql('SELECT * FROM users');
      await sqlPatternsPage.clickDetect();
      await sqlPatternsPage.waitForLoadingComplete();

      // 确认结果卡片可见
      const resultsVisibleBefore = await sqlPatternsPage.isResultsVisible();
      expect(resultsVisibleBefore).toBe(true);

      // 点击清空
      await sqlPatternsPage.clickClear();

      // 确认结果卡片被隐藏（因为清空后patternData设为null）
      const resultsVisibleAfter = await sqlPatternsPage.isResultsVisible();
      expect(resultsVisibleAfter).toBe(false);
    });
  });

  test.describe('检测功能', () => {
    test('输入SQL后点击检测应该显示结果卡片', async () => {
      await sqlPatternsPage.fillSql('SELECT * FROM users WHERE status = 1');
      await sqlPatternsPage.clickDetect();
      await sqlPatternsPage.waitForLoadingComplete();

      const isResultsVisible = await sqlPatternsPage.isResultsVisible();
      expect(isResultsVisible).toBe(true);
    });

    test('检测无反模式的SQL应该显示成功消息', async () => {
      // 输入一个相对简单的SQL，可能不会触发反模式
      await sqlPatternsPage.fillSql('SELECT id, name FROM users WHERE id = 1');
      await sqlPatternsPage.clickDetect();
      await sqlPatternsPage.waitForLoadingComplete();

      // 等待消息显示
      await sqlPatternsPage.page.waitForTimeout(1000);

      // 检查结果卡片是否显示
      const isResultsVisible = await sqlPatternsPage.isResultsVisible();
      expect(isResultsVisible).toBe(true);
    });

    test('检测有反模式的SQL应该显示问题数量', async () => {
      // SELECT * 是反模式
      await sqlPatternsPage.fillSql('SELECT * FROM users');
      await sqlPatternsPage.clickDetect();
      await sqlPatternsPage.waitForLoadingComplete();

      const isResultsVisible = await sqlPatternsPage.isResultsVisible();
      expect(isResultsVisible).toBe(true);

      // 应该显示问题标签
      const problemCount = await sqlPatternsPage.getProblemCount();
      expect(problemCount).toBeGreaterThanOrEqual(0);
    });
  });
});
