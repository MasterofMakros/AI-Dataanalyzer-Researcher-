import { test, expect } from '@playwright/test';

/**
 * Perplexica API E2E Tests - Chat Endpoint (Streaming)
 * 
 * Tests the /api/chat endpoint with streaming responses.
 */

const CHAT_MODEL = { providerId: 'ollama', key: 'qwen3:8b' };
const EMB_MODEL = { providerId: 'ollama', key: 'dengcao/Qwen3-Embedding-8B:Q5_K_M' };

test.describe('API /api/chat (Streaming)', () => {
    test('streams response for valid message', async ({ request, baseURL }) => {
        const chatId = crypto.randomUUID();
        const messageId = crypto.randomUUID();

        const res = await request.post(`${baseURL}/api/chat`, {
            data: {
                message: {
                    messageId,
                    chatId,
                    content: 'Antworte nur mit dem Wort: STREAM_OK',
                },
                optimizationMode: 'speed',
                sources: ['web'],
                history: [],
                files: [],
                chatModel: CHAT_MODEL,
                embeddingModel: EMB_MODEL,
            },
            timeout: 120000,
        });

        expect(res.status()).toBe(200);

        const headers = res.headers();
        // Streaming response should have event-stream or similar content type
        expect(headers['content-type']).toBeTruthy();

        const body = await res.text();

        // Streaming response should contain data
        expect(body.length).toBeGreaterThan(50);

        // Should contain streaming markers or response content
        expect(body).toMatch(/type|data|block|response|STREAM_OK/i);
    });

    test('returns 400 for empty message content', async ({ request, baseURL }) => {
        const res = await request.post(`${baseURL}/api/chat`, {
            data: {
                message: {
                    messageId: crypto.randomUUID(),
                    chatId: crypto.randomUUID(),
                    content: '',
                },
                optimizationMode: 'speed',
                sources: ['web'],
                history: [],
                files: [],
                chatModel: CHAT_MODEL,
                embeddingModel: EMB_MODEL,
            },
        });

        expect(res.status()).toBe(400);
    });

    test('returns 400 for missing message', async ({ request, baseURL }) => {
        const res = await request.post(`${baseURL}/api/chat`, {
            data: {
                optimizationMode: 'speed',
                sources: ['web'],
                history: [],
                files: [],
                chatModel: CHAT_MODEL,
                embeddingModel: EMB_MODEL,
            },
        });

        expect(res.status()).toBe(400);
    });
});
