import { expect, test } from '@playwright/test';
import { getMediaTrigger, openHome, submitQuery } from './helpers';

test('audio preview opens', async ({ page }) => {
  await openHome(page);
  await submitQuery(page);

  const trigger = await getMediaTrigger(page, 'audio');
  test.skip(!trigger, 'no audio sources available');

  await trigger!.click();
  const player = page.getByTestId('media-preview-player');
  await expect(player).toBeVisible();
  await expect(player).toHaveJSProperty('tagName', 'AUDIO');
});
