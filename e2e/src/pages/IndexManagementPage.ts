import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class IndexManagementPage extends BasePage {
  readonly table = '.el-table';
  readonly addButton = 'button:has-text("添加索引")';
  readonly analyzeButton = 'button:has-text("分析使用率")';
  readonly redundantButton = 'button:has-text("检测冗余")';
  readonly dialog = '.el-dialog';

  async goto(): Promise<void> {
    await super.goto('/index-management');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.table);
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    return await title.textContent() || '';
  }

  async clickAddButton(): Promise<void> {
    await this.click(this.addButton);
  }

  async analyzeUsage(): Promise<void> {
    await this.click(this.analyzeButton);
  }

  async detectRedundant(): Promise<void> {
    await this.click(this.redundantButton);
  }

  async deleteIndex(indexName: string): Promise<void> {
    const row = this.page.locator(this.table).getByRole('row', { name: indexName });
    await row.locator('button:has-text("删除")').click();
  }

  async fillIndexForm(data: { name: string; tableName: string; columns: string }): Promise<void> {
    const indexNameInput = this.page.locator(this.dialog + ' input[placeholder*="索引名称"]');
    const tableNameInput = this.page.locator(this.dialog + ' input[placeholder*="表名"]');
    const columnsInput = this.page.locator(this.dialog + ' input[placeholder*="列名"]');

    await indexNameInput.fill(data.name);
    await tableNameInput.fill(data.tableName);
    await columnsInput.fill(data.columns);
  }

  async saveIndex(): Promise<void> {
    const saveButton = this.page.locator(this.dialog + ' button:has-text("保存")');
    await saveButton.click();
  }

  async cancelIndex(): Promise<void> {
    const cancelButton = this.page.locator(this.dialog + ' button:has-text("取消")');
    await cancelButton.click();
  }
}
