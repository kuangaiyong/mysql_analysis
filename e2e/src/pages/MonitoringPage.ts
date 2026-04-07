import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class MonitoringPage extends BasePage {
  readonly connectionSelect = '.page-header .el-select';
  readonly startButton = 'button:has-text("启动采集")';
  readonly stopButton = 'button:has-text("停止采集")';
  readonly wsStatus = '.ws-status';
  readonly pageTitle = '.page-title';
  readonly chartContainer = '[data-testid="chart-container"]';
  readonly qpsChart = '[data-testid="qps-chart"]';
  readonly tpsChart = '[data-testid="tps-chart"]';
  readonly connectionsValue = '[data-testid="connections-value"]';
  readonly qpsValue = '[data-testid="qps-value"]';
  readonly tpsValue = '[data-testid="tps-value"]';
  readonly refreshButton = 'button:has-text("刷新")';

  async goto(): Promise<void> {
    await super.goto('/monitoring');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.connectionSelect);
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    return await title.textContent() || '';
  }

  async selectConnection(connectionName: string): Promise<void> {
    await this.click(this.connectionSelect);
    await this.page.locator(`.el-select-dropdown__item:has-text("${connectionName}")`).click();
  }

  async startMonitoring(): Promise<void> {
    await this.click(this.startButton);
    await expect(this.page.getByRole('button', { name: '停止采集' })).toBeEnabled();
  }

  async stopMonitoring(): Promise<void> {
    await this.click(this.stopButton);
    await expect(this.page.getByRole('button', { name: '启动采集' })).toBeEnabled();
  }

  async refreshMetrics(): Promise<void> {
    await this.click(this.refreshButton);
    await this.waitForLoad();
  }

  async getQPSValue(): Promise<string> {
    return await this.getText('[data-testid="qps-value"]');
  }

  async getTPSValue(): Promise<string> {
    return await this.getText('[data-testid="tps-value"]');
  }

  async getConnectionsValue(): Promise<string> {
    return await this.getText('[data-testid="connections-value"]');
  }
}
