import { test, expect } from '@playwright/test';

/**
 * Perplexica API E2E Tests - Providers & Config
 * 
 * Tests provider availability and configuration endpoints.
 */

test.describe('API /api/providers', () => {
    test('returns list of providers including Ollama', async ({ request, baseURL }) => {
        const res = await request.get(`${baseURL}/api/providers`);
        expect(res.status()).toBe(200);

        const json = await res.json();
        expect(Array.isArray(json)).toBeTruthy();

        // Should contain at least one provider
        expect(json.length).toBeGreaterThan(0);

        // JSON should mention ollama somewhere
        const jsonStr = JSON.stringify(json).toLowerCase();
        expect(jsonStr).toContain('ollama');
    });
});

test.describe('API /api/config', () => {
    test('returns configuration object', async ({ request, baseURL }) => {
        const res = await request.get(`${baseURL}/api/config`);
        expect(res.status()).toBe(200);

        const json = await res.json();
        expect(json).toBeTruthy();
        expect(typeof json).toBe('object');
    });
});
