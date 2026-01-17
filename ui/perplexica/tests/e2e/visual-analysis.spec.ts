import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

test('analyze search result ui density', async ({ page }) => {
    // 1. Navigate to Perplexica
    await page.goto('http://localhost:3100');

    // 2. Perform a search
    // Wait for input to be ready
    const input = page.locator('textarea[placeholder*="Ask"]');
    await input.waitFor();
    await input.fill('Summarize the history of artificial intelligence in 50 words');
    await page.keyboard.press('Enter');

    // 3. Wait for the answer to start streaming and complete
    // "sources" usually appear first, then answer. 
    // We wait for a specific element that signifies "Done" or just a stable state.
    // In Perplexica, the answer streams. We'll wait for a reasonable timeout or a specific "finished" signal if known.
    // For analysis, waiting for text to appear is enough.
    await page.waitForTimeout(10000); // Wait 10s for generation

    // 4. Capture Full Page Screenshot
    const screenshotPath = path.join(__dirname, 'analysis-screenshot.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`Screenshot saved to ${screenshotPath}`);

    // 5. Analyze "Message" Component Structure
    // Assuming the answer is inside a specific container. Based on file list, likely related to MessageBox.
    // We'll dump the text content and some class names to see structure.

    // Try to locate the main message area. 
    // Common selector might be something generic if we don't know the exact class.
    // We'll grab the last message which should be the assistant's answer.
    const messages = page.locator('.prose'); // Tailwind typography class often used for answers
    const count = await messages.count();

    if (count > 0) {
        const lastMessage = messages.last();
        const html = await lastMessage.innerHTML();
        const text = await lastMessage.innerText();

        const analysisData = {
            htmlLength: html.length,
            textLength: text.length,
            elementDensity: (html.match(/<[^>]+>/g) || []).length, // Rough tag count
            structureSnapshot: html.substring(0, 2000) // First 2000 chars of HTML
        };

        const analysisPath = path.join(__dirname, 'ui-analysis.json');
        fs.writeFileSync(analysisPath, JSON.stringify(analysisData, null, 2));
        console.log(`Analysis data saved to ${analysisPath}`);
    } else {
        console.log("Could not find message container (.prose or similar)");
        // Dump body if specific selector fails
        const bodyHtml = await page.content();
        const debugPath = path.join(__dirname, 'debug-body.html');
        fs.writeFileSync(debugPath, bodyHtml);
    }
});
