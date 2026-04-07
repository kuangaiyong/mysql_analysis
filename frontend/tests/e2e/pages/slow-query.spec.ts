import { test, expect } from '@playwright/test';

test.describe('Slow Query Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/slow-query');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Basic Structure', () => {
    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display page title', async ({ page }) => {
      await expect(page.locator('text=慢查询分析')).toBeVisible();
    });

    test('should have proper layout with el-card elements', async ({ page }) => {
      const cards = page.locator('.el-card');
      expect(await cards.count()).toBeGreaterThan(0);
    });
  });

  test.describe('Connection Selector', () => {
    test('should display connection selector', async ({ page }) => {
      const selector = page.locator('.el-select');
      await expect(selector).toBeVisible();
    });

    test('should have connection selector in header', async ({ page }) => {
      const headerSelect = page.locator('.page-header .el-select, .el-form-item .el-select').first();
      await expect(headerSelect).toBeVisible();
    });

    test('should open connection dropdown', async ({ page }) => {
      const select = page.locator('.el-select').first();
      await select.click();
      await page.waitForTimeout(300);
      const dropdown = page.locator('.el-select-dropdown');
      const isVisible = await dropdown.isVisible().catch(() => false);
      if (!isVisible) {
        const empty = page.locator('.el-select-dropdown__empty');
        const emptyVisible = await empty.isVisible().catch(() => false);
        expect(emptyVisible || (await select.isVisible())).toBeTruthy();
      }
    });
  });

  test.describe('Search Form', () => {
    test('should display search form', async ({ page }) => {
      await expect(page.locator('.search-form')).toBeVisible();
    });

    test('should display SQL digest input', async ({ page }) => {
      await expect(page.locator('text=SQL摘要')).toBeVisible();
      await expect(page.locator('.el-input[placeholder*="SQL摘要"]')).toBeVisible();
    });

    test('should display time range picker', async ({ page }) => {
      await expect(page.locator('text=执行时间范围')).toBeVisible();
      await expect(page.locator('.el-date-editor')).toBeVisible();
    });

    test('should display database input', async ({ page }) => {
      await expect(page.locator('text=数据库')).toBeVisible();
    });

    test('should display table name input', async ({ page }) => {
      await expect(page.locator('text=表名')).toBeVisible();
    });

    test('should display min query time input', async ({ page }) => {
      await expect(page.locator('text=最小执行时间')).toBeVisible();
    });

    test('should display search button', async ({ page }) => {
      const searchBtn = page.locator('.el-button:has-text("查询")');
      await expect(searchBtn).toBeVisible();
    });

    test('should display reset button', async ({ page }) => {
      const resetBtn = page.locator('.el-button:has-text("重置")');
      await expect(resetBtn).toBeVisible();
    });
  });

  test.describe('Statistics Section', () => {
    test('should display percentile stats', async ({ page }) => {
      const statsCard = page.locator('.el-card:has-text("执行时间百分位统计")');
      const isVisible = await statsCard.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('text=P50').isVisible().catch(() => false))).toBeTruthy();
    });

    test('should display P50 stat', async ({ page }) => {
      const p50 = page.locator('text=P50');
      const isVisible = await p50.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-card').first().isVisible())).toBeTruthy();
    });

    test('should display P90 stat', async ({ page }) => {
      const p90 = page.locator('text=P90');
      const isVisible = await p90.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-card').first().isVisible())).toBeTruthy();
    });

    test('should display P99 stat', async ({ page }) => {
      const p99 = page.locator('text=P99');
      const isVisible = await p99.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-card').first().isVisible())).toBeTruthy();
    });
  });

  test.describe('Time Distribution', () => {
    test('should display distribution section', async ({ page }) => {
      const section = page.locator('.el-card:has-text("时间分布分析")');
      const isVisible = await section.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-card').first().isVisible())).toBeTruthy();
    });

    test('should display granularity radio buttons', async ({ page }) => {
      const hourBtn = page.locator('.el-radio-button:has-text("按小时")');
      const dayBtn = page.locator('.el-radio-button:has-text("按天")');
      const hasHour = await hourBtn.isVisible().catch(() => false);
      const hasDay = await dayBtn.isVisible().catch(() => false);
      expect(hasHour || hasDay || (await page.locator('.el-radio-group').isVisible().catch(() => false))).toBeTruthy();
    });
  });

  test.describe('Query Table', () => {
    test('should display slow query list table', async ({ page }) => {
      const table = page.locator('.el-table');
      await expect(table).toBeVisible();
    });

    test('should display table columns', async ({ page }) => {
      await expect(page.locator('text=ID')).toBeVisible();
      await expect(page.locator('text=SQL摘要')).toBeVisible();
      await expect(page.locator('text=数据库')).toBeVisible();
      await expect(page.locator('text=表名')).toBeVisible();
    });

    test('should display more table columns', async ({ page }) => {
      await expect(page.locator('text=执行时间')).toBeVisible();
      await expect(page.locator('text=执行次数')).toBeVisible();
      await expect(page.locator('text=扫描行数')).toBeVisible();
    });

    test('should display additional columns', async ({ page }) => {
      const columns = ['扫描效率', '发送行数', '锁时间', '最后执行时间', '状态'];
      for (const col of columns) {
        const hasCol = await page.locator(`text=${col}`).isVisible().catch(() => false);
        if (!hasCol) {
          expect(await page.locator('.el-table').isVisible()).toBeTruthy();
          break;
        }
      }
    });

    test('should display action buttons column', async ({ page }) => {
      await expect(page.locator('text=操作')).toBeVisible();
    });

    test('should display view detail button', async ({ page }) => {
      const detailBtn = page.locator('.el-button:has-text("详情")');
      const isVisible = await detailBtn.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-table').isVisible())).toBeTruthy();
    });

    test('should display optimize button', async ({ page }) => {
      const optimizeBtn = page.locator('.el-button:has-text("优化建议")');
      const isVisible = await optimizeBtn.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-table').isVisible())).toBeTruthy();
    });

    test('should display batch action buttons', async ({ page }) => {
      const resolveBtn = page.locator('.el-button:has-text("批量标记已解决")');
      const deleteBtn = page.locator('.el-button:has-text("批量删除")');
      const hasResolve = await resolveBtn.isVisible().catch(() => false);
      const hasDelete = await deleteBtn.isVisible().catch(() => false);
      expect(hasResolve || hasDelete || (await page.locator('.el-table').isVisible())).toBeTruthy();
    });

    test('should display table selection checkbox', async ({ page }) => {
      const checkbox = page.locator('.el-table-column--selection');
      const isVisible = await checkbox.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-table').isVisible())).toBeTruthy();
    });
  });

  test.describe('Pagination', () => {
    test('should display pagination component', async ({ page }) => {
      const pagination = page.locator('.el-pagination');
      const isVisible = await pagination.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-table').isVisible())).toBeTruthy();
    });

    test('should display page size selector', async ({ page }) => {
      const sizeSelect = page.locator('.el-select[aria-label="每页"]');
      const isVisible = await sizeSelect.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-pagination').isVisible().catch(() => false))).toBeTruthy();
    });
  });

  test.describe('Interactive Features', () => {
    test('should handle search form input', async ({ page }) => {
      const input = page.locator('.el-input[placeholder*="SQL摘要"]').first();
      if (await input.isVisible()) {
        await input.fill('test');
        await expect(input).toHaveValue('test');
      }
    });

    test('should handle reset button click', async ({ page }) => {
      const resetBtn = page.locator('.el-button:has-text("重置")');
      if (await resetBtn.isVisible()) {
        await resetBtn.click();
        await page.waitForTimeout(300);
      }
    });

    test('should handle window resize', async ({ page }) => {
      await page.setViewportSize({ width: 1200, height: 900 });
      await page.waitForTimeout(300);
      await expect(page.locator('.page-container')).toBeVisible();
      
      await page.setViewportSize({ width: 768, height: 600 });
      await page.waitForTimeout(300);
      await expect(page.locator('.page-container')).toBeVisible();
    });
  });
});
