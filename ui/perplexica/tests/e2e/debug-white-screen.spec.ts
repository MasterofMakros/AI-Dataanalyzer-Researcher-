import { test, expect } from '@playwright/test';

/**
 * Debug Test: Capture White Screen Client-Side Exception
 * 
 * This test navigates to Perplexica and captures all browser console logs,
 * errors, and failed network requests to diagnose the "Application error" crash.
 */
test.describe('White Screen Error Debugging', () => {
    let consoleMessages: string[] = [];
    let consoleErrors: string[] = [];
    let failedRequests: string[] = [];

    test.beforeEach(async ({ page }) => {
        // Capture console logs
        page.on('console', (msg) => {
            const text = `[${msg.type()}] ${msg.text()}`;
            consoleMessages.push(text);
            if (msg.type() === 'error') {
                consoleErrors.push(text);
            }
        });

        // Capture page errors (uncaught exceptions)
        page.on('pageerror', (error) => {
            consoleErrors.push(`[PAGE ERROR] ${error.message}\n${error.stack}`);
        });

        // Capture failed requests
        page.on('requestfailed', (request) => {
            failedRequests.push(`${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
        });
    });

    test('should load homepage without client-side exception', async ({ page }) => {
        console.log('\\n======= Starting Perplexica Load Test =======');

        // Navigate to Perplexica
        const response = await page.goto('http://localhost:3100', {
            waitUntil: 'networkidle',
            timeout: 30000
        });

        console.log(`\\n--- HTTP Response ---`);
        console.log(`Status: ${response?.status()}`);
        console.log(`Headers: ${JSON.stringify(await response?.allHeaders(), null, 2)}`);

        // Wait a bit for any async errors to surface
        await page.waitForTimeout(3000);

        console.log(`\\n--- Console Messages (${consoleMessages.length}) ---`);
        consoleMessages.forEach(msg => console.log(msg));

        console.log(`\\n--- Console Errors (${consoleErrors.length}) ---`);
        consoleErrors.forEach(err => console.log(err));

        console.log(`\\n--- Failed Requests (${failedRequests.length}) ---`);
        failedRequests.forEach(req => console.log(req));

        // Check for the error screen
        const errorText = await page.textContent('body').catch(() => '');
        console.log(`\\n--- Page Body Text ---`);
        console.log(errorText?.substring(0, 500));

        // Capture screenshot
        await page.screenshot({ path: 'ui/perplexica/artifacts/e2e_contract/white_screen_error.png', fullPage: true });
        console.log('\\nScreenshot saved to: ui/perplexica/artifacts/e2e_contract/white_screen_error.png');

        // Assertions
        expect(consoleErrors.length, 'Should have no console errors').toBe(0);
        expect(errorText).not.toContain('Application error: a client-side exception');
    });

    test('should capture initial data fetching errors', async ({ page }) => {
        console.log('\\n======= Testing Initial Data Load =======');

        // Monitor all API calls
        const apiCalls: { url: string; status: number; response: any }[] = [];

        page.on('response', async (response) => {
            const url = response.url();
            if (url.includes('/api/')) {
                try {
                    const body = await response.text();
                    apiCalls.push({
                        url,
                        status: response.status(),
                        response: body.substring(0, 200)
                    });
                } catch (e) {
                    apiCalls.push({
                        url,
                        status: response.status(),
                        response: 'Could not read response body'
                    });
                }
            }
        });

        await page.goto('http://localhost:3100', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);

        console.log(`\\n--- API Calls (${apiCalls.length}) ---`);
        apiCalls.forEach(call => {
            console.log(`${call.status} ${call.url}`);
            console.log(`Response: ${call.response}\\n`);
        });

        // Check for 500 errors
        const failedApiCalls = apiCalls.filter(call => call.status >= 400);
        expect(failedApiCalls.length, `No failed API calls. Failed: ${JSON.stringify(failedApiCalls)}`).toBe(0);
    });
});
