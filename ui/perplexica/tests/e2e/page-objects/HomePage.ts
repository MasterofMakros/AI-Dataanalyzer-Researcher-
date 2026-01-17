import { Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Page Object for the Home/Search page.
 * Handles search input, optimization mode, and navigation.
 */
export class HomePage extends BasePage {
  // Search elements
  readonly searchInput: Locator;
  readonly searchSubmit: Locator;
  readonly searchForm: Locator;

  // Optimization mode
  readonly optimizationToggle: Locator;

  // Navigation
  readonly navHome: Locator;
  readonly navDiscover: Locator;
  readonly navLibrary: Locator;

  // Settings & Theme
  readonly themeToggle: Locator;
  readonly settingsButton: Locator;

  constructor(page: import('@playwright/test').Page) {
    super(page);

    // Search elements
    this.searchInput = this.getByTestId('search-input');
    this.searchSubmit = this.getByTestId('search-submit');
    this.searchForm = this.getByTestId('search-form');

    // Optimization mode
    this.optimizationToggle = this.getByTestId('optimization-mode-toggle');

    // Navigation links
    this.navHome = page.locator('a[href="/"]').first();
    this.navDiscover = page.locator('a[href="/discover"]');
    this.navLibrary = page.locator('a[href="/library"]');

    // Settings & Theme
    this.themeToggle = this.getByTestId('theme-toggle');
    this.settingsButton = this.getByTestId('settings-button');
  }

  /**
   * Navigate to the home page
   */
  async goto(): Promise<void> {
    await this.page.goto('/');
    await expect(this.searchInput).toBeVisible({ timeout: 10_000 });
  }

  /**
   * Perform a search query
   */
  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.searchSubmit.click();
  }

  /**
   * Submit search with Enter key
   */
  async searchWithEnter(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.page.keyboard.press('Enter');
  }

  /**
   * Set optimization mode (speed, balanced, quality)
   */
  async setOptimizationMode(
    mode: 'speed' | 'balanced' | 'quality',
  ): Promise<void> {
    await this.optimizationToggle.click();
    await this.getByTestId(`optimization-option-${mode}`).click();
  }

  /**
   * Get current optimization mode
   */
  async getCurrentOptimizationMode(): Promise<string | null> {
    await this.optimizationToggle.click();
    const options = ['speed', 'balanced', 'quality'];

    for (const option of options) {
      const element = this.getByTestId(`optimization-option-${option}`);
      const isSelected = await element.getAttribute('data-selected');
      if (isSelected === 'true') {
        await this.page.keyboard.press('Escape');
        return option;
      }
    }

    await this.page.keyboard.press('Escape');
    return null;
  }

  /**
   * Toggle theme (dark/light)
   */
  async toggleTheme(): Promise<void> {
    await this.themeToggle.click();
  }

  /**
   * Get current theme
   */
  async getCurrentTheme(): Promise<'dark' | 'light'> {
    const html = this.page.locator('html');
    const classList = await html.getAttribute('class');
    return classList?.includes('dark') ? 'dark' : 'light';
  }

  /**
   * Open settings dialog
   */
  async openSettings(): Promise<void> {
    await this.settingsButton.click();
    await expect(this.getByTestId('settings-dialog')).toBeVisible();
  }

  /**
   * Navigate to Library page
   */
  async navigateToLibrary(): Promise<void> {
    await this.navLibrary.click();
    await this.page.waitForURL('**/library');
  }

  /**
   * Navigate to Discover page
   */
  async navigateToDiscover(): Promise<void> {
    await this.navDiscover.click();
    await this.page.waitForURL('**/discover');
  }

  /**
   * Check if search input is focused
   */
  async isSearchFocused(): Promise<boolean> {
    return await this.searchInput.evaluate(
      (el) => document.activeElement === el,
    );
  }

  /**
   * Open keyboard shortcuts help with ? key
   */
  async openKeyboardShortcuts(): Promise<void> {
    await this.page.keyboard.press('?');
    await expect(this.getByTestId('keyboard-shortcuts-modal')).toBeVisible();
  }
}
