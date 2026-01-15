import { expect, test } from '@playwright/test';
import { openHome, submitQuery } from './helpers';

test('search returns results', async ({ page }) => {
  await openHome(page);
  await submitQuery(page);
  await expect(page.getByTestId('results-list')).toBeVisible();
  await expect(page.getByTestId('result-item').first()).toBeVisible();
});
