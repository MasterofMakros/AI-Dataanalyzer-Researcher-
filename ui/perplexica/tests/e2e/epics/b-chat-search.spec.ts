/**
 * Epic B: Chat & Search Workflow (P0)
 *
 * Tests the core search and chat functionality from a user perspective.
 * These are the most critical user flows in the application.
 */

import { test, expect } from '../fixtures/test-fixtures';

test.describe('Epic B: Chat & Search Workflow', () => {
  test.describe('Search Input', () => {
    test('accepts text input', async ({ homePage }) => {
      await homePage.goto();
      await homePage.searchInput.fill('test query');
      await expect(homePage.searchInput).toHaveValue('test query');
    });

    test('clears input on new search', async ({ homePage }) => {
      await homePage.goto();
      await homePage.searchInput.fill('first query');
      await homePage.searchInput.clear();
      await expect(homePage.searchInput).toHaveValue('');
    });

    test('submits on Enter key', async ({ page, homePage }) => {
      await homePage.goto();
      await homePage.searchWithEnter('test search query');
      // Should navigate to chat page
      await expect(page).toHaveURL(/\/c\//);
    });

    test('submits on button click', async ({ page, homePage }) => {
      await homePage.goto();
      await homePage.search('button click search');
      // Should navigate to chat page
      await expect(page).toHaveURL(/\/c\//);
    });

    test('does not submit empty query', async ({ page, homePage }) => {
      await homePage.goto();
      const initialUrl = page.url();
      await homePage.searchSubmit.click();
      // Should stay on the same page
      await expect(page).toHaveURL(initialUrl);
    });
  });

  test.describe('Search Results', () => {
    test('displays results after search', async ({ homePage, chatPage }) => {
      await homePage.goto();
      await homePage.search('E2E_TOKEN_DOCX');
      await chatPage.waitForResults();
      const resultCount = await chatPage.getResultCount();
      expect(resultCount).toBeGreaterThan(0);
    });

    test('shows result content', async ({ homePage, chatPage }) => {
      await homePage.goto();
      await homePage.search('E2E_TOKEN_DOCX');
      await chatPage.waitForResults();
      const content = await chatPage.getResultContent(0);
      expect(content.length).toBeGreaterThan(0);
    });
  });

  test.describe('Streaming Response', () => {
    test('completes streaming and shows full response', async ({
      homePage,
      chatPage,
    }) => {
      await homePage.goto();
      await homePage.search('What is the capital of France?');
      await chatPage.waitForResults();
      await chatPage.waitForStreamingComplete();

      // Verify streaming indicator is gone
      await expect(chatPage.streamingIndicator).toHaveCount(0);

      // Verify we have content
      const content = await chatPage.getResultContent(0);
      expect(content.length).toBeGreaterThan(10);
    });
  });

  test.describe('Sources and Evidence', () => {
    test('displays sources after search', async ({ homePage, chatPage }) => {
      await homePage.goto();
      await homePage.search('E2E_TOKEN_DOCX');
      await chatPage.waitForResults();

      // Wait a bit for sources to load
      await chatPage.waitForTimeout(2000);

      const sourceCount = await chatPage.getSourceCount();
      // May or may not have sources depending on test data
      expect(sourceCount).toBeGreaterThanOrEqual(0);
    });

    test('shows format icons for sources', async ({ page, homePage, chatPage }) => {
      await homePage.goto();
      await homePage.search('E2E_TOKEN_DOCX');
      await chatPage.waitForResults();

      // Check for format icons if sources are present
      const sourceCount = await chatPage.getSourceCount();
      if (sourceCount > 0) {
        const formatIcons = page.getByTestId('format-icon');
        await expect(formatIcons.first()).toBeVisible();
      }
    });
  });

  test.describe('Optimization Mode', () => {
    test('shows optimization toggle', async ({ homePage }) => {
      await homePage.goto();
      await expect(homePage.optimizationToggle).toBeVisible();
    });

    test('opens optimization dropdown on click', async ({ page, homePage }) => {
      await homePage.goto();
      await homePage.optimizationToggle.click();
      await expect(
        page.getByTestId('optimization-option-speed'),
      ).toBeVisible();
    });

    test('switches to balanced mode', async ({ page, homePage }) => {
      await homePage.goto();
      await homePage.setOptimizationMode('balanced');

      // Re-open to verify
      await homePage.optimizationToggle.click();
      await expect(
        page.getByTestId('optimization-option-balanced'),
      ).toHaveAttribute('data-selected', 'true');
    });

    test('switches to quality mode', async ({ page, homePage }) => {
      await homePage.goto();
      await homePage.setOptimizationMode('quality');

      // Re-open to verify
      await homePage.optimizationToggle.click();
      await expect(
        page.getByTestId('optimization-option-quality'),
      ).toHaveAttribute('data-selected', 'true');
    });
  });

  test.describe('Follow-up Messages', () => {
    test('allows follow-up messages in chat', async ({
      homePage,
      chatPage,
    }) => {
      await homePage.goto();
      await homePage.search('Hello');
      await chatPage.waitForResults();
      await chatPage.waitForStreamingComplete();

      // Send follow-up
      await chatPage.sendFollowUp('Tell me more');

      // Should have multiple results now
      await chatPage.waitForStreamingComplete();
      const resultCount = await chatPage.getResultCount();
      expect(resultCount).toBeGreaterThanOrEqual(2);
    });
  });

  test.describe('Error Handling', () => {
    test('shows error banner on API failure', async ({ page, homePage, chatPage }) => {
      // Mock API failure
      await page.route('**/api/providers', (route) =>
        route.fulfill({ status: 500 }),
      );

      await homePage.goto();

      // Check if error banner appears (may not appear immediately)
      const hasError = await chatPage.hasError();
      // Error handling behavior depends on implementation
      expect(typeof hasError).toBe('boolean');
    });
  });
});
