import { mkdirSync, readFileSync, writeFileSync, openSync, closeSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const dataDir = join(__dirname, '..', 'data');
const configPath = join(dataDir, 'config.json');
const dbPath = join(dataDir, 'db.sqlite');

const defaultConfig = {
  version: 1,
  setupComplete: false,
  preferences: {},
  personalization: {},
  modelProviders: [],
  search: {
    searxngURL: '',
  },
};

mkdirSync(dataDir, { recursive: true });

let existingConfig;
try {
  existingConfig = readFileSync(configPath, 'utf8');
} catch {
  existingConfig = null;
}

if (!existingConfig) {
  writeFileSync(configPath, `${JSON.stringify(defaultConfig)}\n`, 'utf8');
}

try {
  const fd = openSync(dbPath, 'a');
  closeSync(fd);
} catch (error) {
  throw new Error(`Failed to ensure sqlite file at ${dbPath}: ${error instanceof Error ? error.message : String(error)}`);
}
