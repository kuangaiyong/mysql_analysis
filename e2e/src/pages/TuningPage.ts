import { Page, expect, type Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class TuningPage extends BasePage {
  // Page title
  readonly pageTitle = '.page-title';
  
  // Connection selector
  readonly connectionSelector = '.page-header .el-select';
  
  // Tabs
  readonly tabs = '.el-tabs__nav';
  readonly indexTab = '.el-tabs__item:has-text("索引建议")';
  readonly rewriteTab = '.el-tabs__item:has-text("SQL改写")';
  readonly innodbTab = '.el-tabs__item:has-text("InnoDB调优")';
  
  // Index suggestions tab
  readonly sqlInputIndex = 'textarea[placeholder*="需要分析索引"]';
  readonly analyzeIndexButton = 'button:has-text("分析索引建议")';
  readonly clearIndexButton = 'button:has-text("清空")';
  readonly indexResultSection = '.suggestions-list';
  readonly indexEmpty = '.el-empty:has-text("暂无索引建议")';
  
  // SQL rewrite tab
  readonly sqlInputRewrite = 'textarea[placeholder*="需要优化"]';
  readonly analyzeRewriteButton = 'button:has-text("分析改写建议")';
  readonly clearRewriteButton = 'button:has-text("清空")';
  readonly rewriteResultSection = '.suggestions-list';
  readonly rewriteEmpty = '.el-empty:has-text("暂无改写建议")';
  
  // InnoDB tuning tab
  readonly innodbButton = 'button:has-text("获取InnoDB调优建议")';
  readonly innodbResultSection = '.suggestions-list';
  readonly innodbEmpty = '.el-empty:has-text("暂无InnoDB调优建议")';
  readonly bufferPoolTag = '.el-tag:has-text("Buffer Pool命中率")';
  
  // Result cards
  readonly suggestionCard = '.suggestion-card';
  readonly copyButton = 'button:has-text("复制语句"), button:has-text("复制SQL")';
  
  // Tags for recommendations count
  readonly recommendationCountTag = '.el-tag:has-text("条建议")';

  async goto(): Promise<void> {
    await super.goto('/tuning');
  }

  async isLoaded(): Promise<boolean> {
    const titleVisible = await this.isVisible(this.pageTitle);
    const tabsVisible = await this.isVisible(this.tabs);
    return titleVisible && tabsVisible;
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator(this.pageTitle);
    await title.waitFor({ state: 'visible', timeout: 10000 });
    return (await title.textContent()) || '';
  }

  async selectConnection(connectionName: string): Promise<void> {
    await this.click(this.connectionSelector);
    await this.page.locator(`.el-select-dropdown__item:has-text("${connectionName}")`).click();
  }

  async switchToIndexTab(): Promise<void> {
    await this.click(this.indexTab);
    await this.page.waitForTimeout(500);
  }

  async switchToRewriteTab(): Promise<void> {
    await this.click(this.rewriteTab);
    await this.page.waitForTimeout(500);
  }

  async switchToInnoDBTab(): Promise<void> {
    await this.click(this.innodbTab);
    await this.page.waitForTimeout(500);
  }

  async enterIndexSQL(sql: string): Promise<void> {
    await this.fill(this.sqlInputIndex, sql);
  }

  async clickAnalyzeIndex(): Promise<void> {
    await this.click(this.analyzeIndexButton);
    await this.page.waitForTimeout(1000);
  }

  async clickClearIndex(): Promise<void> {
    await this.click(this.clearIndexButton);
  }

  async enterRewriteSQL(sql: string): Promise<void> {
    await this.fill(this.sqlInputRewrite, sql);
  }

  async clickAnalyzeRewrite(): Promise<void> {
    await this.click(this.analyzeRewriteButton);
    await this.page.waitForTimeout(1000);
  }

  async clickClearRewrite(): Promise<void> {
    await this.click(this.clearRewriteButton);
  }

  async clickGetInnoDBTuning(): Promise<void> {
    await this.click(this.innodbButton);
    await this.page.waitForTimeout(1000);
  }

  async getIndexResultsCount(): Promise<number> {
    const tag = this.page.locator(this.recommendationCountTag).first();
    const text = await tag.textContent();
    const match = text?.match(/(\d+)\s+条建议/);
    return match ? parseInt(match[1], 10) : 0;
  }

  async getRewriteResultsCount(): Promise<number> {
    const tag = this.page.locator(this.recommendationCountTag).first();
    const text = await tag.textContent();
    const match = text?.match(/(\d+)\s+条建议/);
    return match ? parseInt(match[1], 10) : 0;
  }

  async getInnoDBResultsCount(): Promise<number> {
    const tags = await this.page.locator(this.recommendationCountTag).all();
    if (tags.length < 2) return 0;
    const tag = tags[1];
    const text = await tag.textContent();
    const match = text?.match(/(\d+)\s+条建议/);
    return match ? parseInt(match[1], 10) : 0;
  }

  async hasIndexResults(): Promise<boolean> {
    return await this.isVisible(this.indexResultSection);
  }

  async hasRewriteResults(): Promise<boolean> {
    return await this.isVisible(this.rewriteResultSection);
  }

  async hasInnoDBResults(): Promise<boolean> {
    return await this.isVisible(this.innodbResultSection);
  }

  async getSuggestionCards(): Promise<Locator[]> {
    return await this.page.locator(this.suggestionCard).all();
  }
}
