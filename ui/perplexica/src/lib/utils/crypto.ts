/**
 * Isomorphic crypto utility for UUID generation
 * Works both in browser (window.crypto) and Node.js (crypto module)
 */

// Check if running in browser or Node.js
const isBrowser = typeof window !== 'undefined' && typeof window.crypto !== 'undefined';

let nodeCrypto: typeof import('crypto') | null = null;

if (!isBrowser) {
    try {
        // Dynamically import Node.js crypto only on server-side
        nodeCrypto = require('crypto');
    } catch (e) {
        console.error('Failed to load Node.js crypto module:', e);
    }
}

/**
 * Generate a random UUID
 * Uses window.crypto.randomUUID() in browser, crypto.randomUUID() in Node.js
 */
export function randomUUID(): string {
    if (isBrowser) {
        return window.crypto.randomUUID();
    } else if (nodeCrypto) {
        return nodeCrypto.randomUUID();
    } else {
        throw new Error('No crypto implementation available');
    }
}

/**
 * Generate random bytes as hex string (Node.js only)
 * This is primarily for backwards compatibility with server-side code
 */
export function randomBytes(length: number): string {
    if (!isBrowser && nodeCrypto) {
        return nodeCrypto.randomBytes(length).toString('hex');
    } else {
        // Fallback for browser: use randomUUID (not exact replacement but sufficient for IDs)
        return randomUUID().replace(/-/g, '').substring(0, length * 2);
    }
}
