import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

async function checkService(name: string, url: string, healthPath: string = '') {
    const start = Date.now();
    try {
        const target = `${url}${healthPath}`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3s timeout

        const res = await fetch(target, {
            method: 'GET',
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        const latency = Date.now() - start;

        if (res.ok) {
            return { name, status: 'online', latency, url };
        } else {
            return { name, status: 'error', latency, code: res.status, url };
        }
    } catch (err: any) {
        return { name, status: 'offline', latency: Date.now() - start, error: err.message, url };
    }
}

export async function GET() {
    // Get ENV vars with fallbacks
    const ollamaUrl = process.env.OLLAMA_BASE_URL || 'http://host.docker.internal:11434';
    const qdrantUrl = process.env.QDRANT_URL || 'http://host.docker.internal:6333';
    const searxngUrl = process.env.SEARXNG_API_URL || 'http://localhost:8080';
    const apiUrl = process.env.NEURAL_VAULT_API_URL || 'http://host.docker.internal:8000';

    const results = await Promise.all([
        checkService('Ollama', ollamaUrl, '/api/tags'),
        checkService('Qdrant', qdrantUrl, '/healthz'),
        checkService('SearXNG', searxngUrl, '/config'), // or just root /
        checkService('Neural Vault API', apiUrl, '/health'),
    ]);

    const systemStatus = {
        timestamp: new Date().toISOString(),
        services: results
    };

    return NextResponse.json(systemStatus);
}
