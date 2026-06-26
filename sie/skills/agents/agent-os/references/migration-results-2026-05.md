# hermes-workspace → agent-os Migration Results

**Date:** 2026-05-10
**Tool:** repo-transmute v2
**Source:** github.com/outsourc-e/hermes-workspace
**Target:** github.com/ChonSong/agent-os

## Summary

| Metric | Value |
|--------|-------|
| Components Extracted | 629 |
| Components Migrated | 36 |
| Total Size | 768KB |
| Success Rate | 100% (36/36) |

## Migrated Components

### Chat (10)
- `chat-screen.tsx` (84K) - Main chat with streaming, sessions, history
- `chat-composer.tsx` (115K) - Input with model picker, attachments, slash commands
- `chat-message-list.tsx` (72K) - Message rendering with streaming, tool calls
- `message-item.tsx` (94K) - Individual message with markdown, code blocks
- `chat-sidebar.tsx` (39K) - Session list with search, rename, delete
- `chat-header.tsx` (21K) - Session header with model info
- `chat-empty-state.tsx` (4.2K) - Welcome screen
- `context-bar.tsx` (7.0K) - Context indicator
- `message-status.tsx` (1.2K) - Message status display
- `message-timestamp.tsx` (1.3K) - Message timestamp

### Dashboard (8)
- `dashboard-screen.tsx` (39K) - Main dashboard with KPI cards
- `hero-metrics.tsx` (9.1K) - Hero metrics display
- `widget-shell.tsx` (2.8K) - Widget container
- `active-model-kpi.tsx` (5.3K) - Model KPI card
- `model-info-card.tsx` (14K) - Model info display
- `analytics-hero-card.tsx` (20K) - Analytics hero
- `analytics-summary-card.tsx` (3.8K) - Analytics summary
- `ops-strip.tsx` (8.8K) - Operations status strip

### MCP (3)
- `mcp-screen.tsx` (17K) - MCP server management
- `mcp-server-card.tsx` (9.8K) - Server card with actions
- `mcp-server-dialog.tsx` (14K) - Server config dialog

### Settings (3)
- `providers-screen.tsx` (57K) - LLM provider management
- `provider-wizard.tsx` (34K) - Provider setup wizard
- `provider-icon.tsx` (901B) - Provider icon

### Agents (5)
- `agents-screen.tsx` (3.7K) - Agent listing
- `operations-screen.tsx` (12K) - Operations dashboard
- `operations-agent-card.tsx` (17K) - Agent card with status
- `operations-agent-detail.tsx` (11K) - Agent detail view
- `orchestrator-card.tsx` (7.0K) - Orchestrator card

### UI (7)
- `switch.tsx` (3.3K) - Toggle switch
- `collapsible.tsx` (2.8K) - Collapsible panel
- `toast.tsx` (3.0K) - Toast notifications
- `dialog.tsx` (4.3K) - Dialog/modal
- `command.tsx` (13K) - Command palette
- `scroll-to-bottom-button.tsx` (1.7K) - Scroll control
- `research-card.tsx` (283B) - Research card stub

## Migration Conversions Applied

| Source | Target |
|--------|--------|
| `@tanstack/react-router` | `react-router-dom` or `window.location` |
| `@tanstack/react-query` | `useState`/`useEffect` + `fetch` |
| `@hugeicons/react` | `lucide-react` |
| `@base-ui/react/*` | Standalone React implementations |
| `'use client'` directives | Removed |
| Named exports | `export default` |
| Inline prop types | TypeScript interfaces |

## Integration Blockers

Migrated components cannot be directly dropped into agent-os because:

1. **Missing npm packages:** `recharts`, `motion/react` not in agent-os dependencies
2. **Missing internal modules:** hermes-workspace hooks/utils/types that don't exist in agent-os:
   - `@/screens/chat/hooks/*` (useChatMeasurements, useChatHistory, useSmoothStreamingText, etc.)
   - `@/screens/chat/chat-events`, `@/screens/chat/chat-queries`, `@/screens/chat/pending-send`
   - `@/screens/mcp/hooks/*` (useMcpCapabilityMode, useMcpServers, useMcpHub)
   - `@/screens/dashboard/lib/formatters`
   - `@/screens/gateway/lib/approvals-store`
3. **Complex state management:** hermes-workspace uses TanStack Query + Zustand stores that don't exist in agent-os
4. **Server-side rendering:** hermes-workspace uses TanStack Start (SSR) which agent-os doesn't support

## Path to Integration

To actually use these components in agent-os:

1. **Start small:** Integrate simple UI components first (switch, collapsible, dialog, toast)
2. **Install missing deps:** `npm install recharts motion`
3. **Create stub hooks:** For each missing internal module, create a stub that returns minimal data
4. **Replace complex state:** Convert TanStack Query patterns to useState/useEffect
5. **Test incrementally:** Verify each component compiles before moving to the next
