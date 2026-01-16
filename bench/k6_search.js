import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

/**
 * k6 Benchmark for Perplexica /api/search endpoint
 * 
 * Run: k6 run --env BASE_URL=http://localhost:3100 bench/k6_search.js
 */

// Custom metrics
const searchLatency = new Trend('search_latency');
const searchSuccess = new Rate('search_success');
const searchErrors = new Counter('search_errors');

export const options = {
    scenarios: {
        // Smoke test: 1 VU for 30s
        smoke: {
            executor: 'constant-vus',
            vus: 1,
            duration: '30s',
            gracefulStop: '5s',
        },
        // Load test: ramp up to 5 VUs
        // load: {
        //   executor: 'ramping-vus',
        //   startVUs: 1,
        //   stages: [
        //     { duration: '30s', target: 5 },
        //     { duration: '1m', target: 5 },
        //     { duration: '30s', target: 0 },
        //   ],
        // },
    },
    thresholds: {
        search_latency: ['p(50)<30000', 'p(95)<60000'], // p50 < 30s, p95 < 60s (LLM is slow)
        search_success: ['rate>0.9'], // 90%+ success rate
    },
};

const BASE = __ENV.BASE_URL || 'http://localhost:3100';

const CHAT_MODEL = { providerId: 'ollama', key: 'qwen3:8b' };
const EMB_MODEL = { providerId: 'ollama', key: 'dengcao/Qwen3-Embedding-8B:Q5_K_M' };

const QUERIES = [
    'Was ist künstliche Intelligenz?',
    'Erkläre Machine Learning in einem Satz.',
    'Nenne drei Vorteile von Python.',
    'Was ist ein Transformer-Modell?',
    'Beschreibe den Unterschied zwischen CPU und GPU.',
];

export default function () {
    const query = QUERIES[Math.floor(Math.random() * QUERIES.length)];

    const payload = JSON.stringify({
        query: query,
        sources: ['web'],
        optimizationMode: 'speed',
        stream: false,
        chatModel: CHAT_MODEL,
        embeddingModel: EMB_MODEL,
        history: [],
    });

    const startTime = Date.now();

    const res = http.post(`${BASE}/api/search`, payload, {
        headers: { 'Content-Type': 'application/json' },
        timeout: '120s',
    });

    const latency = Date.now() - startTime;
    searchLatency.add(latency);

    const success = check(res, {
        'status is 200': (r) => r.status === 200,
        'body not empty': (r) => r.body && r.body.length > 100,
        'no error in response': (r) => !r.body.includes('"error"'),
    });

    if (success) {
        searchSuccess.add(1);
    } else {
        searchSuccess.add(0);
        searchErrors.add(1);
        console.log(`Failed query: ${query}, status: ${res.status}`);
    }

    // Think time between requests (simulate real user)
    sleep(2 + Math.random() * 3);
}

export function handleSummary(data) {
    return {
        'stdout': textSummary(data, { indent: ' ', enableColors: true }),
        'bench/k6_results.json': JSON.stringify(data, null, 2),
    };
}

function textSummary(data, opts) {
    // Simple text summary
    const metrics = data.metrics;
    return `
=== k6 Benchmark Summary ===
Search Latency p50: ${metrics.search_latency?.values?.med?.toFixed(0) || 'N/A'} ms
Search Latency p95: ${metrics.search_latency?.values?.p95?.toFixed(0) || 'N/A'} ms
Success Rate: ${((metrics.search_success?.values?.rate || 0) * 100).toFixed(1)}%
Total Requests: ${metrics.http_reqs?.values?.count || 0}
`;
}
