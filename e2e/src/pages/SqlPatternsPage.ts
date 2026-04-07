import { type Page, type Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class SqlPatternsPage extends BasePage {
  readonly pageTitle = '.page-title';
  readonly sqlTextarea = 'textarea[placeholder*="输入要检测的SQL语句"]';
  readonly detectButton = 'button:has-text("检测反模式")';
  readonly clearButton = 'button:has-text("清空")';
  readonly resultsCard = '.el-card:has-text("检测结果")';
  readonly resultTag = '.el-tag:has-text("个问题")';
  readonly sqlHint = '.sql-hint';
  readonly successMessage = '.el-message--success';
  readonly warningMessage = '.el-message--warning';
  readonly errorMessage = '.el-message--error';

  async goto(): Promise<void> {
    await super.goto('/sql-patterns');
  }

  async isLoaded(): Promise<boolean> {
    const titleVisible = await this.isVisible(this.pageTitle);
    const textareaVisible = await this.isVisible(this.sqlTextarea);
    const detectButtonVisible = await this.isVisible(this.detectButton);
    return titleVisible && textareaVisible && detectButtonVisible;
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator(this.pageTitle);
    await title.waitFor({ state: 'visible', timeout: 10000 });
    return (await title.textContent()) || '';
  }

  async fillSql(sql: string): Promise<void> {
    await this.fill(this.sqlTextarea, sql);
  }

  async clickDetect(): Promise<void> {
    await this.click(this.detectButton);
    await this.page.waitForLoadState('networkidle');
  }

  async clickClear(): Promise<void> {
    await this.click(this.clearButton);
  }

  async getResultsCard(): Promise<Locator> {
    return this.page.locator(this.resultsCard);
  }

  async isResultsVisible(): Promise<boolean> {
    return this.isVisible(this.resultsCard);
  }

  async getProblemCount(): Promise<number> {
    const tagText = await this.getText(this.resultTag);
    const match = tagText.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  async getSqlHintText(): Promise<string> {
    return this.getText(this.sqlHint);
  }

  async isDetectButtonDisabled(): Promise<boolean> {
    const button = this.page.locator(this.detectButton);
    const isDisabled = await button.getAttribute('disabled');
    return isDisabled !== null;
  }

  async waitForLoadingComplete(): Promise<void> {
    await this.page.waitForSelector('.el-button:not([disabled])', { timeout: 10000 });
  }
}
