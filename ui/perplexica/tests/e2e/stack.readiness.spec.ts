import { test, expect } from '@playwright/test';

/**
 * Stack Readiness Tests
 * 
 * Gate tests that must pass before other E2E tests run.
 * Validates all required services are up and responding.
 */

test.describe('Stack Readiness', () => {
    test('Perplexica UI is accessible', async ({ request, baseURL }) => {
        const res = await request.get(baseURL!, { timeout: 10000 });
        expect(res.status()).toBe(200);
    });

    test('Perplexica API providers endpoint responds', async ({ request, baseURL }) => {
        const res = await request.get(`${baseURL}/api/providers`, { timeout: 10000 });
        expect(res.status()).toBe(200);
    });

    test('Ollama is accessible and has models', async ({ request }) => {
        const res = await request.get('http://localhost:11435/api/tags', { timeout: 10000 });
        expect(res.status()).toBe(200);

        const json = await res.json();
        expect(json.models).toBeTruthy();
        expect(json.models.length).toBeGreaterThan(0);

        // Verify required models exist
        const modelNames = json.models.map((m: any) => m.name);
        const hasQwen = modelNames.some((n: string) => n.includes('qwen'));
        expect(hasQwen).toBeTruthy();
    });

    test('Qdrant is accessible', async ({ request }) => {
        const res = await request.get('http://localhost:6333/collections', { timeout: 10000 });
        expect(res.status()).toBe(200);
    });

    test('Tika is accessible', async ({ request }) => {
        const res = await request.get('http://localhost:9998/tika', { timeout: 10000 });
        expect(res.status()).toBe(200);
    });
});
