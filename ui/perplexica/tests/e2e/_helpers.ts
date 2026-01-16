import fs from 'fs';
import path from 'path';

/**
 * E2E Test Helpers
 * 
 * Utility functions for E2E tests including artifact management,
 * error signature detection, and response snapshots.
 */

/**
 * Returns the artifacts directory path and creates it if needed.
 */
export function artifactsDir(): string {
    const dir = path.resolve(process.cwd(), 'artifacts', 'e2e_contract');
    fs.mkdirSync(dir, { recursive: true });
    return dir;
}

/**
 * Saves a snapshot of test data for contract analysis.
 */
export function saveSnapshot(name: string, content: unknown): string {
    const dir = artifactsDir();
    const filePath = path.join(dir, name);
    const data = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
    fs.writeFileSync(filePath, data, 'utf8');
    return filePath;
}

/**
 * Error signatures that indicate backend problems.
 * If any of these appear in responses, the test should fail.
 */
const ERROR_SIGNATURES = [
    'Traceback',
    'ModuleNotFoundError',
    'ImportError',
    'Unhandled',
    'Exception',
    'ERROR:',
    'Internal Server Error',
    'CUDA out of memory',
    'NoneType',
    'KeyError',
    'AttributeError',
    'TypeError',
    'ValueError',
];

/**
 * Asserts that the text contains no error signatures.
 * Throws an error with details if a signature is found.
 */
export function assertNoErrorSignatures(text: string): void {
    for (const sig of ERROR_SIGNATURES) {
        if (text.includes(sig)) {
            // Extract context around the error
            const idx = text.indexOf(sig);
            const start = Math.max(0, idx - 50);
            const end = Math.min(text.length, idx + sig.length + 100);
            const context = text.slice(start, end);
            throw new Error(`Error signature detected: "${sig}"\nContext: ...${context}...`);
        }
    }
}

/**
 * Model configuration for tests.
 * Uses the models configured in the stack.
 */
export const TEST_MODELS = {
    chat: {
        providerId: 'ollama',
        key: 'qwen3:8b',
    },
    embedding: {
        providerId: 'ollama',
        key: 'dengcao/Qwen3-Embedding-8B:Q5_K_M',
    },
};

/**
 * Alternative model configuration (for A/B testing).
 */
export const TEST_MODELS_ALT = {
    chat: {
        providerId: 'ollama',
        key: 'qwen2.5:7b-instruct',
    },
    embedding: {
        providerId: 'ollama',
        key: 'nomic-embed-text:latest',
    },
};

/**
 * Extracts answer/message from a search response.
 * Handles various field name conventions.
 */
export function extractAnswer(json: Record<string, unknown>): string {
    return (
        (json.answer as string) ??
        (json.message as string) ??
        (json.response as string) ??
        (json.result as string) ??
        ''
    );
}

/**
 * Extracts sources array from a search response.
 * Handles various field name conventions.
 */
export function extractSources(json: Record<string, unknown>): unknown[] {
    return (
        (json.sources as unknown[]) ??
        (json.results as unknown[]) ??
        (json.documents as unknown[]) ??
        ((json.data as Record<string, unknown>)?.sources as unknown[]) ??
        []
    );
}

/**
 * Parses SSE stream text into data events.
 */
export function parseSSEEvents(text: string): string[] {
    return text
        .split('\n')
        .filter((line) => line.startsWith('data:'))
        .map((line) => line.replace(/^data:\s*/, '').trim())
        .filter(Boolean);
}

/**
 * Assembles content from SSE events or raw text.
 */
export function assembleStreamContent(text: string): string {
    const events = parseSSEEvents(text);
    if (events.length > 0) {
        // Try to parse JSON events and extract content
        const contents: string[] = [];
        for (const evt of events) {
            try {
                const parsed = JSON.parse(evt);
                if (parsed.data) contents.push(String(parsed.data));
                if (parsed.content) contents.push(String(parsed.content));
                if (parsed.delta) contents.push(String(parsed.delta));
            } catch {
                // Not JSON, use raw
                contents.push(evt);
            }
        }
        return contents.join('');
    }
    return text;
}
