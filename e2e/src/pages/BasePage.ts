import { type Page, type Locator } from '@playwright/test';

export abstract class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto(path: string): Promise<void> {
    // Handle hash history routing - convert /path to /#/path
    if (!path.startsWith('#')) {
      const hashPath = path.startsWith('/') ? `/#${path}` : `/#/${path}`;
      await this.page.goto(hashPath);
    } else {
      await this.page.goto(path);
    }
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForTimeout(2000);
  }

  async waitForLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  async click(selector: string): Promise<void> {
    await this.page.click(selector);
  }

  async fill(selector: string, value: string): Promise<void> {
    await this.page.fill(selector, value);
  }

  async type(selector: string, text: string): Promise<void> {
    await this.page.type(selector, text);
  }

  async isVisible(selector: string): Promise<boolean> {
    return await this.page.isVisible(selector);
  }

  async isHidden(selector: string): Promise<boolean> {
    return await this.page.isHidden(selector);
  }

  async getText(selector: string): Promise<string> {
    return await this.page.textContent(selector) || '';
  }

  async getAttribute(selector: string, attribute: string): Promise<string | null> {
    return await this.page.getAttribute(selector, attribute);
  }

  async waitForElement(selector: string, timeout?: number): Promise<void> {
    await this.page.waitForSelector(selector, { timeout });
  }

  async waitForElementVisible(selector: string, timeout?: number): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'visible', timeout });
  }

  async waitForElementHidden(selector: string, timeout?: number): Promise<void> {
    await this.page.waitForSelector(selector, { state: 'hidden', timeout });
  }

  async checkText(selector: string, text: string): Promise<void> {
    await this.page.waitForSelector(selector);
    const elementText = await this.page.textContent(selector);
    if (!elementText || !elementText.includes(text)) {
      throw new Error(`Expected text "${text}" not found in element "${selector}"`);
    }
  }

  abstract isLoaded(): Promise<boolean>;
}
