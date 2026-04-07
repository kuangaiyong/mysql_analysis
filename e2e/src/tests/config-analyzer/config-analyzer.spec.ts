import { test, expect } from '../../fixtures/base.fixture';
import { ConfigAnalyzerPage } from '../../pages/ConfigAnalyzerPage';

const mockConnections = [
  { id: 1, name: 'Test Connection', host: 'localhost', port: 3306 }
];

const mockAnalysis = {
  id: 1,
  health_score: 85,
  critical_count: 2,
  warning_count: 5,
  info_count: 8,
  mysql_version: '8.0.35',
  analysis_timestamp: '2026-02-17T10:30:00',
  violations: [
    {
      param: 'innodb_buffer_pool_size',
      severity: 'CRIT',
      current_value: '128M',
      recommended_value: '1G',
      source: 'best-practice',
      impact: 'Buffer pool too small for dataset',
      fix_sql: "SET GLOBAL innodb_buffer_pool_size = 1073741824;",
      fix_config: 'innodb_buffer_pool_size = 1G'
    },
    {
      param: 'max_connections',
      severity: 'WARN',
      current_value: '151',
      recommended_value: '500',
      source: 'workload',
      impact: 'May run out of connections under load',
      fix_sql: "SET GLOBAL max_connections = 500;",
      fix_config: 'max_connections = 500'
    },
    {
      param: 'slow_query_log',
      severity: 'INFO',
      current_value: 'OFF',
      recommended_value: 'ON',
      source: 'best-practice',
      impact: 'Slow queries are not being logged',
      fix_sql: "SET GLOBAL slow_query_log = 'ON';",
      fix_config: 'slow_query_log = ON'
    }
  ]
};

const mockHistory = {
  analyses: [
    {
      id: 1,
      health_score: 85,
      critical_count: 2,
      warning_count: 5,
      info_count: 8,
      analysis_timestamp: '2026-02-17T10:30:00'
    },
    {
      id: 2,
      health_score: 78,
      critical_count: 3,
      warning_count: 6,
      info_count: 10,
      analysis_timestamp: '2026-02-16T10:30:00'
    }
  ]
};

