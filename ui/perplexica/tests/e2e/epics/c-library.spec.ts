import { test, expect } from '../fixtures/test-fixtures';

test.describe('Library', () => {
    test('should display library page', async ({ page }) => {
        await page.goto('/library');
        await expect(page.getByRole('heading', { name: 'Library' })).toBeVisible();
        await expect(page.getByText('Past chats')).toBeVisible();
    });

    test('should show empty state or list', async ({ page }) => {
        await page.goto('/library');
        const emptyState = page.getByText('No chats found');
        const list = page.getByTestId('chat-list');

        // Either empty state OR list must be visible
        const emptyVisible = await emptyState.isVisible();
        const listVisible = await list.isVisible();

        expect(emptyVisible || listVisible).toBeTruthy();
    });
});
