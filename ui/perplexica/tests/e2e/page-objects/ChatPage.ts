import { Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Page Object for the Chat/Conversation page.
 * Handles results, sources, streaming, and export.
 */
export class ChatPage extends BasePage {
  // Results
  readonly resultsList: Locator;
  readonly resultItems: Locator;

  // Sources
  readonly sourcesPanel: Locator;
  readonly localSourcesPanel: Locator;
  readonly sourceItems: Locator;
  readonly localSourceItems: Locator;

  // Streaming
  readonly streamingIndicator: Locator;

  // Actions
  readonly messageInput: Locator;
  readonly exportButton: Locator;
  readonly deleteButton: Locator;

  // Error handling
  readonly errorBanner: Locator;

  constructor(page: import('@playwright/test').Page) {
    super(page);

    // Results
    this.resultsList = this.getByTestId('results-list');
    this.resultItems = this.getByTestId('result-item');

    // Sources
    this.sourcesPanel = this.getByTestId('sources-panel');
    this.localSourcesPanel = this.getByTestId('local-sources-panel');
    this.sourceItems = this.getByTestId('source-item');
    this.localSourceItems = this.getByTestId('local-source-item');

    // Streaming
    this.streamingIndicator = this.getByTestId('streaming-indicator');

    // Actions
    this.messageInput = this.getByTestId('search-input');
    this.exportButton = this.getByTestId('export-button');
    this.deleteButton = this.getByTestId('delete-chat-button');

    // Error handling
    this.errorBanner = this.getByTestId('error-banner');
  }

  /**
   * Wait for search results to appear
   */
  async waitForResults(timeout = 60_000): Promise<void> {
    await expect(this.resultItems.first()).toBeVisible({ timeout });
  }

  /**
   * Wait for streaming to complete
   */
  async waitForStreamingComplete(timeout = 90_000): Promise<void> {
    // First wait for streaming to start (indicator appears)
    // Then wait for it to complete (indicator disappears)
    try {
      await expect(this.streamingIndicator).toBeVisible({ timeout: 5_000 });
    } catch {
      // Streaming might have already completed or not started
    }
    await expect(this.streamingIndicator).toHaveCount(0, { timeout });
  }

  /**
   * Get total source count (web + local)
   */
  async getSourceCount(): Promise<number> {
    const webSources = await this.sourceItems.count();
    const localSources = await this.localSourceItems.count();
    return webSources + localSources;
  }

  /**
   * Get web source count only
   */
  async getWebSourceCount(): Promise<number> {
    return await this.sourceItems.count();
  }

  /**
   * Get local source count only
   */
  async getLocalSourceCount(): Promise<number> {
    return await this.localSourceItems.count();
  }

  /**
   * Open source preview by index
   */
  async openSourcePreview(index: number): Promise<void> {
    const source = this.sourceItems.nth(index);
    const previewTrigger = source.getByTestId('media-preview-open');

    if ((await previewTrigger.count()) > 0) {
      await previewTrigger.click();
    } else {
      // Click on the source card directly
      await source.click();
    }

    await expect(this.getByTestId('source-preview-modal')).toBeVisible();
  }

  /**
   * Open local source preview by index
   */
  async openLocalSourcePreview(index: number): Promise<void> {
    const source = this.localSourceItems.nth(index);
    await source.click();
    await expect(this.getByTestId('source-preview-modal')).toBeVisible();
  }

  /**
   * Close source preview
   */
  async closeSourcePreview(): Promise<void> {
    await this.page.keyboard.press('Escape');
    await expect(this.getByTestId('source-preview-modal')).toHaveCount(0);
  }

  /**
   * Send a follow-up message
   */
  async sendFollowUp(message: string): Promise<void> {
    await this.messageInput.fill(message);
    await this.page.keyboard.press('Enter');
  }

  /**
   * Export chat as Markdown
   */
  async exportAsMarkdown(): Promise<void> {
    await this.exportButton.click();
    await this.getByTestId('export-markdown').click();
  }

  /**
   * Export chat as PDF
   */
  async exportAsPDF(): Promise<void> {
    await this.exportButton.click();
    await this.getByTestId('export-pdf').click();
  }

  /**
   * Delete the current chat
   */
  async deleteChat(): Promise<void> {
    await this.deleteButton.click();
    await this.getByTestId('confirm-delete').click();
  }

  /**
   * Check if error banner is visible
   */
  async hasError(): Promise<boolean> {
    return await this.errorBanner.isVisible();
  }

  /**
   * Get error message text
   */
  async getErrorMessage(): Promise<string> {
    return await this.errorBanner.textContent() ?? '';
  }

  /**
   * Get result content by index
   */
  async getResultContent(index: number): Promise<string> {
    return (await this.resultItems.nth(index).textContent()) ?? '';
  }

  /**
   * Get number of results
   */
  async getResultCount(): Promise<number> {
    return await this.resultItems.count();
  }

  /**
   * Check if sources are visible
   */
  async hasVisibleSources(): Promise<boolean> {
    const webVisible = await this.sourcesPanel.isVisible();
    const localVisible = await this.localSourcesPanel.isVisible();
    return webVisible || localVisible;
  }
}
