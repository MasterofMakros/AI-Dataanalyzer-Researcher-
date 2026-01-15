import { expect, Page } from '@playwright/test';

export const DEFAULT_QUERY = 'E2E_TOKEN_DOCX';

export const openHome = async (page: Page) => {
  await page.goto('/');
  await expect(page.getByTestId('search-input')).toBeVisible();
};

export const submitQuery = async (page: Page, query = DEFAULT_QUERY) => {
  const input = page.getByTestId('search-input');
  await input.fill(query);
  await page.getByTestId('search-submit').click();
  await expect(page.getByTestId('result-item').first()).toBeVisible({
    timeout: 60_000,
  });
};

export const waitForAnySources = async (page: Page) => {
  await expect
    .poll(
      async () =>
        (await page.getByTestId('source-item').count()) +
        (await page.getByTestId('local-source-item').count()),
    )
    .toBeGreaterThan(0);
};

export const getMediaTrigger = async (
  page: Page,
  sourceType: 'image' | 'audio' | 'video',
) => {
  const local = page.locator(
    `[data-testid="local-source-item"][data-source-type="${sourceType}"] [data-testid="media-preview-open"]`,
  );
  if (await local.count()) {
    return local.first();
  }

  const web = page.locator(
    `[data-testid="source-item"][data-source-type="${sourceType}"] [data-testid="media-preview-open"]`,
  );
  if (await web.count()) {
    return web.first();
  }

  return null;
};
