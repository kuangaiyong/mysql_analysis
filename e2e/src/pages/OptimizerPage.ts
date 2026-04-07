import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class OptimizerPage extends BasePage {
  readonly sqlInput = 'textarea[placeholder*="输入要分析的SQL语句"]';
  readonly connectionSelect = '.el-form-item:has-text("连接") .el-select';
  readonly analyzeButton = 'button:has-text("分析优化器")';
  readonly clearButton = 'button:has-text("清空")';
  readonly resultCard = '.el-card:has-text("追踪结果")';
  readonly sqlHint = '.sql-hint';
  readonly traceViewer = '.trace-viewer';

  async goto(): Promise<void> {
    await super.goto('/optimizer');
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
    await this.waitForElementVisible(this.resultCard);
  }

  async clickClear(): Promise<void> {
    await this.click(this.clearButton);
  }

  async isResultVisible(): Promise<boolean> {
    return await this.isVisible(this.resultCard);
  }

  async getResultText(): Promise<string> {
    return await this.getText(this.resultCard);
  }
}
