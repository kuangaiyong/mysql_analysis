import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class AlertHistoryPage extends BasePage {
  readonly historyTable = '.history-table';
  readonly filterForm = '.filter-form';
  readonly searchButton = 'button:has-text("查询")';
  readonly resetButton = 'button:has-text("重置")';
  readonly resolveButton = 'button:has-text("标记已解决")';
  readonly batchResolveButton = 'button:has-text("批量解决")';
  readonly backButton = 'button:has-text("返回")';

  async goto(): Promise<void> {
    await super.goto('/alerts/history');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.historyTable);
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    return await title.textContent() || '';
  }

  async searchByTimeRange(startTime: string, endTime: string): Promise<void> {
    const startTimeInput = 'input[placeholder*="开始时间"]';
    const endTimeInput = 'input[placeholder*="结束时间"]';
    await this.fill(startTimeInput, startTime);
    await this.fill(endTimeInput, endTime);
    await this.click(this.searchButton);
  }

  async resolveAlert(alertId: string): Promise<void> {
    const row = this.page.locator(this.historyTable).getByRole('row', { name: alertId });
    await row.locator('button:has-text("解决")').click();
  }

  async batchResolve(): Promise<void> {
    await this.click(this.batchResolveButton);
  }

  async clickBack(): Promise<void> {
    await this.click(this.backButton);
  }
}
