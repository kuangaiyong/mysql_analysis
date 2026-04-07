import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ReportDetailPage extends BasePage {
  readonly reportContent = '.report-content';
  readonly downloadButton = 'button:has-text("下载")';
  readonly backButton = 'button:has-text("返回")';

  async goto(): Promise<void> {
    await super.goto('/reports/1');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.reportContent);
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    return await title.textContent() || '';
  }

  async getContent(): Promise<string> {
    return await this.getText(this.reportContent);
  }

  async clickDownload(): Promise<void> {
    await this.click(this.downloadButton);
  }

  async clickBack(): Promise<void> {
    await this.click(this.backButton);
  }
}
