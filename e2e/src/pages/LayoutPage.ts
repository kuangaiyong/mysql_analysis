import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class LayoutPage extends BasePage {
  readonly sidebarSelector = '.el-aside';
  readonly headerSelector = '.el-header';
  readonly mainContentSelector = '.el-main';
  readonly menuItemsSelector = '.el-menu-item';
  readonly tabsSelector = '.el-tabs';

  async isLoaded(): Promise<boolean> {
    const sidebarVisible = await this.isVisible(this.sidebarSelector);
    const headerVisible = await this.isVisible(this.headerSelector);
    const mainContentVisible = await this.isVisible(this.mainContentSelector);
    return sidebarVisible && headerVisible && mainContentVisible;
  }

  async navigateToMenuItem(menuItemText: string): Promise<void> {
    await this.click(`.el-menu-item:has-text("${menuItemText}")`);
    await this.waitForLoad();
  }

  async getActiveMenuItem(): Promise<string> {
    const activeItem = this.page.locator('.el-menu-item.is-active');
    return await activeItem.textContent() || '';
  }

  async clickTab(tabText: string): Promise<void> {
    await this.click(`.el-tabs__item:has-text("${tabText}")`);
    await this.page.waitForTimeout(500);
  }

  async getActiveTab(): Promise<string> {
    const activeTab = this.page.locator('.el-tabs__item.is-active');
    return await activeTab.textContent() || '';
  }
}
