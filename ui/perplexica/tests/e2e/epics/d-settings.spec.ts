import { test, expect } from '../fixtures/test-fixtures';

test.describe('Settings', () => {
    test('should open settings and toggle theme', async ({ page }) => {
        await page.goto('/');

        // Check theme toggle
        const themeBtn = page.getByTestId('theme-toggle');
        await expect(themeBtn).toBeVisible();
        await themeBtn.click();
        // Just verify it's clickable and exists for now
    });
});
