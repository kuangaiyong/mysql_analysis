/**
 * E2E Test Utilities
 * Reusable helpers for page navigation, Element Plus selectors, and assertions
 */

import type { Page, Locator } from '@playwright/test'
import { expect } from '@playwright/test'

const BASE_URL = 'http://localhost:5173'

/**
 * Navigate to hash route (e.g., '/dashboard' becomes '#/dashboard')
 */
export async function navigateToPage(page: Page, path: string): Promise<void> {
  const hashPath = path.startsWith('#') ? path : `#${path}`
  await page.goto(`${BASE_URL}${hashPath}`)
  await waitForPageLoad(page)
}

/**
 * Wait for page to fully load
 */
export async function waitForPageLoad(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle')
  await page.waitForLoadState('domcontentloaded')
  
  // Wait for Element Plus components to be ready
  await page.waitForFunction(() => {
    return document.readyState === 'complete'
  })
}

/**
 * Get menu item selector by title text
 */
export function getMenuSelector(title: string): string {
  return `.el-menu-item:has-text("${title}")`
}

/**
 * Click sidebar menu item
 */
export async function clickMenuItem(page: Page, title: string): Promise<void> {
  const selector = getMenuSelector(title)
  await page.click(selector)
  await waitForPageLoad(page)
}

// ============================================
// Common Element Plus Selectors
// ============================================

/**
 * Get Element Plus button selector
 */
export function getElButton(selector?: string): string {
  if (selector) {
    return `.el-button${selector}`
  }
  return '.el-button'
}

/**
 * Get Element Plus input selector
 */
export function getElInput(selector?: string): string {
  if (selector) {
    return `.el-input${selector}`
  }
  return '.el-input'
}

/**
 * Get Element Plus table selector
 */
export function getElTable(selector?: string): string {
  if (selector) {
    return `.el-table${selector}`
  }
  return '.el-table'
}

/**
 * Get Element Plus select selector
 */
export function getElSelect(selector?: string): string {
  if (selector) {
    return `.el-select${selector}`
  }
  return '.el-select'
}

/**
 * Get Element Plus dialog selector
 */
export function getElDialog(selector?: string): string {
  if (selector) {
    return `.el-dialog${selector}`
  }
  return '.el-dialog'
}

/**
 * Get Element Plus form selector
 */
export function getElForm(selector?: string): string {
  if (selector) {
    return `.el-form${selector}`
  }
  return '.el-form'
}

/**
 * Get Element Plus card selector
 */
export function getElCard(selector?: string): string {
  if (selector) {
    return `.el-card${selector}`
  }
  return '.el-card'
}

/**
 * Get Element Plus pagination selector
 */
export function getElPagination(selector?: string): string {
  if (selector) {
    return `.el-pagination${selector}`
  }
  return '.el-pagination'
}

/**
 * Get Element Plus message box selector
 */
export function getElMessageBox(selector?: string): string {
  if (selector) {
    return `.el-message-box${selector}`
  }
  return '.el-message-box'
}

// ============================================
// Assertions
// ============================================

/**
 * Assert page has correct title
 */
export async function assertPageTitle(page: Page, expectedTitle: string): Promise<void> {
  await page.waitForSelector('.el-page-header', { state: 'visible' })
  const titleElement = await page.locator('.el-page-header__title').textContent()
  expect(titleElement?.trim()).toBe(expectedTitle)
}

/**
 * Assert element is visible
 */
export async function assertElementVisible(page: Page, selector: string): Promise<void> {
  await page.waitForSelector(selector, { state: 'visible' })
  const isVisible = await page.isVisible(selector)
  expect(isVisible).toBe(true)
}

/**
 * Assert element is hidden
 */
export async function assertElementHidden(page: Page, selector: string): Promise<void> {
  const isHidden = await page.isHidden(selector)
  expect(isHidden).toBe(true)
}

/**
 * Assert element contains text
 */
export async function assertElementText(page: Page, selector: string, expectedText: string): Promise<void> {
  await page.waitForSelector(selector, { state: 'visible' })
  const text = await page.locator(selector).textContent()
  expect(text?.trim()).toContain(expectedText)
}

/**
 * Assert table row count
 */
export async function assertTableRowCount(page: Page, selector: string, expectedCount: number): Promise<void> {
  await page.waitForSelector(selector, { state: 'visible' })
  const rows = await page.locator(`${selector} .el-table__row`).count()
  expect(rows).toBe(expectedCount)
}

/**
 * Check for console errors
 */
export async function assertNoConsoleErrors(page: Page): Promise<void> {
  const consoleErrors: string[] = []
  
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text())
    }
  })
  
  // Give time for any errors to be captured
  await page.waitForTimeout(1000)
  
  // Filter out known non-critical errors
  const criticalErrors = consoleErrors.filter(error => 
    !error.includes('[HMR]') && 
    !error.includes('favicon') &&
    !error.includes('sockjs')
  )
  
  expect(criticalErrors).toHaveLength(0)
}

// ============================================
// Helper Functions
// ============================================

/**
 * Get locator for Element Plus input and fill it
 */
export async function fillInput(page: Page, selector: string, value: string): Promise<void> {
  await page.waitForSelector(selector, { state: 'visible' })
  await page.fill(selector, value)
}

/**
 * Click button and wait for navigation/load
 */
export async function clickButton(page: Page, selector: string): Promise<void> {
  await page.waitForSelector(selector, { state: 'visible' })
  await page.click(selector)
  await waitForPageLoad(page)
}

/**
 * Select option from Element Plus select
 */
export async function selectOption(page: Page, selectSelector: string, optionText: string): Promise<void> {
  await page.waitForSelector(selectSelector, { state: 'visible' })
  await page.click(selectSelector)
  await page.waitForSelector('.el-select-dropdown__item', { state: 'visible' })
  await page.click(`.el-select-dropdown__item:has-text("${optionText}")`)
}

/**
 * Wait for dialog to appear
 */
export async function waitForDialog(page: Page, timeout = 5000): Promise<Locator> {
  const dialog = page.locator('.el-dialog:visible')
  await dialog.waitFor({ state: 'visible', timeout })
  return dialog
}

/**
 * Close dialog
 */
export async function closeDialog(page: Page): Promise<void> {
  const closeButton = page.locator('.el-dialog__headerbtn')
  if (await closeButton.isVisible()) {
    await closeButton.click()
    await page.waitForSelector('.el-dialog', { state: 'hidden' })
  }
}

/**
 * Wait for table to load data
 */
export async function waitForTableData(page: Page, selector = '.el-table'): Promise<void> {
  await page.waitForSelector(selector, { state: 'visible' })
  // Wait for loading to finish
  await page.waitForSelector('.el-table__body-wrapper .el-loading-mask', {
    state: 'hidden',
    timeout: 10000
  }).catch(() => {
    // Loading mask may not exist if data loads quickly
  })
}

/**
 * Get table cell text by row and column
 */
export async function getTableCellText(
  page: Page,
  rowIndex: number,
  columnIndex: number,
  tableSelector = '.el-table'
): Promise<string> {
  const cell = page.locator(`${tableSelector} .el-table__body tr:nth-child(${rowIndex + 1}) td:nth-child(${columnIndex + 1})`)
  await cell.waitFor({ state: 'visible' })
  return (await cell.textContent())?.trim() ?? ''
}
