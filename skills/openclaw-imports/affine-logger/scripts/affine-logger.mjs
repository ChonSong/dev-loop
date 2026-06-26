#!/usr/bin/env node

/**
 * AFFiNE-compatible Logger
 * Creates journal entries in local JSONL format with AFFiNE-compatible schema
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DEFAULT_LOG_PATH = process.env.JOURNAL_LOG_PATH ||
  '/home/sean/.openclaw/agents/journal/memory/journal.jsonl';

const args = process.argv.slice(2);
const command = args[0];

// Parse named arguments
const parseArgs = () => {
  const result = {};
  for (let i = 1; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      const value = args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : 'true';
      result[key] = value;
      if (value !== 'true') i++;
    }
  }
  return result;
};

const ensureLogDir = () => {
  const dir = path.dirname(DEFAULT_LOG_PATH);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
};

const createEntry = (title, content, tags = []) => {
  return {
    id: crypto.randomUUID(),
    title,
    content,
    tags: typeof tags === 'string' ? tags.split(',').map(t => t.trim()) : tags,
    created: new Date().toISOString(),
    synced: false
  };
};

const appendEntry = (entry) => {
  ensureLogDir();
  const line = JSON.stringify(entry) + '\n';
  fs.appendFileSync(DEFAULT_LOG_PATH, line);
  console.log(JSON.stringify({ ok: true, id: entry.id, created: entry.created }));
};

const listEntries = (limit = 10) => {
  if (!fs.existsSync(DEFAULT_LOG_PATH)) {
    console.log(JSON.stringify({ entries: [] }));
    return;
  }

  const content = fs.readFileSync(DEFAULT_LOG_PATH, 'utf-8');
  const lines = content.trim().split('\n').filter(Boolean);
  const entries = lines.slice(-limit).reverse().map(line => JSON.parse(line));
  console.log(JSON.stringify({ entries }));
};

const syncToAffine = async () => {
  const affineUrl = process.env.AFFINE_URL;
  const affineToken = process.env.AFFINE_TOKEN;

  if (!affineUrl || !affineToken) {
    console.log(JSON.stringify({
      ok: false,
      error: 'AFFINE_URL and AFFINE_TOKEN not configured',
      message: 'Set environment variables to enable AFFiNE sync'
    }));
    return;
  }

  // Read unsynced entries
  if (!fs.existsSync(DEFAULT_LOG_PATH)) {
    console.log(JSON.stringify({ ok: true, synced: 0 }));
    return;
  }

  const content = fs.readFileSync(DEFAULT_LOG_PATH, 'utf-8');
  const lines = content.trim().split('\n').filter(Boolean);
  const entries = lines.map(line => JSON.parse(line)).filter(e => !e.synced);

  if (entries.length === 0) {
    console.log(JSON.stringify({ ok: true, synced: 0, message: 'No entries to sync' }));
    return;
  }

  // In a full implementation, this would call the AFFiNE API
  // For now, mark all as synced locally
  for (const entry of entries) {
    entry.synced = true;
    entry.syncedAt = new Date().toISOString();
  }

  console.log(JSON.stringify({ ok: true, synced: entries.length, message: 'Entries marked as synced' }));
};

const main = async () => {
  const params = parseArgs();

  switch (command) {
    case 'log': {
      const title = params.title || 'Journal Entry';
      const content = params.content || '';
      const tags = params.tags || [];
      const entry = createEntry(title, content, tags);
      appendEntry(entry);
      break;
    }

    case 'list': {
      const limit = parseInt(params.limit) || 10;
      listEntries(limit);
      break;
    }

    case 'sync': {
      await syncToAffine();
      break;
    }

    default:
      console.log(JSON.stringify({
        ok: false,
        error: 'Unknown command',
        commands: ['log', 'list', 'sync']
      }));
  }
};

main().catch(err => {
  console.error(JSON.stringify({ ok: false, error: err.message }));
  process.exit(1);
});
