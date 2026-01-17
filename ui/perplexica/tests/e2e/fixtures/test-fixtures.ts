import { test as base, expect } from '@playwright/test';
import { HomePage } from '../page-objects/HomePage';
import { ChatPage } from '../page-objects/ChatPage';
import { LibraryPage } from '../page-objects/LibraryPage';
import { SettingsDialog } from '../page-objects/SettingsDialog';

/**
 * Custom test fixtures that provide Page Objects
 * for all E2E tests.
 */
type TestFixtures = {
  homePage: HomePage;
  chatPage: ChatPage;
  libraryPage: LibraryPage;
  settingsDialog: SettingsDialog;
};

/**
 * Extended test with Page Object fixtures
 */
export const test = base.extend<TestFixtures>({
  homePage: async ({ page }, use) => {
    const homePage = new HomePage(page);
    await use(homePage);
  },

  chatPage: async ({ page }, use) => {
    const chatPage = new ChatPage(page);
    await use(chatPage);
  },

  libraryPage: async ({ page }, use) => {
    const libraryPage = new LibraryPage(page);
    await use(libraryPage);
  },

  settingsDialog: async ({ page }, use) => {
    const settingsDialog = new SettingsDialog(page);
    await use(settingsDialog);
  },
});

export { expect };

/**
 * Helper to create a chat for testing
 * Returns the chat ID from the URL
 */
export async function createTestChat(
  homePage: HomePage,
  chatPage: ChatPage,
  query = 'E2E_TOKEN_DOCX',
): Promise<string> {
  await homePage.goto();
  await homePage.search(query);
  await chatPage.waitForResults();

  // Extract chat ID from URL (format: /c/{chatId})
  const url = homePage.getCurrentUrl();
  const match = url.match(/\/c\/([a-zA-Z0-9-]+)/);
  return match?.[1] ?? '';
}

/**
 * Helper to wait for API response
 */
export async function waitForApiResponse(
  page: import('@playwright/test').Page,
  urlPattern: string | RegExp,
  timeout = 30_000,
): Promise<void> {
  await page.waitForResponse(
    (response) => {
      const url = response.url();
      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern);
      }
      return urlPattern.test(url);
    },
    { timeout },
  );
}

/**
 * Helper to mock API responses
 */
export async function mockApiResponse(
  page: import('@playwright/test').Page,
  urlPattern: string | RegExp,
  response: object,
  status = 200,
): Promise<void> {
  await page.route(urlPattern, (route) => {
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

/**
 * Helper to mock API error
 */
export async function mockApiError(
  page: import('@playwright/test').Page,
  urlPattern: string | RegExp,
  status = 500,
  message = 'Internal Server Error',
): Promise<void> {
  await page.route(urlPattern, (route) => {
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify({ error: message }),
    });
  });
}
