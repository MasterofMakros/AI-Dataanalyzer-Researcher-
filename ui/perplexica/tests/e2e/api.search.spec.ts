import { test, expect } from '@playwright/test';

/**
 * Perplexica API E2E Tests - Search Endpoint
 * 
 * Tests the /api/search endpoint with non-streaming responses.
 * Validates schema, response content, and error handling.
 */

const CHAT_MODEL = { providerId: 'ollama', key: 'qwen3:8b' };
const EMB_MODEL = { providerId: 'ollama', key: 'dengcao/Qwen3-Embedding-8B:Q5_K_M' };

test.describe('API /api/search', () => {
    test('returns results for valid query (non-stream)', async ({ request, baseURL }) => {
        const res = await request.post(`${baseURL}/api/search`, {
            data: {
                query: 'Was ist künstliche Intelligenz?',
                sources: ['web'],
                optimizationMode: 'speed',
                stream: false,
                chatModel: CHAT_MODEL,
                embeddingModel: EMB_MODEL,
                history: [],
            },
            timeout: 120000, // 2 min for LLM response
        });

        expect(res.status()).toBe(200);
        const json = await res.json();

        // Schema validation
        expect(json).toBeTruthy();
        expect(typeof json).toBe('object');

        // Response should contain either message/answer or sources
        const responseText = JSON.stringify(json);
        expect(responseText.length).toBeGreaterThan(100);
    });

    test('returns 400 for missing query', async ({ request, baseURL }) => {
        const res = await request.post(`${baseURL}/api/search`, {
            data: {
                sources: ['web'],
                optimizationMode: 'speed',
                stream: false,
                chatModel: CHAT_MODEL,
                embeddingModel: EMB_MODEL,
                history: [],
            },
        });

        expect(res.status()).toBe(400);
    });

    test('returns 400 for missing sources', async ({ request, baseURL }) => {
        const res = await request.post(`${baseURL}/api/search`, {
            data: {
                query: 'Test query',
                optimizationMode: 'speed',
                stream: false,
                chatModel: CHAT_MODEL,
                embeddingModel: EMB_MODEL,
                history: [],
            },
        });

        expect(res.status()).toBe(400);
    });
});
