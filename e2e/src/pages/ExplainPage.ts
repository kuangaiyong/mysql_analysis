import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ExplainPage extends BasePage {
  readonly sqlInput = 'textarea[placeholder*="输入SQL语句"]';
  readonly connectionSelect = '.el-form-item:has-text("连接") .el-select';
  readonly databaseInput = '.el-form-item:has-text("数据库") .el-input';
  readonly analyzeButton = 'button:has-text("分析")';
  readonly executeExplainButton = 'button:has-text("执行 EXPLAIN")';
  readonly executeExplainAnalyzeButton = 'button:has-text("执行 EXPLAIN ANALYZE")';
  readonly resultContainer = '.result-card';
  readonly treeView = '.result-view';
  readonly tableView = '.result-view';
  readonly jsonView = '.result-view .json-viewer';
  readonly viewToggleTree = 'button:has-text("树形视图")';
  readonly viewToggleTable = 'button:has-text("表格视图")';
  readonly viewToggleJSON = 'button:has-text("JSON格式")';
  readonly suggestionsTable = '.el-table';
  readonly suggestionsTitle = '.suggestions-title';

  async goto(): Promise<void> {
    await super.goto('/explain');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.sqlInput);
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    return await title.textContent() || '';
  }

  async inputSQL(sql: string): Promise<void> {
    await this.fill(this.sqlInput, sql);
  }

  async clickAnalyze(): Promise<void> {
    await this.click(this.analyzeButton);
    await this.waitForElementVisible(this.resultContainer);
  }

  async switchToTreeView(): Promise<void> {
    await this.click(this.viewToggleTree);
  }

  async switchToTableView(): Promise<void> {
    await this.click(this.viewToggleTable);
  }

  async switchToJSONView(): Promise<void> {
    await this.click(this.viewToggleJSON);
  }

  async getResultText(): Promise<string> {
    return await this.getText(this.resultContainer);
  }

  async isResultVisible(): Promise<boolean> {
    return await this.isVisible(this.resultContainer);
  }
}
