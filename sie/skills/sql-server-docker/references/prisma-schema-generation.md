# SQL Server to Prisma Schema Generation

## Overview

Generate a Prisma schema with proper `@id`, `@relation`, and type mappings from a live SQL Server database.

## What it extracts

1. **Primary keys** — from `sys.indexes` + `sys.index_columns` where `is_primary_key = 1`
2. **Columns with types** — from `sys.columns` + `sys.types`, mapped to Prisma types
3. **Foreign keys** — from `sys.foreign_keys` + `sys.foreign_key_columns`, generating `@relation` fields

## Prisma 7.8 Config

```typescript
// prisma.config.ts
import path from 'path'
import { defineConfig } from 'prisma/config'

export default defineConfig({
  earlyAccess: true,
  schema: path.join(import.meta.dirname, 'prisma', 'schema.prisma'),
  datasource: {
    url: 'file:./data/onetag.db',
  },
})
```

Install adapter: `npm install prisma-adapter-sqlite` (NOT `@prisma/adapter-sqlite`).

## Starting Prisma Studio

```bash
export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH"
cd /workspace/project
npx prisma studio --port 8766
```

**Note:** Background sessions don't have `node`/`npx` in PATH. Use full paths or export PATH explicitly.