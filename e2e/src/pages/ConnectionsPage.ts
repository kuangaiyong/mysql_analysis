import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ConnectionsPage extends BasePage {
  readonly addButton = 'button:has-text("添加连接")';
  readonly searchButton = 'button:has-text("查询")';
  readonly resetButton = 'button:has-text("重置")';
  readonly tableRows = '.el-table__body-wrapper .el-table__row';
  readonly pagination = '.el-pagination';
  readonly dialog = '.el-dialog';
  readonly nameInput = 'input[placeholder*="连接名称"]';
  readonly hostInput = 'input[placeholder*="主机地址"]';
  readonly portInput = '.el-form-item:has-text("端口") .el-input-number input';
  readonly usernameInput = 'input[placeholder*="用户名"]';
  readonly passwordInput = 'input[type="password"]';
  readonly databaseInput = 'input[placeholder*="数据库名"]';
  readonly saveButton = '.el-dialog button:has-text("确定")';
  readonly cancelButton = '.el-dialog button:has-text("取消")';

  async goto(): Promise<void> {
    await super.goto('/connections');
  }

  async isLoaded(): Promise<boolean> {
    // 等待页面标题和添加按钮可见，表示页面已加载
    const titleVisible = await this.isVisible('.page-title');
    const buttonVisible = await this.isVisible(this.addButton);
    return titleVisible && buttonVisible;
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

  async clickAddButton(): Promise<void> {
    await this.click(this.addButton);
    await this.waitForElementVisible(this.dialog);
  }

  async fillConnectionForm(data: {
    name: string;
    host: string;
    port: string;
    username: string;
    password: string;
    database: string;
  }): Promise<void> {
    await this.fill(this.nameInput, data.name);
    await this.fill(this.hostInput, data.host);
    await this.page.locator(this.portInput).fill(data.port);
    await this.fill(this.usernameInput, data.username);
    await this.fill(this.passwordInput, data.password);
    await this.fill(this.databaseInput, data.database);
  }

  async saveConnection(): Promise<void> {
    await this.click(this.saveButton);
  }

  async cancel(): Promise<void> {
    await this.click(this.cancelButton);
  }

  async searchByName(name: string): Promise<void> {
    await this.fill(this.nameInput, name);
    await this.click(this.searchButton);
    await this.waitForLoad();
  }

  async searchByHost(host: string): Promise<void> {
    await this.fill(this.hostInput, host);
    await this.click(this.searchButton);
    await this.waitForLoad();
  }

  async resetSearch(): Promise<void> {
    await this.click(this.resetButton);
    await this.waitForLoad();
  }

  async verifyConnectionInList(name: string): Promise<void> {
    const row = this.page.locator(this.tableRows).getByRole('row', { name: name });
    await expect(row).toBeVisible();
  }

  async editConnection(name: string): Promise<void> {
    const row = this.page.locator(this.tableRows).getByRole('row', { name: name });
    await row.locator('button:has-text("编辑")').click();
    await this.waitForElementVisible(this.dialog);
  }

  async deleteConnection(name: string): Promise<void> {
    const row = this.page.locator(this.tableRows).getByRole('row', { name: name });
    await row.locator('button:has-text("删除")').click();
    await this.page.locator('.el-message-box__btns button:has-text("确认")').click();
  }
}
