import { Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Page Object for the Settings Dialog.
 * Handles theme, models, providers, and preferences.
 */
export class SettingsDialog extends BasePage {
  // Dialog container
  readonly dialog: Locator;
  readonly closeButton: Locator;

  // Tabs
  readonly preferencesTab: Locator;
  readonly modelsTab: Locator;
  readonly searchTab: Locator;
  readonly personalizationTab: Locator;

  // Theme
  readonly themeSelect: Locator;

  // Models
  readonly chatModelSelect: Locator;
  readonly embeddingModelSelect: Locator;
  readonly modelProviderList: Locator;
  readonly addProviderButton: Locator;

  constructor(page: import('@playwright/test').Page) {
    super(page);

    // Dialog container
    this.dialog = this.getByTestId('settings-dialog');
    this.closeButton = this.getByTestId('settings-close');

    // Tabs
    this.preferencesTab = this.getByTestId('settings-tab-preferences');
    this.modelsTab = this.getByTestId('settings-tab-models');
    this.searchTab = this.getByTestId('settings-tab-search');
    this.personalizationTab = this.getByTestId('settings-tab-personalization');

    // Theme
    this.themeSelect = this.getByTestId('theme-select');

    // Models
    this.chatModelSelect = this.getByTestId('chat-model-select');
    this.embeddingModelSelect = this.getByTestId('embedding-model-select');
    this.modelProviderList = this.getByTestId('model-provider-list');
    this.addProviderButton = this.getByTestId('add-provider-button');
  }

  /**
   * Wait for dialog to be visible
   */
  async waitForOpen(): Promise<void> {
    await expect(this.dialog).toBeVisible();
  }

  /**
   * Close the settings dialog
   */
  async close(): Promise<void> {
    await this.closeButton.click();
    await expect(this.dialog).toHaveCount(0);
  }

  /**
   * Close with Escape key
   */
  async closeWithEscape(): Promise<void> {
    await this.page.keyboard.press('Escape');
    await expect(this.dialog).toHaveCount(0);
  }

  /**
   * Switch to a specific tab
   */
  async switchToTab(
    tab: 'preferences' | 'models' | 'search' | 'personalization',
  ): Promise<void> {
    const tabLocator = this.getByTestId(`settings-tab-${tab}`);
    await tabLocator.click();
    // Wait for tab content to load
    await this.page.waitForTimeout(100);
  }

  /**
   * Set theme
   */
  async setTheme(theme: 'light' | 'dark' | 'system'): Promise<void> {
    await this.themeSelect.selectOption(theme);
  }

  /**
   * Get current theme setting
   */
  async getCurrentThemeSetting(): Promise<string> {
    return await this.themeSelect.inputValue();
  }

  /**
   * Select chat model
   */
  async selectChatModel(modelName: string): Promise<void> {
    await this.switchToTab('models');
    await this.chatModelSelect.selectOption({ label: modelName });
  }

  /**
   * Select embedding model
   */
  async selectEmbeddingModel(modelName: string): Promise<void> {
    await this.switchToTab('models');
    await this.embeddingModelSelect.selectOption({ label: modelName });
  }

  /**
   * Get available chat models
   */
  async getAvailableChatModels(): Promise<string[]> {
    await this.switchToTab('models');
    const options = this.chatModelSelect.locator('option');
    const count = await options.count();
    const models: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await options.nth(i).textContent();
      if (text) models.push(text);
    }
    return models;
  }

  /**
   * Add a new provider
   */
  async addProvider(name: string, apiKey: string): Promise<void> {
    await this.switchToTab('models');
    await this.addProviderButton.click();

    await this.getByTestId('provider-name-input').fill(name);
    await this.getByTestId('provider-apikey-input').fill(apiKey);
    await this.getByTestId('provider-save-button').click();
  }

  /**
   * Get provider count
   */
  async getProviderCount(): Promise<number> {
    await this.switchToTab('models');
    return await this.modelProviderList
      .locator('[data-testid="provider-item"]')
      .count();
  }

  /**
   * Check if dialog is open
   */
  async isOpen(): Promise<boolean> {
    return await this.dialog.isVisible();
  }
}
