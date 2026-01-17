import { Page, Locator, expect } from '@playwright/test';

/**
 * Abstract base class for all Page Objects.
 * Provides common utilities for interacting with pages.
 */
export abstract class BasePage {
  constructor(protected page: Page) {}

  /**
   * Get element by data-testid attribute
   */
  protected getByTestId(testId: string): Locator {
    return this.page.getByTestId(testId);
  }

  /**
   * Wait for loading spinners to disappear
   */
  async waitForLoadingComplete(timeout = 30_000): Promise<void> {
    // Wait for any loading indicators to disappear
    const loadingIndicators = [
      '[data-testid="loading-spinner"]',
      '[data-testid="streaming-indicator"]',
      '.animate-pulse',
    ];

    for (const selector of loadingIndicators) {
      const count = await this.page.locator(selector).count();
      if (count > 0) {
        await expect(this.page.locator(selector).first()).toHaveCount(0, {
          timeout,
        });
      }
    }
  }

  /**
   * Wait for network to be idle
   */
  async waitForNetworkIdle(timeout = 10_000): Promise<void> {
    await this.page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Press a keyboard shortcut
   */
  async pressKey(key: string): Promise<void> {
    await this.page.keyboard.press(key);
  }

  /**
   * Check if an element is visible
   */
  async isVisible(testId: string): Promise<boolean> {
    return await this.getByTestId(testId).isVisible();
  }

  /**
   * Get current URL
   */
  getCurrentUrl(): string {
    return this.page.url();
  }

  /**
   * Wait for a specific timeout
   */
  async waitForTimeout(ms: number): Promise<void> {
    await this.page.waitForTimeout(ms);
  }
}
