import { test as base } from '@playwright/test';
import { ChatPage } from '../page-objects/ChatPage';

type MyFixtures = {
    chatPage: ChatPage;
};

export const test = base.extend<MyFixtures>({
    chatPage: async ({ page }, use) => {
        const chatPage = new ChatPage(page);
        await use(chatPage);
    },
});

export { expect } from '@playwright/test';
