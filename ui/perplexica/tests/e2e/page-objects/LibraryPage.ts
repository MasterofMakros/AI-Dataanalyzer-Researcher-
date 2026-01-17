import { Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Page Object for the Library/History page.
 * Handles chat list, bulk operations, rename, and export.
 */
export class LibraryPage extends BasePage {
  // Chat list
  readonly chatList: Locator;
  readonly chatItems: Locator;

  // Selection mode
  readonly selectionModeButton: Locator;
  readonly selectAllButton: Locator;
  readonly bulkDeleteButton: Locator;

  // States
  readonly loadingSpinner: Locator;
  readonly emptyState: Locator;

  // Confirmation dialog
  readonly deleteConfirmation: Locator;
  readonly confirmDeleteButton: Locator;
  readonly cancelDeleteButton: Locator;

  constructor(page: import('@playwright/test').Page) {
    super(page);

    // Chat list
    this.chatList = this.getByTestId('chat-list');
    this.chatItems = this.getByTestId('chat-item');

    // Selection mode
    this.selectionModeButton = this.getByTestId('selection-mode-button');
    this.selectAllButton = this.getByTestId('select-all-button');
    this.bulkDeleteButton = this.getByTestId('bulk-delete-button');

    // States
    this.loadingSpinner = this.getByTestId('library-loading');
    this.emptyState = this.getByTestId('library-empty');

    // Confirmation dialog
    this.deleteConfirmation = this.getByTestId('delete-confirmation');
    this.confirmDeleteButton = this.getByTestId('confirm-delete');
    this.cancelDeleteButton = this.getByTestId('cancel-delete');
  }

  /**
   * Navigate to Library page
   */
  async goto(): Promise<void> {
    await this.page.goto('/library');
    await this.waitForChatsLoaded();
  }

  /**
   * Wait for chat list to load
   */
  async waitForChatsLoaded(timeout = 10_000): Promise<void> {
    // Wait for loading spinner to disappear
    try {
      await expect(this.loadingSpinner).toHaveCount(0, { timeout });
    } catch {
      // Loading spinner might not appear for fast loads
    }
  }

  /**
   * Get number of chats
   */
  async getChatCount(): Promise<number> {
    return await this.chatItems.count();
  }

  /**
   * Check if library is empty
   */
  async isEmpty(): Promise<boolean> {
    return await this.emptyState.isVisible();
  }

  /**
   * Enter selection mode for bulk operations
   */
  async enterSelectionMode(): Promise<void> {
    await this.selectionModeButton.click();
    await expect(this.selectAllButton).toBeVisible();
  }

  /**
   * Exit selection mode
   */
  async exitSelectionMode(): Promise<void> {
    await this.selectionModeButton.click();
    await expect(this.selectAllButton).toHaveCount(0);
  }

  /**
   * Select a chat by index
   */
  async selectChat(index: number): Promise<void> {
    const chatItem = this.chatItems.nth(index);
    const checkbox = chatItem.getByTestId('chat-checkbox');
    await checkbox.click();
  }

  /**
   * Select all chats
   */
  async selectAllChats(): Promise<void> {
    await this.selectAllButton.click();
  }

  /**
   * Get number of selected chats
   */
  async getSelectedCount(): Promise<number> {
    const checkboxes = this.page.locator(
      '[data-testid="chat-checkbox"]:checked',
    );
    return await checkboxes.count();
  }

  /**
   * Delete selected chats (bulk delete)
   */
  async bulkDelete(): Promise<void> {
    await this.bulkDeleteButton.click();
    await expect(this.deleteConfirmation).toBeVisible();
    await this.confirmDeleteButton.click();
  }

  /**
   * Cancel bulk delete
   */
  async cancelBulkDelete(): Promise<void> {
    await this.bulkDeleteButton.click();
    await expect(this.deleteConfirmation).toBeVisible();
    await this.cancelDeleteButton.click();
  }

  /**
   * Open rename input for a chat
   */
  async startRenameChat(index: number): Promise<void> {
    const chatItem = this.chatItems.nth(index);
    const renameButton = chatItem.getByTestId('rename-button');
    await renameButton.click();
    await expect(chatItem.getByTestId('rename-input')).toBeVisible();
  }

  /**
   * Rename a chat
   */
  async renameChat(index: number, newTitle: string): Promise<void> {
    await this.startRenameChat(index);
    const chatItem = this.chatItems.nth(index);
    const input = chatItem.getByTestId('rename-input');
    await input.fill(newTitle);
    await chatItem.getByTestId('rename-save').click();
  }

  /**
   * Cancel rename
   */
  async cancelRenameChat(index: number): Promise<void> {
    const chatItem = this.chatItems.nth(index);
    await this.page.keyboard.press('Escape');
    await expect(chatItem.getByTestId('rename-input')).toHaveCount(0);
  }

  /**
   * Get chat title by index
   */
  async getChatTitle(index: number): Promise<string> {
    const chatItem = this.chatItems.nth(index);
    const title = chatItem.getByTestId('chat-title');
    return (await title.textContent()) ?? '';
  }

  /**
   * Get chat timestamp by index
   */
  async getChatTimestamp(index: number): Promise<string> {
    const chatItem = this.chatItems.nth(index);
    const timestamp = chatItem.getByTestId('chat-timestamp');
    return (await timestamp.textContent()) ?? '';
  }

  /**
   * Open a chat by index
   */
  async openChat(index: number): Promise<void> {
    const chatItem = this.chatItems.nth(index);
    const link = chatItem.getByTestId('chat-link');
    await link.click();
    await this.page.waitForURL('**/c/*');
  }

  /**
   * Delete a single chat
   */
  async deleteChat(index: number): Promise<void> {
    const chatItem = this.chatItems.nth(index);
    const deleteButton = chatItem.getByTestId('delete-chat-button');
    await deleteButton.click();
    await expect(this.deleteConfirmation).toBeVisible();
    await this.confirmDeleteButton.click();
  }
}
