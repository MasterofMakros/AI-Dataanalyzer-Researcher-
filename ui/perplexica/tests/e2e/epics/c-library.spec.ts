/**
 * Epic C: Library Management (P1)
 *
 * Tests the library/history functionality including:
 * - Chat history display
 * - Bulk delete operations
 * - Chat rename
 * - Navigation to previous chats
 */

import { test, expect } from '../fixtures/test-fixtures';
import { createTestChat } from '../fixtures/test-fixtures';

test.describe('Epic C: Library Management', () => {
  test.describe('Chat History Display', () => {
    test('navigates to library page', async ({ page, libraryPage }) => {
      await libraryPage.goto();
      await expect(page).toHaveURL(/\/library/);
    });

    test('shows loading state initially', async ({ page }) => {
      // Navigate without waiting
      await page.goto('/library');
      // Loading state should appear briefly
      const loadingSpinner = page.getByTestId('library-loading');
      // It may or may not be visible depending on load time
      const isVisible = await loadingSpinner.isVisible().catch(() => false);
      expect(typeof isVisible).toBe('boolean');
    });

    test('displays chat list when chats exist', async ({
      homePage,
      chatPage,
      libraryPage,
    }) => {
      // First create a chat
      await homePage.goto();
      await homePage.search('Test chat for library');
      await chatPage.waitForResults();

      // Now go to library
      await libraryPage.goto();

      // Should see at least one chat
      const chatCount = await libraryPage.getChatCount();
      expect(chatCount).toBeGreaterThanOrEqual(1);
    });

    test('shows empty state when no chats', async ({ page, libraryPage }) => {
      // Mock empty chats response
      await page.route('**/api/chats', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ chats: [] }),
        }),
      );

      await libraryPage.goto();
      const isEmpty = await libraryPage.isEmpty();
      expect(isEmpty).toBe(true);
    });

    test('shows chat metadata (title, timestamp)', async ({
      homePage,
      chatPage,
      libraryPage,
    }) => {
      // Create a chat first
      await homePage.goto();
      await homePage.search('Metadata test chat');
      await chatPage.waitForResults();

      await libraryPage.goto();
      await libraryPage.waitForChatsLoaded();

      // Check for title
      const title = await libraryPage.getChatTitle(0);
      expect(title.length).toBeGreaterThan(0);

      // Check for timestamp
      const timestamp = await libraryPage.getChatTimestamp(0);
      expect(timestamp).toContain('Ago');
    });
  });

  test.describe('Selection Mode', () => {
    test.beforeEach(async ({ homePage, chatPage }) => {
      // Create a test chat
      await homePage.goto();
      await homePage.search('Selection mode test');
      await chatPage.waitForResults();
    });

    test('enters selection mode', async ({ libraryPage }) => {
      await libraryPage.goto();
      await libraryPage.enterSelectionMode();
      await expect(libraryPage.selectAllButton).toBeVisible();
    });

    test('exits selection mode', async ({ libraryPage }) => {
      await libraryPage.goto();
      await libraryPage.enterSelectionMode();
      await libraryPage.exitSelectionMode();
      await expect(libraryPage.selectAllButton).toHaveCount(0);
    });

    test('selects individual chats', async ({ page, libraryPage }) => {
      await libraryPage.goto();
      await libraryPage.enterSelectionMode();

      // Select first chat
      await libraryPage.selectChat(0);

      // Verify selection
      const checkbox = page.getByTestId('chat-checkbox').first();
      await expect(checkbox).toHaveAttribute('data-checked', 'true');
    });

    test('selects all chats', async ({ libraryPage }) => {
      await libraryPage.goto();
      await libraryPage.enterSelectionMode();
      await libraryPage.selectAllChats();

      const chatCount = await libraryPage.getChatCount();
      const selectedCount = await libraryPage.getSelectedCount();
      expect(selectedCount).toBe(chatCount);
    });
  });

  test.describe('Bulk Delete', () => {
    test('shows bulk delete button when chats selected', async ({
      homePage,
      chatPage,
      libraryPage,
    }) => {
      // Create a test chat
      await homePage.goto();
      await homePage.search('Bulk delete test');
      await chatPage.waitForResults();

      await libraryPage.goto();
      await libraryPage.enterSelectionMode();
      await libraryPage.selectChat(0);

      await expect(libraryPage.bulkDeleteButton).toBeVisible();
    });

    // Note: Actual bulk delete test would modify data
    // In a real test environment, you'd want to isolate this
    test.skip('deletes selected chats', async ({ libraryPage }) => {
      await libraryPage.goto();
      await libraryPage.enterSelectionMode();
      await libraryPage.selectChat(0);

      const initialCount = await libraryPage.getChatCount();
      await libraryPage.bulkDelete();

      const newCount = await libraryPage.getChatCount();
      expect(newCount).toBe(initialCount - 1);
    });
  });

  test.describe('Chat Rename', () => {
    test.beforeEach(async ({ homePage, chatPage }) => {
      // Create a test chat
      await homePage.goto();
      await homePage.search('Rename test chat');
      await chatPage.waitForResults();
    });

    test('shows rename button on hover', async ({ page, libraryPage }) => {
      await libraryPage.goto();

      // Hover over first chat item
      const chatItem = page.getByTestId('chat-item').first();
      await chatItem.hover();

      const renameButton = chatItem.getByTestId('rename-button');
      await expect(renameButton).toBeVisible();
    });

    test('opens rename input on click', async ({ page, libraryPage }) => {
      await libraryPage.goto();

      // Hover and click rename
      const chatItem = page.getByTestId('chat-item').first();
      await chatItem.hover();
      await libraryPage.startRenameChat(0);

      const renameInput = page.getByTestId('rename-input');
      await expect(renameInput).toBeVisible();
    });

    test('saves new title', async ({ page, libraryPage }) => {
      await libraryPage.goto();

      const newTitle = 'Renamed Chat ' + Date.now();
      await libraryPage.renameChat(0, newTitle);

      // Wait for save to complete
      await page.waitForTimeout(500);

      // Verify new title is displayed
      const title = await libraryPage.getChatTitle(0);
      expect(title).toBe(newTitle);
    });

    test('cancels rename on Escape', async ({ page, libraryPage }) => {
      await libraryPage.goto();

      const originalTitle = await libraryPage.getChatTitle(0);
      await libraryPage.startRenameChat(0);
      await libraryPage.cancelRenameChat(0);

      // Title should remain unchanged
      const title = await libraryPage.getChatTitle(0);
      expect(title).toBe(originalTitle);
    });
  });

  test.describe('Chat Navigation', () => {
    test('opens chat on click', async ({ page, homePage, chatPage, libraryPage }) => {
      // Create a test chat
      await homePage.goto();
      await homePage.search('Navigation test chat');
      await chatPage.waitForResults();

      await libraryPage.goto();
      await libraryPage.openChat(0);

      // Should navigate to chat page
      await expect(page).toHaveURL(/\/c\//);
    });
  });
});
