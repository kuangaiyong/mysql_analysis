import { test, expect } from '../../fixtures/base.fixture';
import { TuningPage } from '../../pages/TuningPage';

test.describe('Tuning Page', () => {
  let tuningPage: TuningPage;

  test.beforeEach(async ({ page }) => {
    tuningPage = new TuningPage(page);
    await tuningPage.goto();
  });

  test.describe('页面加载', () => {
    test('应该正确加载Tuning页面', async ({ page }) => {
      await page.goto('/tuning');
      await expect(page).toHaveURL(/.*tuning/);
      await expect(page).toHaveTitle(/MySQL性能诊断与优化系统/);
    });

    test('应该显示页面标题', async () => {
      const title = await tuningPage.getTitle();
      expect(title).toBe('调优建议');
    });

    test('应该显示页面加载完成', async () => {
      const isLoaded = await tuningPage.isLoaded();
      expect(isLoaded).toBe(true);
    });
  });

  test.describe('连接选择器', () => {
    test('应该显示连接选择器', async () => {
      const connectionSelector = tuningPage.page.locator(tuningPage.connectionSelector);
      await expect(connectionSelector).toBeVisible();
    });
  });

  test.describe('标签页切换', () => {
    test('应该默认显示索引建议标签', async () => {
      const indexTab = tuningPage.page.locator(tuningPage.indexTab);
      await expect(indexTab).toBeVisible();
      const activeTab = tuningPage.page.locator('.el-tabs__item.is-active');
      const activeText = await activeTab.textContent();
      expect(activeText).toContain('索引建议');
    });

    test('应该可以切换到SQL改写标签', async () => {
      await tuningPage.switchToRewriteTab();
      const rewriteTab = tuningPage.page.locator(tuningPage.rewriteTab);
      await expect(rewriteTab).toBeVisible();
    });

    test('应该可以切换到InnoDB调优标签', async () => {
      await tuningPage.switchToInnoDBTab();
      const innodbTab = tuningPage.page.locator(tuningPage.innodbTab);
      await expect(innodbTab).toBeVisible();
    });
  });

  test.describe('索引建议功能', () => {
    test('应该显示索引建议输入框', async () => {
      await tuningPage.switchToIndexTab();
      const sqlInput = tuningPage.page.locator(tuningPage.sqlInputIndex);
      await expect(sqlInput).toBeVisible();
    });

    test('应该显示分析索引建议按钮', async () => {
      await tuningPage.switchToIndexTab();
      const button = tuningPage.page.locator(tuningPage.analyzeIndexButton);
      await expect(button).toBeVisible();
    });

    test('应该显示清空按钮', async () => {
      await tuningPage.switchToIndexTab();
      const button = tuningPage.page.locator(tuningPage.clearIndexButton);
      await expect(button).toBeVisible();
    });

    test('输入SQL后分析按钮应该可用', async () => {
      await tuningPage.switchToIndexTab();
      await tuningPage.enterIndexSQL('SELECT * FROM users WHERE id = 1');
      const button = tuningPage.page.locator(tuningPage.analyzeIndexButton);
      await expect(button).toBeEnabled();
    });
  });

  test.describe('SQL改写功能', () => {
    test('应该显示SQL改写输入框', async () => {
      await tuningPage.switchToRewriteTab();
      const sqlInput = tuningPage.page.locator(tuningPage.sqlInputRewrite);
      await expect(sqlInput).toBeVisible();
    });

    test('应该显示分析改写建议按钮', async () => {
      await tuningPage.switchToRewriteTab();
      const button = tuningPage.page.locator(tuningPage.analyzeRewriteButton);
      await expect(button).toBeVisible();
    });

    test('应该显示清空按钮', async () => {
      await tuningPage.switchToRewriteTab();
      const button = tuningPage.page.locator(tuningPage.clearRewriteButton);
      await expect(button).toBeVisible();
    });

    test('输入SQL后分析按钮应该可用', async () => {
      await tuningPage.switchToRewriteTab();
      await tuningPage.enterRewriteSQL('SELECT * FROM users');
      const button = tuningPage.page.locator(tuningPage.analyzeRewriteButton);
      await expect(button).toBeEnabled();
    });
  });

  test.describe('InnoDB调优功能', () => {
    test('应该显示InnoDB调优按钮', async () => {
      await tuningPage.switchToInnoDBTab();
      const button = tuningPage.page.locator(tuningPage.innodbButton);
      await expect(button).toBeVisible();
    });

    test('应该显示点击获取建议的提示', async () => {
      await tuningPage.switchToInnoDBTab();
      const empty = tuningPage.page.locator('.el-empty:has-text("点击上方按钮")');
      await expect(empty).toBeVisible();
    });
  });
});