test.describe('Config Analyzer Page', () => {
  let configPage: ConfigAnalyzerPage;

  test.beforeEach(async ({ page }) => {
    configPage = new ConfigAnalyzerPage(page);
    await configPage.goto();
  });

  test.describe('页面加载', () => {
    test('应该正确加载配置分析页面', async ({ page }) => {
      await page.goto('/#/config-analyzer');
      await expect(page).toHaveURL(/.*config-analyzer/);
      await expect(page).toHaveTitle(/MySQL性能诊断与优化系统/);
    });

    test('应该显示页面标题', async () => {
      const title = await configPage.getTitle();
      expect(title).toBe('MySQL配置分析');
    });

    test('应该显示页面加载完成', async () => {
      const isLoaded = await configPage.isLoaded();
      expect(isLoaded).toBe(true);
    });
  });

  test.describe('连接选择器', () => {
    test('应该显示连接选择器', async () => {
      const connectionSelector = configPage.page.locator(configPage.connectionSelector);
      await expect(connectionSelector).toBeVisible();
    });
  });

  test.describe('操作按钮', () => {
    test('应该显示开始分析按钮', async () => {
      const analyzeButton = configPage.page.locator(configPage.analyzeButton);
      await expect(analyzeButton).toBeVisible();
    });

    test('应该显示导出报告按钮', async () => {
      const exportButton = configPage.page.locator(configPage.exportButton);
      await expect(exportButton).toBeVisible();
    });
  });

  test.describe('配置对比', () => {
    test('应该显示配置对比卡片', async () => {
      const isVisible = await configPage.isComparisonCardVisible();
      expect(isVisible).toBe(true);
    });

    test('应该默认显示时间对比模式', async () => {
      const timeRadio = configPage.page.locator(configPage.timeCompareRadio);
      await expect(timeRadio).toBeVisible();
    });

    test('应该显示实例对比模式切换', async () => {
      const instanceRadio = configPage.page.locator(configPage.instanceCompareRadio);
      await expect(instanceRadio).toBeVisible();
    });

    test('应该可以切换到实例对比模式', async () => {
      await configPage.switchToInstanceCompare();
      const instanceCompareButton = configPage.page.locator(configPage.instanceCompareButton);
      await expect(instanceCompareButton).toBeVisible();
    });
  });

  test.describe('历史记录', () => {
    test('应该显示历史记录卡片', async () => {
      const isVisible = await configPage.isHistoryCardVisible();
      expect(isVisible).toBe(true);
    });

    test('应该显示日期范围选择器', async () => {
      const datePicker = configPage.page.locator(configPage.dateRangePicker);
      await expect(datePicker).toBeVisible();
    });

    test('无数据时应该显示空状态', async () => {
      const empty = configPage.page.locator(configPage.historyEmpty);
      await expect(empty).toBeVisible();
    });
  });

  test.describe('分析结果展示（mock数据）', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/v1/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockConnections)
        });
      });

      await page.route('**/api/v1/config/*/history*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockHistory)
        });
      });
    });

    test('选择连接后应该加载历史记录', async () => {
      await configPage.selectConnection('Test Connection');
      await configPage.waitForLoadingComplete();

      const timeline = configPage.page.locator(configPage.historyTimeline);
      await expect(timeline).toBeVisible();
    });

    test('历史记录应该显示查看详情按钮', async () => {
      await configPage.selectConnection('Test Connection');
      await configPage.waitForLoadingComplete();

      const detailButton = configPage.page.locator(configPage.viewDetailButton).first();
      await expect(detailButton).toBeVisible();
    });
  });

  test.describe('分析结果卡片（mock完整分析）', () => {
    test.beforeEach(async ({ page }) => {
      await page.route('**/api/v1/connections', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockConnections)
        });
      });

      await page.route('**/api/v1/config/*/history*', async (route) => {
        const url = route.request().url();
        if (url.includes('limit=1')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ analyses: [mockAnalysis] })
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(mockHistory)
          });
        }
      });
    });

    test('应该显示健康分数', async () => {
      await configPage.selectConnection('Test Connection');
      await configPage.waitForLoadingComplete();

      const isVisible = await configPage.isHealthScoreVisible();
      expect(isVisible).toBe(true);

      const score = await configPage.getHealthScore();
      expect(score).toContain('85');
    });

    test('应该显示问题统计', async () => {
      await configPage.selectConnection('Test Connection');
      await configPage.waitForLoadingComplete();

      const isVisible = await configPage.isStatsCardVisible();
      expect(isVisible).toBe(true);

      const critical = await configPage.getCriticalCount();
      expect(critical).toContain('2');

      const warning = await configPage.getWarningCount();
      expect(warning).toContain('5');

      const info = await configPage.getInfoCount();
      expect(info).toContain('8');
    });

    test('应该显示MySQL版本', async () => {
      await configPage.selectConnection('Test Connection');
      await configPage.waitForLoadingComplete();

      const version = configPage.page.locator(configPage.versionValue);
      await expect(version).toBeVisible();
      await expect(version).toContainText('8.0.35');
    });

    test('应该显示配置违规列表', async () => {
      await configPage.selectConnection('Test Connection');
      await configPage.waitForLoadingComplete();

      const isVisible = await configPage.isViolationsCardVisible();
      expect(isVisible).toBe(true);

      const collapse = configPage.page.locator(configPage.violationCollapse);
      await expect(collapse).toBeVisible();
    });

    test('应该显示违规严重程度筛选器', async () => {
      await configPage.selectConnection('Test Connection');
      await configPage.waitForLoadingComplete();

      const filter = configPage.page.locator(configPage.violationFilter);
      await expect(filter).toBeVisible();
    });
  });
});
