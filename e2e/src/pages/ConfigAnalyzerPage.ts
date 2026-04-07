import { Page, type Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class ConfigAnalyzerPage extends BasePage {
  // Page title
  readonly pageTitle = '.page-title';

  // Connection selector
  readonly connectionSelector = '.page-header .el-select';

  // Action buttons
  readonly analyzeButton = 'button:has-text("开始分析")';
  readonly exportButton = 'button:has-text("导出报告")';

  // Health score card
  readonly healthScoreCard = '.health-score-card';
  readonly scoreValue = '.score-value';
  readonly scoreLabel = '.score-label';

  // Stats card
  readonly statsCard = '.stats-card';
  readonly criticalCount = '.stat-item.crit .stat-value';
  readonly warningCount = '.stat-item.warn .stat-value';
  readonly infoCount = '.stat-item.info .stat-value';

  // Version card
  readonly versionCard = '.version-card';
  readonly versionValue = '.version-value';

  // Violations card
  readonly violationsCard = '.violations-card';
  readonly violationFilter = '.violations-header .el-select';
  readonly violationCollapse = '.violations-card .el-collapse';

  // Comparison card
  readonly comparisonCard = '.comparison-card';
  readonly timeCompareRadio = '.el-radio-button:has-text("时间对比")';
  readonly instanceCompareRadio = '.el-radio-button:has-text("实例对比")';
  readonly compareButton = 'button:has-text("对比")';
  readonly instanceCompareButton = 'button:has-text("实例对比")';
  readonly comparisonTable = '.comparison-card .el-table';

  // History card
  readonly historyCard = '.history-card';
  readonly historyTimeline = '.el-timeline';
  readonly historyEmpty = '.el-empty:has-text("暂无历史记录")';
  readonly dateRangePicker = '.history-header .el-date-editor';
  readonly viewDetailButton = 'button:has-text("查看详情")';

  async goto(): Promise<void> {
    await super.goto('/config-analyzer');
  }

  async isLoaded(): Promise<boolean> {
    const titleVisible = await this.isVisible(this.pageTitle);
    const comparisonVisible = await this.isVisible(this.comparisonCard);
    return titleVisible && comparisonVisible;
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator(this.pageTitle);
    await title.waitFor({ state: 'visible', timeout: 10000 });
    return (await title.textContent()) || '';
  }

  async selectConnection(connectionName: string): Promise<void> {
    await this.click(this.connectionSelector);
    await this.page.locator(`.el-select-dropdown__item:has-text("${connectionName}")`).click();
  }

  async clickAnalyze(): Promise<void> {
    await this.click(this.analyzeButton);
    await this.page.waitForTimeout(1000);
  }

  async clickExport(): Promise<void> {
    await this.click(this.exportButton);
  }

  async getHealthScore(): Promise<string> {
    return await this.getText(this.scoreValue);
  }

  async getCriticalCount(): Promise<string> {
    return await this.getText(this.criticalCount);
  }

  async getWarningCount(): Promise<string> {
    return await this.getText(this.warningCount);
  }

  async getInfoCount(): Promise<string> {
    return await this.getText(this.infoCount);
  }

  async switchToTimeCompare(): Promise<void> {
    await this.click(this.timeCompareRadio);
    await this.page.waitForTimeout(300);
  }

  async switchToInstanceCompare(): Promise<void> {
    await this.click(this.instanceCompareRadio);
    await this.page.waitForTimeout(300);
  }

  async selectViolationFilter(label: string): Promise<void> {
    await this.click(this.violationFilter);
    await this.page.locator(`.el-select-dropdown__item:has-text("${label}")`).click();
  }

  async waitForLoadingComplete(): Promise<void> {
    await this.page.waitForTimeout(1000);
    await this.page.waitForLoadState('networkidle');
  }

  async isHealthScoreVisible(): Promise<boolean> {
    return await this.isVisible(this.healthScoreCard);
  }

  async isStatsCardVisible(): Promise<boolean> {
    return await this.isVisible(this.statsCard);
  }

  async isViolationsCardVisible(): Promise<boolean> {
    return await this.isVisible(this.violationsCard);
  }

  async isComparisonCardVisible(): Promise<boolean> {
    return await this.isVisible(this.comparisonCard);
  }

  async isHistoryCardVisible(): Promise<boolean> {
    return await this.isVisible(this.historyCard);
  }
}
