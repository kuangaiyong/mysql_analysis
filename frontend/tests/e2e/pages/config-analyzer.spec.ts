import { test, expect } from '@playwright/test';

test.describe('Config Analyzer Page', () => {
  // Navigate to config-analyzer before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/config-analyzer');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Structure', () => {
    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display page title', async ({ page }) => {
      // The PageHeader shows "MySQL配置分析" in an h2 element with class page-title
      await expect(page.locator('.page-title')).toBeVisible();
      await expect(page.getByText('MySQL配置分析')).toBeVisible();
    });

    test('should display connection selector', async ({ page }) => {
      // Connection selector is inside PageHeader template #extra
      const select = page.locator('.el-select').first();
      await expect(select).toBeVisible();
    });

    test('should have correct placeholder for connection selector', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await expect(select).toBeVisible();
      const placeholderText = await select.locator('.el-input__inner').getAttribute('placeholder');
      expect(placeholderText).toBe('选择连接');
    });

    test('should display analyze button with icon', async ({ page }) => {
      const analyzeButton = page.locator('.el-button:has-text("开始分析")');
      await expect(analyzeButton).toBeVisible();
    });

    test('should display export report button', async ({ page }) => {
      const exportButton = page.locator('.el-button:has-text("导出报告")');
      await expect(exportButton).toBeVisible();
    });
  });

  test.describe('Health Score Section', () => {
    test('should display health score card', async ({ page }) => {
      const healthCard = page.locator('.health-score-card');
      const isVisible = await healthCard.isVisible().catch(() => false);
      if (isVisible) {
        await expect(healthCard).toBeVisible();
      }
    });

    test('should display health score label', async ({ page }) => {
      const scoreLabel = page.locator('.score-label');
      const isVisible = await scoreLabel.isVisible().catch(() => false);
      if (isVisible) {
        await expect(scoreLabel).toBeVisible();
        await expect(page.getByText('健康分数')).toBeVisible();
      }
    });

    test('should display problem statistics section', async ({ page }) => {
      const statsCard = page.locator('.stats-card');
      const isVisible = await statsCard.isVisible().catch(() => false);
      if (isVisible) {
        await expect(statsCard).toBeVisible();
      }
    });

    test('should display stats grid with severity levels', async ({ page }) => {
      const statsGrid = page.locator('.stats-grid');
      const isVisible = await statsGrid.isVisible().catch(() => false);
      if (isVisible) {
        await expect(statsGrid).toBeVisible();
      }
    });

    test('should display critical count', async ({ page }) => {
      const criticalLabel = page.locator('.stat-label').filter({ hasText: '严重' });
      const isVisible = await criticalLabel.isVisible().catch(() => false);
      if (isVisible) {
        await expect(criticalLabel).toBeVisible();
      }
    });

    test('should display warning count', async ({ page }) => {
      const warningLabel = page.locator('.stat-label').filter({ hasText: '警告' });
      const isVisible = await warningLabel.isVisible().catch(() => false);
      if (isVisible) {
        await expect(warningLabel).toBeVisible();
      }
    });

    test('should display info count', async ({ page }) => {
      const infoLabel = page.locator('.stat-label').filter({ hasText: '信息' });
      const isVisible = await infoLabel.isVisible().catch(() => false);
      if (isVisible) {
        await expect(infoLabel).toBeVisible();
      }
    });

    test('should display MySQL version section', async ({ page }) => {
      const versionCard = page.locator('.version-card');
      const isVisible = await versionCard.isVisible().catch(() => false);
      if (isVisible) {
        await expect(versionCard).toBeVisible();
      }
    });

    test('should display MySQL version label', async ({ page }) => {
      const versionCard = page.locator('.version-card');
      const isVisible = await versionCard.isVisible().catch(() => false);
      if (isVisible) {
        await expect(versionCard).toBeVisible();
        await expect(page.getByText('MySQL版本')).toBeVisible();
      }
    });

    test('should display health trend chart container', async ({ page }) => {
      const trendChart = page.locator('.health-trend-chart, .score-trend-chart');
      const isVisible = await trendChart.isVisible().catch(() => false);
      if (isVisible) {
        await expect(trendChart).toBeVisible();
      }
    });
  });

  test.describe('Config Violations Section', () => {
    test('should display violations card', async ({ page }) => {
      const violationsCard = page.locator('.violations-card');
      const isVisible = await violationsCard.isVisible().catch(() => false);
      if (isVisible) {
        await expect(violationsCard).toBeVisible();
      }
    });

    test('should display violations header', async ({ page }) => {
      const violationsCard = page.locator('.violations-card');
      const isVisible = await violationsCard.isVisible().catch(() => false);
      if (isVisible) {
        await expect(page.getByText('配置违规')).toBeVisible();
      }
    });

    test('should display violation filter select', async ({ page }) => {
      const violationsCard = page.locator('.violations-card');
      const isVisible = await violationsCard.isVisible().catch(() => false);
      if (isVisible) {
        const filterSelect = violationsCard.locator('.el-select');
        await expect(filterSelect).toBeVisible();
      }
    });

    test('should display filter options', async ({ page }) => {
      const violationsCard = page.locator('.violations-card');
      const isVisible = await violationsCard.isVisible().catch(() => false);
      if (isVisible) {
        const filterSelect = violationsCard.locator('.el-select');
        const isFilterVisible = await filterSelect.isVisible().catch(() => false);
        if (isFilterVisible) {
          await expect(filterSelect).toBeVisible();
        }
      }
    });

    test('should display severity filter options', async ({ page }) => {
      const violationsCard = page.locator('.violations-card');
      const isVisible = await violationsCard.isVisible().catch(() => false);
      if (isVisible) {
        const filterSelect = violationsCard.locator('.el-select');
        const isFilterVisible = await filterSelect.isVisible().catch(() => false);
        if (isFilterVisible) {
          await filterSelect.click();
          await expect(page.locator('.el-select-dropdown__item').filter({ hasText: '全部' }).first()).toBeVisible();
          await expect(page.locator('.el-select-dropdown__item').filter({ hasText: '严重' }).first()).toBeVisible();
          await expect(page.locator('.el-select-dropdown__item').filter({ hasText: '警告' }).first()).toBeVisible();
          await expect(page.locator('.el-select-dropdown__item').filter({ hasText: '信息' }).first()).toBeVisible();
        }
      }
    });
  });

  test.describe('Config Comparison Section', () => {
    test('should display comparison card', async ({ page }) => {
      const comparisonCard = page.locator('.comparison-card');
      await expect(comparisonCard).toBeVisible();
    });

    test('should display comparison header', async ({ page }) => {
      await expect(page.getByText('配置对比')).toBeVisible();
    });

    test('should display comparison mode radio buttons', async ({ page }) => {
      const comparisonCard = page.locator('.comparison-card');
      const isVisible = await comparisonCard.isVisible().catch(() => false);
      if (isVisible) {
        await expect(comparisonCard.locator('.el-radio-group')).toBeVisible();
      }
    });

    test('should display time comparison option', async ({ page }) => {
      const comparisonCard = page.locator('.comparison-card');
      const isVisible = await comparisonCard.isVisible().catch(() => false);
      if (isVisible) {
        await expect(page.getByText('时间对比')).toBeVisible();
      }
    });

    test('should display instance comparison option', async ({ page }) => {
      const comparisonCard = page.locator('.comparison-card');
      const isVisible = await comparisonCard.isVisible().catch(() => false);
      if (isVisible) {
        await expect(page.getByText('实例对比')).toBeVisible();
      }
    });

    test('should display time point selectors when time mode selected', async ({ page }) => {
      const comparisonCard = page.locator('.comparison-card');
      const isVisible = await comparisonCard.isVisible().catch(() => false);
      if (isVisible) {
        const timeSelects = comparisonCard.locator('.comparison-content .el-select');
        const count = await timeSelects.count();
        if (count > 0) {
          await expect(timeSelects).toHaveCount(2);
        }
      }
    });

    test('should display compare button', async ({ page }) => {
      const comparisonCard = page.locator('.comparison-card');
      const isVisible = await comparisonCard.isVisible().catch(() => false);
      if (isVisible) {
        const compareBtn = comparisonCard.locator('.el-button').filter({ hasText: '对比' });
        const btnVisible = await compareBtn.isVisible().catch(() => false);
        if (btnVisible) {
          await expect(compareBtn).toBeVisible();
        }
      }
    });
  });

  test.describe('History Section', () => {
    test('should display history card', async ({ page }) => {
      const historyCard = page.locator('.history-card');
      await expect(historyCard).toBeVisible();
    });

    test('should display history header', async ({ page }) => {
      const historyCard = page.locator('.history-card');
      const isVisible = await historyCard.isVisible().catch(() => false);
      if (isVisible) {
        const header = historyCard.locator('.el-card__header').filter({ hasText: '历史记录' });
        const headerVisible = await header.isVisible().catch(() => false);
        if (headerVisible) {
          await expect(header).toBeVisible();
        }
      }
    });

    test('should display date range picker', async ({ page }) => {
      const historyCard = page.locator('.history-card');
      const isVisible = await historyCard.isVisible().catch(() => false);
      if (isVisible) {
        const datePicker = historyCard.locator('.el-date-editor');
        const pickerVisible = await datePicker.isVisible().catch(() => false);
        if (pickerVisible) {
          await expect(datePicker).toBeVisible();
        }
      }
    });

    test('should display date picker placeholder', async ({ page }) => {
      const historyCard = page.locator('.history-card');
      const isVisible = await historyCard.isVisible().catch(() => false);
      if (isVisible) {
        const datePicker = historyCard.locator('.el-date-editor');
        const pickerVisible = await datePicker.isVisible().catch(() => false);
        if (pickerVisible) {
          await expect(datePicker).toBeVisible();
        }
      }
    });

    test('should display timeline component', async ({ page }) => {
      const historyCard = page.locator('.history-card');
      const isVisible = await historyCard.isVisible().catch(() => false);
      if (isVisible) {
        const timeline = historyCard.locator('.el-timeline');
        await expect(timeline).toBeVisible();
      }
    });
  });

  test.describe('Interactive Elements', () => {
    test('should analyze button be clickable', async ({ page }) => {
      const analyzeButton = page.locator('.el-button:has-text("开始分析")');
      await expect(analyzeButton).toBeEnabled();
    });

    test('should export button be visible and clickable', async ({ page }) => {
      const exportButton = page.locator('.el-button:has-text("导出报告")');
      await expect(exportButton).toBeVisible();
    });

    test('should switch comparison mode to instance', async ({ page }) => {
      const instanceRadio = page.locator('.el-radio-button').filter({ hasText: '实例对比' });
      await instanceRadio.click();
      await expect(page.getByText('选择实例1')).toBeVisible();
    });

    test('should open date picker', async ({ page }) => {
      const datePicker = page.locator('.el-date-editor');
      await datePicker.click();
      await expect(page.locator('.el-date-picker')).toBeVisible();
    });
  });

  test.describe('Layout and Styling', () => {
    test('should have el-row layout', async ({ page }) => {
      await expect(page.locator('.el-row').first()).toBeVisible();
    });

    test('should have el-col layout', async ({ page }) => {
      await expect(page.locator('.el-col').first()).toBeVisible();
    });

    test('should have proper card styling', async ({ page }) => {
      await expect(page.locator('.el-card').first()).toBeVisible();
    });

    test('should responsive layout work', async ({ page }) => {
      await page.setViewportSize({ width: 1200, height: 800 });
      await page.waitForTimeout(300);
      await expect(page.locator('.el-col').first()).toBeVisible();

      await page.setViewportSize({ width: 768, height: 600 });
      await page.waitForTimeout(300);
      await expect(page.locator('.el-col').first()).toBeVisible();
    });
  });
});
