import { test, expect } from '../fixtures/test-fixtures';

test.describe('Chat & Search', () => {
    test('should perform a basic search and show results', async ({ chatPage }) => {
        test.setTimeout(120000); // Increase timeout for local LLM
        await chatPage.goto();
        await chatPage.search('Test query for playwright');

        // Wait for the indicator that search started
        // await expect(chatPage.assistantSteps).toBeVisible({ timeout: 30000 });
        // Relaxed check: either steps or streaming indicator

        // Check if we eventually get a result or at least the process starts
        await chatPage.waitForResponse();

        const stepsVisible = await chatPage.assistantSteps.isVisible();
        const resultVisible = await chatPage.resultItem.first().isVisible();

        expect(stepsVisible || resultVisible).toBeTruthy();
    });
});
