import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class QueryTrendsPage extends BasePage {
  readonly searchForm = '.search-form';
  readonly connectionSelect = 'input[placeholder="选择连接"]';
  readonly timeRangeSelect = '.el-select:has-text("时间范围")';
  readonly tableNameInput = 'input[placeholder="请输入表名"]';
  readonly searchButton = 'button:has-text("查询")';
  readonly resetButton = 'button:has-text("重置")';
  readonly generateButton = 'button:has-text("生成指纹")';
  readonly exportButton = 'button:has-text("导出CSV")';
  readonly table = '.el-table';
  readonly tabs = '.el-tabs__item';
  readonly chartTab = 'text=趋势图表';
  readonly tableTab = 'text=数据列表';
  readonly pagination = '.el-pagination';
  readonly pageHeader = '.page-title';

  async goto(): Promise<void> {
    await super.goto('/query-trends');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.table);
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    return await title.textContent() || '';
  }

  async selectConnection(connectionName: string): Promise<void> {
    await this.page.locator('.el-select').first().click();
    await this.page.locator(`.el-select-dropdown__item:has-text("${connectionName}")`).click();
  }

  async selectTimeRange(timeRange: string): Promise<void> {
    await this.page.locator('.el-select').nth(1).click();
    await this.page.locator(`.el-select-dropdown__item:has-text("${timeRange}")`).click();
  }

  async searchByTableName(tableName: string): Promise<void> {
    await this.fill(this.tableNameInput, tableName);
    await this.click(this.searchButton);
    await this.waitForLoad();
  }

  async resetFilters(): Promise<void> {
    await this.click(this.resetButton);
    await this.waitForLoad();
  }

  async switchToChartTab(): Promise<void> {
    await this.click(this.chartTab);
  }

  async switchToTableTab(): Promise<void> {
    await this.click(this.tableTab);
  }

  async getTableRowCount(): Promise<number> {
    const table = this.page.locator(this.table);
    return await table.locator('tr').count();
  }

  async clickPagination(pageNumber: number): Promise<void> {
    const pageButton = this.page.locator(`.el-pagination button.number`).nth(pageNumber - 1);
    await pageButton.click();
    await this.waitForLoad();
  }

  async isPaginationVisible(): Promise<boolean> {
    return await this.isVisible(this.pagination);
  }

  async getPaginationTotal(): Promise<number> {
    const totalText = await this.getText('.el-pagination__total');
    const match = totalText.match(/共\s*(\d+)/);
    return match ? parseInt(match[1]) : 0;
  }
}
