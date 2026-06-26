# Q&A Design Walk — Session Examples

## Repo Consolidation (May 13, 2026)
Session: hermes-web-computer research. Goal: reach shared understanding of repo consolidation plan.

### Q1: Archive hermes-computer-planning?
**Context:** Planning repo had 4 docs across commits — ANALYSIS-README.md (original 4-repo analysis), completion-plan.md (473 lines, P0/P1/P2 priorities), APPLICATION-PLAN.md (322 lines, 12 migration candidates), ONE-WEBSITE.md (189 lines). Repo also had main branch in bad state (deleted files in working tree).
**Answer:** Migrate docs to hermes-web-computer/docs/archive-source/ first, then archive as git branch (not deletion). Preserve all history.
**Resolution:** ✓ User accepted

### Q2: Keep hermes-web-computer + agent-os merged or separate?
**Context:** Two repos with overlapping purpose. agent-os is production (Cloudflare tunnel, real users). HWC is active dev (Go+Svelte5, 30% done). Transpilation strategy (agent-os features → HWC components) was already identified.
**Answer:** Separate repos — different deployment cadences (production vs dev), different stacks (Node/React vs Go/Svelte5), different CI pipelines. Merging risks production disruption on every dev push.
**Resolution:** ⏳ Pending user confirmation

### Key finding surfaced during Q1:
hermes-computer-planning had more content than initially apparent (4 docs, not 1). The archive branch was created empty (missing commits from main). All deleted files had to be recovered via `git show <commit>:<filename>` before migration. Lesson: always `git log --all --oneline` to see full commit history before assuming repo state.

### Transpilation strategy (pre-decided, Q2 context):
- Dash* components: already ported to HWC
- Sessions/profiles/skills/config: need Svelte port
- Cron/MCP: need Go backend rebuild
- Terminal/chat: replaced by HWC's WS approach

### Next questions (unasked):
- Q3: MVP v1 scope ranking (which tiles ship first vs deferred)
- Q4: Next feature to implement after transpilation is done
- Q5: Uncommitted Dockerfile — examine or discard