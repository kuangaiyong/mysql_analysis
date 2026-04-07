import { test as base, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

type BaseFixtures = {
  baseURL: string;
  apiBaseURL: string;
  testWebSocketSimulation: void;
};

const injectWebSocketFunctions = (page: Page) => {
  page.addInitScript(() => {
    (window as any).__testPushMetrics = (data: any) => {
      window.dispatchEvent(new CustomEvent('metrics', { detail: data }));
    };
    (window as any).__testPushAlert = (data: any) => {
      window.dispatchEvent(new CustomEvent('alert', { detail: data }));
    };
    (window as any).__testPushSlowQuery = (data: any) => {
      window.dispatchEvent(new CustomEvent('slow-query', { detail: data }));
    };
  });
};

export const test = base.extend<BaseFixtures>({
  baseURL: async ({}, use) => {
    await use(process.env.BASE_URL || 'http://localhost:5173');
  },

  apiBaseURL: async ({}, use) => {
    await use(process.env.API_BASE_URL || 'http://localhost:8000');
  },

  testWebSocketSimulation: async ({ page }, use) => {
    injectWebSocketFunctions(page);
    await use();
  }
});

export { expect };
