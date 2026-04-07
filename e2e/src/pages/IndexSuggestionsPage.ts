import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class IndexSuggestionsPage extends BasePage {
  readonly table = '.el-table';
  readonly searchForm = '.search-form';
  readonly connectionSelect = '.el-select[placeholder="选择连接"]';
  readonly tableNameInput = 'input[placeholder="请输入表名"]';
  readonly statusSelect = '.el-select[placeholder="选择状态"]';
  readonly searchButton = 'button:has-text("查询")';
  readonly resetButton = 'button:has-text("重置")';
  readonly analyzeButton = 'button:has-text("分析查询")';
  readonly analyzeDialog = '.el-dialog:has-text("分析查询")';
  readonly sqlDialog = '.el-dialog:has-text("CREATE INDEX")';
  readonly pagination = '.el-pagination';

  async goto(): Promise<void> {
    await super.goto('/index-suggestions');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.table);
  }

  async selectConnection(connectionName: string): Promise<void> {
    await this.click(this.connectionSelect);
    await this.page.locator(`.el-select-dropdown__item:has-text("${connectionName}")`).click();
  }

  async searchByTableName(tableName: string): Promise<void> {
    await this.fill(this.tableNameInput, tableName);
    await this.click(this.searchButton);
    await this.waitForLoad();
  }

  async filterByStatus(status: string): Promise<void> {
    await this.click(this.statusSelect);
    await this.page.locator(`.el-select-dropdown__item:has-text("${status}")`).click();
  }

  async resetFilters(): Promise<void> {
    await this.click(this.resetButton);
    await this.waitForLoad();
  }

  async openAnalyzeDialog(): Promise<void> {
    await this.click(this.analyzeButton);
    await this.waitForElementVisible(this.analyzeDialog);
  }

  async viewSQL(rowIndex: number): Promise<void> {
    const row = this.page.locator(this.table).locator('tr').nth(rowIndex);
    await row.locator('button:has-text("查看SQL")').click();
    await this.waitForElementVisible(this.sqlDialog);
  }

  async acceptSuggestion(rowIndex: number): Promise<void> {
    const row = this.page.locator(this.table).locator('tr').nth(rowIndex);
    await row.locator('button:has-text("采纳")').click();
  }

  async rejectSuggestion(rowIndex: number, reason: string): Promise<void> {
    const row = this.page.locator(this.table).locator('tr').nth(rowIndex);
    await row.locator('button:has-text("拒绝")').click();
    await this.page.locator('.el-message-box__content input').fill(reason);
    await this.page.locator('.el-message-box__btns button:has-text("确定")').click();
  }

  async deleteSuggestion(rowIndex: number): Promise<void> {
    const row = this.page.locator(this.table).locator('tr').nth(rowIndex);
    await row.locator('button:has-text("删除")').click();
  }

  async getSuggestionCount(): Promise<number> {
    const rows = await this.page.locator(this.table).locator('tr').count();
    return rows > 0 ? rows - 1 : 0;
  }

  async closeDialog(): Promise<void> {
    await this.page.locator('.el-dialog__close').click();
  }
}
