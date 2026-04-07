import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class SessionsPage extends BasePage {
  readonly connectionSelect = 'input[placeholder="请选择MySQL连接"]';
  readonly connectionSelector = '.el-select:has-text("选择连接")';
  readonly userInput = 'input[placeholder="请输入用户名"]';
  readonly databaseInput = 'input[placeholder="请输入数据库名"]';
  readonly stateSelect = '.el-form-item:has-text("状态") .el-select input';
  readonly commandSelect = '.el-form-item:has-text("命令") .el-select input';
  readonly searchButton = 'button:has-text("查询")';
  readonly resetButton = 'button:has-text("重置")';
  readonly batchKillButton = 'button:has-text("批量Kill")';
  readonly exportButton = 'button:has-text("导出CSV")';
  readonly refreshButton = 'button:has-text("刷新")';
  readonly tableRows = '.el-table__body-wrapper .el-table__row';
  readonly table = '.el-table';
  readonly loadingMask = '.el-loading-mask';
  readonly pagination = '.el-pagination';
  readonly confirmButton = '.el-message-box__btns button:has-text("确定")';
  readonly cancelButton = '.el-message-box__btns button:has-text("取消")';
  readonly messageBox = '.el-message-box';

  async goto(): Promise<void> {
    await super.goto('/sessions');
  }

  async isLoaded(): Promise<boolean> {
    const titleVisible = await this.isVisible('.page-title');
    const selectVisible = await this.isVisible(this.connectionSelect);
    return titleVisible && selectVisible;
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    await title.waitFor({ state: 'visible', timeout: 10000 });
    const titleText = await title.textContent();
    if (!titleText || titleText.trim() === '') {
      return '';
    }
    return titleText || '';
  }

  async selectConnection(connectionName: string): Promise<void> {
    await this.click(this.connectionSelect);
    await this.page.locator(`.el-select-dropdown__item:has-text("${connectionName}")`).click();
    await this.waitForLoad();
  }

  async fillUserFilter(user: string): Promise<void> {
    await this.fill(this.userInput, user);
  }

  async fillDatabaseFilter(database: string): Promise<void> {
    await this.fill(this.databaseInput, database);
  }

  async selectStateFilter(state: string): Promise<void> {
    await this.click(this.stateSelect);
    await this.page.locator(`.el-select-dropdown__item:has-text("${state}")`).click();
  }

  async selectCommandFilter(command: string): Promise<void> {
    await this.click(this.commandSelect);
    await this.page.locator(`.el-select-dropdown__item:has-text("${command}")`).click();
  }

  async clickSearchButton(): Promise<void> {
    await this.click(this.searchButton);
    await this.waitForLoad();
  }

  async clickResetButton(): Promise<void> {
    await this.click(this.resetButton);
    await this.waitForLoad();
  }

  async clickRefreshButton(): Promise<void> {
    await this.click(this.refreshButton);
    await this.waitForLoad();
  }

  async clickExportButton(): Promise<void> {
    await this.click(this.exportButton);
  }

  async isFilterFormVisible(): Promise<boolean> {
    return await this.isVisible(this.userInput);
  }

  async isTableVisible(): Promise<boolean> {
    return await this.isVisible(this.table);
  }

  async isPaginationVisible(): Promise<boolean> {
    return await this.isVisible(this.pagination);
  }

  async getTableRowCount(): Promise<number> {
    const rows = this.page.locator(this.tableRows);
    return await rows.count();
  }

  async selectTableRow(index: number): Promise<void> {
    const row = this.page.locator(this.tableRows).nth(index);
    await row.locator('.el-checkbox').click();
  }

  async clickKillButton(index: number): Promise<void> {
    const row = this.page.locator(this.tableRows).nth(index);
    await row.locator('button:has-text("Kill")').click();
  }

  async confirmKill(): Promise<void> {
    await this.click(this.confirmButton);
    await this.waitForLoad();
  }

  async cancelKill(): Promise<void> {
    await this.click(this.cancelButton);
  }

  async isConfirmDialogVisible(): Promise<boolean> {
    return await this.isVisible(this.messageBox);
  }

  async waitForLoadingComplete(): Promise<void> {
    await this.page.waitForSelector(this.loadingMask, { state: 'hidden', timeout: 10000 }).catch(() => {});
  }

  async getTableHeaders(): Promise<string[]> {
    const headers = this.page.locator('.el-table__header-wrapper th');
    const count = await headers.count();
    const texts: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await headers.nth(i).textContent();
      if (text) texts.push(text.trim());
    }
    return texts;
  }
}
