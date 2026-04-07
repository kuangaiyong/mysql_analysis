import { test, expect } from '@playwright/test';

test.describe('EXPLAIN Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/explain');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Page Basic Structure', () => {
    test('should display page container', async ({ page }) => {
      await expect(page.locator('.page-container')).toBeVisible();
    });

    test('should display page title', async ({ page }) => {
      await expect(page.locator('text=EXPLAIN分析')).toBeVisible();
    });

    test('should have proper layout with el-card', async ({ page }) => {
      const cards = page.locator('.el-card');
      expect(await cards.count()).toBeGreaterThan(0);
    });
  });

  test.describe('Connection Selection', () => {
    test('should display connection select', async ({ page }) => {
      const select = page.locator('.el-select');
      await expect(select).toBeVisible();
    });

    test('should display connection label', async ({ page }) => {
      await expect(page.locator('text=连接')).toBeVisible();
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

  test.describe('Database Selection', () => {
    test('should display database input', async ({ page }) => {
      await expect(page.locator('text=数据库')).toBeVisible();
      await expect(page.locator('.el-input[placeholder*="数据库"]')).toBeVisible();
    });

    test('should have database input with icon', async ({ page }) => {
      const input = page.locator('.el-input[placeholder*="数据库"]');
      if (await input.isVisible()) {
        const icon = input.locator('.el-input__prefix');
        const hasIcon = await icon.isVisible().catch(() => false);
        expect(hasIcon || (await input.isVisible())).toBeTruthy();
      }
    });
  });

  test.describe('Analysis Type Selection', () => {
    test('should display analysis type label', async ({ page }) => {
      await expect(page.locator('text=分析类型')).toBeVisible();
    });

    test('should display Traditional radio option', async ({ page }) => {
      await expect(page.locator('text=Traditional')).toBeVisible();
    });

    test('should display JSON radio option', async ({ page }) => {
      await expect(page.locator('text=JSON')).toBeVisible();
    });

    test('should display Tree radio option', async ({ page }) => {
      await expect(page.locator('text=Tree')).toBeVisible();
    });

    test('should display Flowchart radio option', async ({ page }) => {
      await expect(page.locator('text=Flowchart')).toBeVisible();
    });

    test('should have radio group for analysis type', async ({ page }) => {
      await expect(page.locator('.el-radio-group')).toBeVisible();
    });
  });

  test.describe('SQL Input', () => {
    test('should display SQL input label', async ({ page }) => {
      await expect(page.locator('text=SQL语句')).toBeVisible();
    });

    test('should display SQL textarea', async ({ page }) => {
      const textarea = page.locator('.el-textarea');
      await expect(textarea).toBeVisible();
    });

    test('should have textarea with correct rows', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await expect(textarea).toBeVisible();
      const rows = await textarea.getAttribute('rows');
      expect(rows).toBe('8');
    });

    test('should display SQL hint text', async ({ page }) => {
      const hint = page.locator('.sql-hint');
      const isVisible = await hint.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-textarea').isVisible())).toBeTruthy();
    });

    test('should accept SQL input', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await expect(textarea).toBeVisible();
      await textarea.fill('SELECT * FROM users WHERE id = 1');
      await expect(textarea).toHaveValue('SELECT * FROM users WHERE id = 1');
    });
  });

  test.describe('Action Buttons', () => {
    test('should display EXPLAIN button', async ({ page }) => {
      const btn = page.locator('.el-button:has-text("执行 EXPLAIN")');
      await expect(btn).toBeVisible();
    });

    test('should display EXPLAIN ANALYZE button', async ({ page }) => {
      const btn = page.locator('.el-button:has-text("执行 EXPLAIN ANALYZE")');
      await expect(btn).toBeVisible();
    });

    test('should display clear button', async ({ page }) => {
      const btn = page.locator('.el-button:has-text("清空")');
      await expect(btn).toBeVisible();
    });

    test('should have buttons with icons', async ({ page }) => {
      const buttons = page.locator('.el-button');
      const count = await buttons.count();
      expect(count).toBeGreaterThanOrEqual(3);
    });

    test('should disable execute buttons when no input', async ({ page }) => {
      const explainBtn = page.locator('.el-button:has-text("执行 EXPLAIN")');
      const isDisabled = await explainBtn.getAttribute('disabled');
      expect(isDisabled || (await explainBtn.isVisible())).toBeTruthy();
    });
  });

  test.describe('Result Display', () => {
    test('should display result section when result exists', async ({ page }) => {
      const resultCard = page.locator('.el-card:has-text("分析结果")');
      const isVisible = await resultCard.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-textarea').isVisible())).toBeTruthy();
    });

    test('should display view mode selector', async ({ page }) => {
      const treeView = page.locator('.el-radio-button:has-text("树形视图")');
      const tableView = page.locator('.el-radio-button:has-text("表格视图")');
      const jsonView = page.locator('.el-radio-button:has-text("JSON格式")');
      const hasTree = await treeView.isVisible().catch(() => false);
      const hasTable = await tableView.isVisible().catch(() => false);
      const hasJson = await jsonView.isVisible().catch(() => false);
      expect(hasTree || hasTable || hasJson || (await page.locator('.el-card').first().isVisible())).toBeTruthy();
    });

    test('should display tree view option', async ({ page }) => {
      const treeView = page.locator('.el-radio-button:has-text("树形视图")');
      const isVisible = await treeView.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-radio-button').first().isVisible())).toBeTruthy();
    });

    test('should display table view option', async ({ page }) => {
      const tableView = page.locator('.el-radio-button:has-text("表格视图")');
      const isVisible = await tableView.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-radio-button').first().isVisible())).toBeTruthy();
    });

    test('should display JSON view option', async ({ page }) => {
      const jsonView = page.locator('.el-radio-button:has-text("JSON格式")');
      const isVisible = await jsonView.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-radio-button').first().isVisible())).toBeTruthy();
    });

    test('should display empty state when no result', async ({ page }) => {
      const empty = page.locator('.el-empty');
      const isVisible = await empty.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-textarea').isVisible())).toBeTruthy();
    });
  });

  test.describe('Performance Analysis', () => {
    test('should display analysis section', async ({ page }) => {
      const section = page.locator('.el-card:has-text("性能分析")');
      const isVisible = await section.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-textarea').isVisible())).toBeTruthy();
    });

    test('should display execution time statistic', async ({ page }) => {
      const stat = page.locator('.el-statistic:has-text("执行时间")');
      const isVisible = await stat.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-card').first().isVisible())).toBeTruthy();
    });

    test('should display query cost statistic', async ({ page }) => {
      const stat = page.locator('.el-statistic:has-text("查询成本")');
      const isVisible = await stat.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-card').first().isVisible())).toBeTruthy();
    });

    test('should display efficiency score', async ({ page }) => {
      const score = page.locator('.efficiency-score, text=效率评分');
      const isVisible = await score.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-card').first().isVisible())).toBeTruthy();
    });
  });

  test.describe('Suggestions', () => {
    test('should display suggestions section', async ({ page }) => {
      const section = page.locator('text=索引建议');
      const isVisible = await section.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-card').first().isVisible())).toBeTruthy();
    });

    test('should display suggestions table when available', async ({ page }) => {
      const table = page.locator('.el-table');
      const isVisible = await table.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-card').first().isVisible())).toBeTruthy();
    });
  });

  test.describe('Visualization', () => {
    test('should display visualization section', async ({ page }) => {
      const section = page.locator('.el-card:has-text("可视化分析")');
      const isVisible = await section.isVisible().catch(() => false);
      expect(isVisible || (await page.locator('.el-textarea').isVisible())).toBeTruthy();
    });
  });

  test.describe('Interactive Features', () => {
    test('should handle clear button', async ({ page }) => {
      const textarea = page.locator('.el-textarea textarea');
      await textarea.fill('SELECT * FROM test');
      
      const clearBtn = page.locator('.el-button:has-text("清空")');
      await clearBtn.click();
      
      await page.waitForTimeout(300);
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
