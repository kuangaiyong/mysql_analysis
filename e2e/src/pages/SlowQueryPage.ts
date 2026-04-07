import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class SlowQueryPage extends BasePage {
  readonly table = '.el-table';
  readonly searchButton = 'button:has-text("查询")';
  readonly resetButton = 'button:has-text("重置")';
  readonly analyzeButton = 'button:has-text("分析")';
  readonly optimizeButton = 'button:has-text("优化建议")';
  readonly batchResolveButton = 'button:has-text("批量解决")';
  readonly batchDeleteButton = 'button:has-text("批量删除")';
  readonly sqlText = 'pre.sql-text';
  readonly dialog = '.el-dialog';

  async goto(): Promise<void> {
    await super.goto('/slow-query');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.table);
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
    await this.waitForLoad();
  }

  async viewDetail(sqlText: string): Promise<void> {
    const row = this.page.locator(this.table).getByText(sqlText).locator('..');
    await row.locator('button:has-text("查看详情")').click();
  }

  async selectSlowQueries(count: number): Promise<void> {
    const checkboxes = this.page.locator('.el-table .el-checkbox__original');
    for (let i = 0; i < count; i++) {
      await checkboxes.nth(i).check();
    }
  }

  async batchResolve(): Promise<void> {
    await this.click(this.batchResolveButton);
  }

  async batchDelete(): Promise<void> {
    await this.click(this.batchDeleteButton);
  }

  async getSlowQueryCount(): Promise<number> {
    const text = await this.getText('.el-pagination__total');
    const match = text.match(/共\s*(\d+)/);
    return match ? parseInt(match[1]) : 0;
  }

  async openOptimizeSuggestion(): Promise<void> {
    const row = this.page.locator(this.table).locator('tr').first();
    const optimizeButton = row.locator('button:has-text("优化建议")');
    await optimizeButton.click();
  }

  async openDetailDialog(sqlText: string): Promise<void> {
    const row = this.page.locator(this.table).getByText(sqlText).locator('..');
    const detailButton = row.locator('button:has-text("查看详情")');
    await detailButton.click();
  }
}
