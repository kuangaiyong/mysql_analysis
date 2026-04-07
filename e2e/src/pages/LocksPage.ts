import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class LocksPage extends BasePage {
  readonly connectionSelect = 'input[placeholder="请选择MySQL连接"]';
  readonly pageTitle = '锁分析';
  readonly emptyState = '.el-empty';
  readonly lockWaitsTab = '.el-tabs__item:has-text("当前锁等待")';
  readonly deadlocksTab = '.el-tabs__item:has-text("死锁历史")';
  readonly lockGraphTab = '.el-tabs__item:has-text("锁等待图")';
  readonly refreshButton = 'button:has-text("刷新")';
  readonly table = '.el-table';
  readonly loadingMask = '.el-loading-mask';
  
  readonly timeRangeSelect = '.el-select:has-text("时间范围") input';
  readonly historyHoursOption = (hours: number) => `.el-select-dropdown__item:has-text("${hours}小时")`;
  
  readonly autoRefreshCheckbox = '.el-checkbox:has-text("自动刷新")';
  readonly lockGraphChart = '.lock-graph-chart';
  readonly graphContainer = '.graph-container';

  async goto(): Promise<void> {
    await super.goto('/locks');
  }

  async isLoaded(): Promise<boolean> {
    const titleVisible = await this.isVisible('.page-title');
    const selectVisible = await this.isVisible(this.connectionSelect);
    return titleVisible && selectVisible;
  }

  async getTitle(): Promise<string> {
    const title = this.page.locator('.page-title');
    await title.waitFor({ state: 'visible', timeout: 10000 });
    const titleText = await title.textContent();
    return titleText?.trim() || '';
  }

  async selectConnection(connectionName: string): Promise<void> {
    await this.click(this.connectionSelect);
    await this.page.locator(`.el-select-dropdown__item:has-text("${connectionName}")`).click();
    await this.waitForLoad();
  }

  async isTabsVisible(): Promise<boolean> {
    return await this.isVisible(this.lockWaitsTab);
  }

  async clickLockWaitsTab(): Promise<void> {
    await this.click(this.lockWaitsTab);
    await this.waitForLoad();
  }

  async clickDeadlocksTab(): Promise<void> {
    await this.click(this.deadlocksTab);
    await this.waitForLoad();
  }

  async clickLockGraphTab(): Promise<void> {
    await this.click(this.lockGraphTab);
    await this.waitForLoad();
  }

  async clickRefreshButton(): Promise<void> {
    await this.click(this.refreshButton);
    await this.waitForLoadingComplete();
  }

  async isTableVisible(): Promise<boolean> {
    return await this.isVisible(this.table);
  }

  async isEmptyStateVisible(): Promise<boolean> {
    return await this.isVisible(this.emptyState);
  }

  async getEmptyStateText(): Promise<string> {
    const empty = this.page.locator(this.emptyState);
    const description = empty.locator('.el-empty__description');
    return await description.textContent() || '';
  }

  async isRefreshButtonVisible(): Promise<boolean> {
    return await this.isVisible(this.refreshButton);
  }

  async selectTimeRange(hours: number): Promise<void> {
    await this.click(this.timeRangeSelect);
    await this.page.locator(this.historyHoursOption(hours)).click();
    await this.waitForLoadingComplete();
  }

  async isTimeRangeSelectVisible(): Promise<boolean> {
    return await this.isVisible(this.timeRangeSelect);
  }

  async isAutoRefreshCheckboxVisible(): Promise<boolean> {
    return await this.isVisible(this.autoRefreshCheckbox);
  }

  async isLockGraphChartVisible(): Promise<boolean> {
    return await this.isVisible(this.lockGraphChart);
  }

  async isLockGraphEmptyVisible(): Promise<boolean> {
    const empty = this.page.locator(`${this.graphContainer} ${this.emptyState}`);
    return await empty.isVisible();
  }

  async getTableHeaders(): Promise<string[]> {
    const headers = this.page.locator('.el-table__header-wrapper th');
    const count = await headers.count();
    const texts: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await headers.nth(i).textContent();
      if (text) texts.push(text.trim());
    }
    return texts;
  }

  async getTableRowCount(): Promise<number> {
    const rows = this.page.locator('.el-table__body-wrapper .el-table__row');
    return await rows.count();
  }

  async waitForLoadingComplete(): Promise<void> {
    await this.page.waitForSelector(this.loadingMask, { state: 'hidden', timeout: 10000 }).catch(() => {});
  }

  async isConnectionEmptyStateVisible(): Promise<boolean> {
    const empty = this.page.locator(this.emptyState);
    const description = empty.locator('.el-empty__description');
    const text = await description.textContent();
    return text?.includes('请先选择连接') || false;
  }
}
