import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class SlowQueryDetailPage extends BasePage {
  readonly sqlText = 'pre.sql-text';
  readonly executionPlan = '.execution-plan';
  readonly optimizationSuggestions = '.optimization-suggestions';
  readonly backButton = 'button:has-text("返回")';
  readonly resolveButton = 'button:has-text("标记已解决")';

  async goto(): Promise<void> {
    await super.goto('/slow-query/detail/1');
  }

  async isLoaded(): Promise<boolean> {
    return await this.isVisible(this.sqlText);
  }

  async getSQLText(): Promise<string> {
    return await this.getText(this.sqlText);
  }

  async getExecutionPlan(): Promise<string> {
    return await this.getText(this.executionPlan);
  }

  async getOptimizationSuggestions(): Promise<string[]> {
    const suggestions = this.page.locator(this.optimizationSuggestions).locator('.suggestion-item');
    const texts = [];
    const count = await suggestions.count();
    for (let i = 0; i < count; i++) {
      texts.push(await suggestions.nth(i).textContent() || '');
    }
    return texts;
  }

  async clickResolve(): Promise<void> {
    await this.click(this.resolveButton);
  }

  async clickBack(): Promise<void> {
    await this.click(this.backButton);
  }
}
