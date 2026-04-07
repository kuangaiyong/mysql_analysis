import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  readonly pageTitle = '.page-title';
  readonly qpsValue = '.metric-card:has-text("QPS") .card-value';
  readonly tpsValue = '.metric-card:has-text("TPS") .card-value';
  readonly connectionsValue = '.metric-card:has-text("活跃连接") .card-value';
  readonly chartContainer = '.chart-container';
  readonly qpsChart = '.chart-card:has-text("QPS监控") .chart';
  readonly tpsChart = '.chart-card:has-text("TPS监控") .chart';
  readonly quickLinks = '.quick-links';

  async goto(): Promise<void> {
    await super.goto('/dashboard');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.pageTitle);
  }

  async getTitle(): Promise<string> {
    return await this.getText(this.pageTitle);
  }

  async getQPSValue(): Promise<string> {
    return await this.getText(this.qpsValue);
  }

  async getTPSValue(): Promise<string> {
    return await this.getText(this.tpsValue);
  }

  async getConnectionsCount(): Promise<string> {
    return await this.getText(this.connectionsValue);
  }

  async isChartVisible(): Promise<boolean> {
    return await this.isVisible(this.chartContainer);
  }

  async clickQuickLink(linkText: string): Promise<void> {
    await this.page.locator(this.quickLinks).getByText(linkText).click();
  }

  getQpsChart(): Locator {
    return this.page.locator(this.qpsChart);
  }

  getTpsChart(): Locator {
    return this.page.locator(this.tpsChart);
  }

  async getChartDataPoints(metricType: string): Promise<number[]> {
    // Simulate getting chart data points from __testPushMetrics
    const points = await this.page.evaluate((type) => {
      if ((window as any).__testChartDataPoints && (window as any).__testChartDataPoints[type]) {
        return (window as any).__testChartDataPoints[type];
      }
      return [];
    }, metricType);
    return points;
  }

  getQpsCard(): Locator {
    return this.page.locator('.metric-card', { has: this.page.getByText('QPS') });
  }

  getTpsCard(): Locator {
    return this.page.locator('.metric-card', { has: this.page.getByText('TPS') });
  }

  getConnectionCard(): Locator {
    return this.page.locator('.metric-card', { has: this.page.getByText('活跃连接') });
  }

  getBufferPoolCard(): Locator {
    return this.page.locator('.metric-card', { has: this.page.getByText('Buffer Pool命中率') });
  }

  getQpsTitle(): Locator {
    return this.page.locator('.metric-card:has-text("QPS") .card-title');
  }

  getTpsTitle(): Locator {
    return this.page.locator('.metric-card:has-text("TPS") .card-title');
  }

  getConnectionTitle(): Locator {
    return this.page.locator('.metric-card:has-text("活跃连接") .card-title');
  }

  getBufferPoolTitle(): Locator {
    return this.page.locator('.metric-card:has-text("Buffer Pool命中率") .card-title');
  }

  getQpsChartElement(): Locator {
    return this.page.locator(this.qpsChart);
  }

  getTpsChartElement(): Locator {
    return this.page.locator(this.tpsChart);
  }

  async getQpsChartTitle(): Promise<Locator> {
    return this.page.locator('.chart-card:has-text("QPS监控") .el-card__header');
  }

  async getTpsChartTitle(): Promise<Locator> {
    return this.page.locator('.chart-card:has-text("TPS监控") .el-card__header');
  }

  async getQpsValue(): Promise<string> {
    return await this.getText('.metric-card:has-text("QPS") .card-value');
  }

  async getTpsValue(): Promise<string> {
    return await this.getText('.metric-card:has-text("TPS") .card-value');
  }
}
