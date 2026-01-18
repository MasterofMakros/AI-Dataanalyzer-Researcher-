import { type Page, type Locator, expect } from '@playwright/test';

export class ChatPage {
    readonly page: Page;
    readonly messageInput: Locator;
    readonly sendButton: Locator;
    readonly assistantSteps: Locator;
    readonly streamingIndicator: Locator;
    readonly resultItem: Locator;

    constructor(page: Page) {
        this.page = page;
        this.messageInput = page.getByPlaceholder('Ask anything...');
        this.sendButton = page.locator('button[type="submit"]'); // Adjust selector as needed
        this.assistantSteps = page.getByTestId('assistant-steps');
        this.streamingIndicator = page.getByTestId('streaming-indicator');
        this.resultItem = page.getByTestId('result-item');
    }

    async goto() {
        await this.page.goto('/');
    }

    async search(query: string) {
        await this.messageInput.fill(query);
        await this.messageInput.press('Enter');
    }

    async waitForResponse() {
        // Wait for either the streaming indicator (brainstorming), steps, or result
        await Promise.race([
            this.streamingIndicator.waitFor({ state: 'visible', timeout: 5000 }).catch(() => { }),
            this.assistantSteps.waitFor({ state: 'visible', timeout: 30000 }).catch(() => { }),
            this.resultItem.first().waitFor({ state: 'visible', timeout: 60000 }).catch(() => { })
        ]);

        // Then wait for something substantial
        try {
            await this.assistantSteps.waitFor({ state: 'visible', timeout: 10000 });
            // If steps visible, wait for them to potentially finish or just exist
        } catch (e) {
            // If no steps, maybe direct answer
            await this.resultItem.first().waitFor({ state: 'visible', timeout: 120000 });
        }
    }
}
