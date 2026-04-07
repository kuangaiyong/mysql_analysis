import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class AlertsPage extends BasePage {
  readonly rulesTable = '.el-table';
  readonly tableRows = '.el-table__body-wrapper .el-table__row';
  readonly addButton = 'button:has-text("创建规则")';
  readonly historyButton = 'button:has-text("告警历史")';
  readonly dialog = '.el-dialog';

  async goto(): Promise<void> {
    await super.goto('/alerts');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.rulesTable);
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    return await title.textContent() || '';
  }

  async clickAddButton(): Promise<void> {
    await this.click(this.addButton);
  }

  async goToHistory(): Promise<void> {
    await this.click(this.historyButton);
  }

  async toggleRule(ruleName: string): Promise<void> {
    const row = this.page.locator(this.tableRows).getByRole('row', { name: ruleName });
    await row.locator('.el-switch').click();
  }

  async editRule(ruleName: string): Promise<void> {
    const row = this.page.locator(this.tableRows).getByRole('row', { name: ruleName });
    await row.locator('button:has-text("编辑")').click();
  }

  async deleteRule(ruleName: string): Promise<void> {
    const row = this.page.locator(this.tableRows).getByRole('row', { name: ruleName });
    await row.locator('button:has-text("删除")').click();
  }

  async fillAlertForm(data: {
    name: string;
    connection: string;
    type: string;
    condition: string;
    threshold: string;
    severity: string;
    channel: string;
  }): Promise<void> {
    const nameInput = this.page.locator(this.dialog + ' input[placeholder*="规则名称"]');
    const connectionSelect = this.page.locator(this.dialog + ' .connection-select');
    const typeSelect = this.page.locator(this.dialog + ' .alert-type-select');
    const conditionSelect = this.page.locator(this.dialog + ' .condition-select');
    const thresholdInput = this.page.locator(this.dialog + ' input[placeholder*="阈值"]');
    const severitySelect = this.page.locator(this.dialog + ' .severity-select');
    const channelSelect = this.page.locator(this.dialog + ' .channel-select');

    await nameInput.fill(data.name);
    await connectionSelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + data.connection + '")').click();
    await typeSelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + data.type + '")').click();
    await conditionSelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + data.condition + '")').click();
    await thresholdInput.fill(data.threshold);
    await severitySelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + data.severity + '")').click();
    await channelSelect.click();
    await this.page.locator(this.dialog + ' .el-select-dropdown__item:has-text("' + data.channel + '")').click();
  }

  async saveAlert(): Promise<void> {
    const saveButton = this.page.locator(this.dialog + ' button:has-text("保存")');
    await saveButton.click();
  }

  async cancelAlert(): Promise<void> {
    const cancelButton = this.page.locator(this.dialog + ' button:has-text("取消")');
    await cancelButton.click();
  }

  async clickCreateButton(): Promise<void> {
    await this.click(this.addButton);
    await this.page.waitForSelector('.el-dialog:visible', { timeout: 10000 });
  }
}
