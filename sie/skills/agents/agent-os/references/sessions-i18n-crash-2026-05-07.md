# Sessions / Chat / Cron Crash — Root Cause Analysis (2026-05-07)

## TL;DR — Three Separate Bugs in One Chain

1. **I18nContext had no Provider** → `t = {}` everywhere → `t.common.X = undefined` → crashes
2. **getModelName(null) returned ""** → `"" || Proxy → Proxy.split() → TypeError`
3. **ChatSidebar.info.model is an object** → `.split("/")` called on object → TypeError

## Bug 1 — I18nContext Missing Provider (Root of Sessions/Cron/Chat Crashes)

**Symptom**: `TypeError: Cannot read properties of undefined (reading 'clear')` or similar on Sessions, Chat, Cron. Containers/Files/Observability worked fine.

**Root Cause**: `I18nContext` in `src/i18n/context.tsx` had a default value of `t = {}` (empty object). **No `I18nContext.Provider` wrapped the app.** Every call to `useI18n()` got this empty `t`. So `t.common.clear`, `t.status.local`, `t.nav.sessions` — all `undefined`. Any code treating these as strings (`.split()`, `.length`, template literals) threw.

**Fix**: Rewrote `context.tsx` with a Proxy-based safe i18n factory. The Proxy intercepts any key access and returns a fallback string (e.g., `"clear"` for `t.common.clear`). This means `t.common.clear?.()` is safe and returns `undefined` (no crash), and `String(t.common.clear)` becomes `"undefined"` rather than throwing.

**Key code pattern**:
```typescript
// OLD (crashed):
const { t } = useI18n();
return <div>{t.common.sessions.split('/').pop()}</div>; // t.common.sessions = undefined → throws

// NEW (safe):
const { t } = useI18n(); // t is now a safe Proxy — missing keys return fallback strings
return <div>{t.common.sessions.split('/').pop()}</div>; // "sessions".split('/').pop() = "sessions"
```

## Bug 2 — getModelName(null) → Proxy Fallback → .split() Throws

**Symptom**: Even after fixing I18n, Sessions still crashed with `TypeError: split is not a function` at the `.split()` call.

**Root Cause**: `session.model` is an object `{provider: "openrouter", name: "anthropic/claude-3-5-sonnet"}`, NOT a string. Code doing `session.model.split('@')` called `.split()` on an object.

Further: `getModelName(null)` returned `""`. The expression `session.model?.name || "—" || t.common.unknown` evaluated to `"" || Proxy` due to short-circuit `||` — JavaScript's `||` returns the first truthy value, and `""` is falsy, so it returned the Proxy! Then `Proxy.split("/")` threw.

**Fix**:
```typescript
function getModelName(model: string | object | null): string {
  if (!model) return "—";
  if (typeof model === 'string') return model.split('@')[0];
  return (model as any).name || (model as any).id || '—';
}
```

And guard every `.split()` call: `(session.model?.split('/')[0] ?? '—')`

## Bug 3 — ChatSidebar.info.model → .split() on Object

**Symptom**: Chat page crashed with `split is not a function`.

**Root Cause**: `info.model` (from the chat session API) is also an object `{provider, name}`, not a string. Same `.split("/")` pattern on line 299 of `ChatSidebar.tsx`.

**Fix**: Replaced with `getModelName(info.model)` call.

## Files Changed

| File | Change |
|------|--------|
| `src/i18n/context.tsx` | Proxy-based safe i18n replacing `t = {}` default |
| `src/pages/SessionsPage.tsx` | `getModelName()` wrapper + `?? "—"` guards on `.split()` |
| `src/components/ChatSidebar.tsx` | `getModelName(info.model)` for model display |
| `src/App.tsx` | Removed incorrect `I18nContext.Provider` wrapper |

## Diagnostic Pattern for Similar Crashes

When React page crashes with `TypeError: X is not a function` or `Cannot read properties of undefined`:

1. Check if page uses `useI18n()` — if so, I18nContext is suspect #1
2. Find ALL `.split()` calls in the page source: `grep -n '\.split' SessionsPage.tsx`
3. For each `.split()`, identify what object/field it's called on and check the API response shape
4. Check `session.model`, `info.model`, `s.model` — these are commonly objects with `.name` or `.id` rather than strings

## Key Insight — Why It Was Hard to Find

- `browser_console` showed generic React error #31, not the actual TypeError
- The error stack was minified (production build)
- The crash happened in a different file (SessionsPage calling into i18n context)
- Three separate bugs stacked: missing Provider → Proxy fallback → Proxy.split() crash
