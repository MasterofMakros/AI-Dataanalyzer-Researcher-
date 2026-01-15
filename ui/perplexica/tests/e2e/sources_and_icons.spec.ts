import { expect, test } from '@playwright/test';
import { openHome, submitQuery, waitForAnySources } from './helpers';

test('sources and format icons render', async ({ page }) => {
  await openHome(page);
  await submitQuery(page);
  await waitForAnySources(page);

  const sourceCount =
    (await page.getByTestId('source-item').count()) +
    (await page.getByTestId('local-source-item').count());
  expect(sourceCount).toBeGreaterThan(0);

  await expect(page.getByTestId('format-icon').first()).toBeVisible();
});
