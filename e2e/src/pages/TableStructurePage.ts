import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class TableStructurePage extends BasePage {
  readonly tableList = '.table-list';
  readonly tableDetail = '.table-detail';
  readonly ddlText = 'pre.ddl-text';
  readonly foreignKeys = '.foreign-keys';
  readonly statistics = '.statistics';
  readonly backButton = 'button:has-text("返回")';

  async goto(): Promise<void> {
    await super.goto('/table-structure');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.tableList);
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    return await title.textContent() || '';
  }

  async selectTable(tableName: string): Promise<void> {
    const tableItem = this.page.locator(this.tableList).getByText(tableName);
    await tableItem.click();
  }

  async getDDLText(): Promise<string> {
    return await this.getText(this.ddlText);
  }

  async getForeignKeys(): Promise<string> {
    return await this.getText(this.foreignKeys);
  }

  async getStatistics(): Promise<string> {
    return await this.getText(this.statistics);
  }

  async clickBack(): Promise<void> {
    await this.click(this.backButton);
  }
}
