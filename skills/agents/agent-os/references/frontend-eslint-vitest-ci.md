# eslint + vitest CI Fixes (2026-05-05/07)

## Common ESLint Errors in This Project

**`error TS1117: An object literal cannot have multiple properties with the same name`**
ESLint catches duplicate keys that TypeScript's `tsc --noEmit` may miss in certain configurations. This happens when the same key appears twice in an object literal (e.g., two `"0 10 * * 1"` entries in a schedule map). ESLint reports `Parsing error: Property assignment expected` at the line of the second occurrence. TypeScript reports `TS2741: Property 'rating' is missing` because the duplicate silently drops the second property, making its value unavailable.

Fix: Find and remove the duplicate key in the object literal.

**`npm run lint` catches what `tsc --noEmit` misses:** ESLint runs separately in CI and can fail even when TypeScript compiles clean. Always run `cd apps/dashboard/frontend && npx --yes eslint src --ext ts,tsx` locally before pushing.

## eslint (ESLint v9 Flat Config)

The frontend had no `eslint.config.js`. CI Lint step failed with `Cannot find package '@eslint/js'`.

### Create `apps/dashboard/frontend/eslint.config.js`

```javascript
import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parserOptions: {
        project: './tsconfig.json',
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/no-explicit-any': 'off',
      'no-console': 'off',
      'react-hooks/exhaustive-deps': 'off',
      'no-empty': 'warn',
    },
  },
];
```

### Install dev deps
```bash
cd apps/dashboard/frontend
npm install --save-dev eslint @eslint/js typescript-eslint
```

### Fix stale eslint-disable comments
Remove `// eslint-disable-next-line react-hooks/exhaustive-deps` from:
- `src/components/ChatSidebar.tsx`
- `src/components/ModelPickerDialog.tsx`
- `src/components/OAuthLoginModal.tsx`

### Verify
```bash
npx eslint apps/dashboard/frontend/src --ext ts,tsx
# Expect: 0 errors (warnings OK)
```

## vitest --passWithNoTests

Packages with no test files: frontend, backend, shared-types. vitest exits 1 without `--passWithNoTests`.

Add to all three package.json scripts:
```json
"test": "vitest --passWithNoTests"
```

## CI mypy --config-file flag

When running `mypy packages/` from repo root, mypy auto-discovers `pyproject.toml`. But if CI ever CDs into a subdirectory, it won't find config. Always use:
```bash
mypy packages/ --config-file=pyproject.toml
```

## npm omit=dev environment issue

Local hermes container had `npm config omit=dev` set, causing dev dependencies to be skipped even with `npm ci`. This meant vitest wasn't installed locally. Fix:
```bash
npm config set omit ""
unset NODE_ENV
npm ci --include=dev
```
CI does NOT have this issue — `npm ci` in CI installs devDeps by default.
