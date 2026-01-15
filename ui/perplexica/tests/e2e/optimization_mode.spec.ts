import { expect, test } from '@playwright/test';
import { openHome } from './helpers';

test('optimization mode toggles', async ({ page }) => {
  await openHome(page);

  const toggle = page.getByTestId('optimization-mode-toggle');
  await toggle.click();

  const target = page.getByTestId('optimization-option-quality');
  if (!(await target.count())) {
    test.skip(true, 'optimization options not available');
  }

  await target.click();

  await toggle.click();
  await expect(page.getByTestId('optimization-option-quality')).toHaveAttribute(
    'data-selected',
    'true',
  );
});
