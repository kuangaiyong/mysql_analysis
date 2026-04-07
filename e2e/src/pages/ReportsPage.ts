import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ReportsPage extends BasePage {
  readonly reportsTable = '.reports-table';
  readonly tableRows = '.el-table__body-wrapper .el-table__row';
  readonly addButton = 'button:has-text("生成报告")';
  readonly filterForm = '.filter-form';
  readonly searchButton = 'button:has-text("查询")';
  readonly dialog = '.create-report-dialog';

  async goto(): Promise<void> {
    await super.goto('/reports');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.tableRows);
  }

  async viewReport(reportName: string): Promise<void> {
    const row = this.page.locator(this.tableRows).getByRole('row', { name: reportName });
    await row.locator('button:has-text("查看")').click();
  }

  async downloadReport(reportName: string): Promise<void> {
    const row = this.page.locator(this.tableRows).getByRole('row', { name: reportName });
    await row.locator('button:has-text("下载")').click();
  }

  async deleteReport(reportName: string): Promise<void> {
    const row = this.page.locator(this.tableRows).getByRole('row', { name: reportName });
    await row.locator('button:has-text("删除")').click();
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    return await title.textContent() || '';
  }

  async clickAddButton(): Promise<void> {
    await this.click(this.addButton);
  }

  async viewReport(reportName: string): Promise<void> {
    const row = this.page.locator(this.reportsTable).getByRole('row', { name: reportName });
    await row.locator('button:has-text("查看")').click();
  }

  async downloadReport(reportName: string): Promise<void> {
    const row = this.page.locator(this.reportsTable).getByRole('row', { name: reportName });
    await row.locator('button:has-text("下载")').click();
  }

  async deleteReport(reportName: string): Promise<void> {
    const row = this.page.locator(this.reportsTable).getByRole('row', { name: reportName });
    await row.locator('button:has-text("删除")').click();
  }

  async fillReportForm(data: {
    reportType: string;
    connection: string;
    dateRange: string;
  }): Promise<void> {
    const typeSelect = this.page.locator(this.dialog + ' .report-type-select');
    const connectionSelect = this.page.locator(this.dialog + ' .connection-select');
    const dateRangeSelect = this.page.locator(this.dialog + ' .date-range-select');

    await typeSelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + data.reportType + '")').click();
    await connectionSelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + data.connection + '")').click();
    await dateRangeSelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + data.dateRange + '")').click();
  }

  async selectReportType(type: string): Promise<void> {
    const typeSelect = this.page.locator(this.dialog + ' .report-type-select');
    await typeSelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + type + '")').click();
  }

  async selectConnection(connection: string): Promise<void> {
    const connectionSelect = this.page.locator(this.dialog + ' .connection-select');
    await connectionSelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + connection + '")').click();
  }

  async selectDateRange(range: string): Promise<void> {
    const dateRangeSelect = this.page.locator(this.dialog + ' .date-range-select');
    await dateRangeSelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + range + '")').click();
  }
}
