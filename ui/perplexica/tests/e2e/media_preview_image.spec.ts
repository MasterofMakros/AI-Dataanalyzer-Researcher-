import { expect, test } from '@playwright/test';
import { getMediaTrigger, openHome, submitQuery } from './helpers';

test('image preview opens', async ({ page }) => {
  await openHome(page);
  await submitQuery(page);

  const trigger = await getMediaTrigger(page, 'image');
  test.skip(!trigger, 'no image sources available');

  await trigger!.click();
  await expect(page.getByTestId('media-preview-player')).toBeVisible();
});
