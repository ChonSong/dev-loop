# SUPERSEDED — See `references/sessions-i18n-crash-2026-05-07.md`

This file contained incorrect hypotheses (`.clear()` on gatewayClient, `t.common.clear` in dependency arrays). The actual root causes were:

1. Missing `I18nContext.Provider` → `t = {}` everywhere
2. `getModelName(null)` returned `""` → `"" || Proxy.split()` threw
3. `ChatSidebar.info.model` is an object → `.split()` on non-string

Full analysis at `references/sessions-i18n-crash-2026-05-07.md`.
