import { expect, test } from '@playwright/test';

test('shows error banner when providers fail', async ({ page }) => {
  await page.route('**/api/providers', async (route) => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'error' }),
    });
  });

  await page.goto('/');
  await expect(page.getByTestId('error-banner')).toBeVisible();
});
