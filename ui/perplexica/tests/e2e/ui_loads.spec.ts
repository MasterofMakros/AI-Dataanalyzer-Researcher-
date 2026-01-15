import { expect, test } from '@playwright/test';
import { openHome } from './helpers';

test('ui loads without error banner', async ({ page }) => {
  await openHome(page);
  await expect(page.getByTestId('error-banner')).toHaveCount(0);
});
