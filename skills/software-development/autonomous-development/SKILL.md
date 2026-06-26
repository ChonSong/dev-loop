---
name: autonomous-development
description: "Use when building features end-to-end from spec. Closed-loop: spec to subagent implementation to visual QA to CSS fix to commit. Screenshot-only reference. Autonomous iteration to greater-than-or-equal 85% similarity."
tags: ["autonomous", "spec-driven", "visual-qa", "subagent", "closed-loop"]
related_skills: ["subagent-driven-development", "writing-plans", "hermes-agent-skill-authoring"]
---

# Autonomous Development Pipeline

## Overview

A self-correcting **vision-driven** autonomous development workflow that iterates from **spec to verified commit** using component-level screenshot analysis. The pipeline uses a vision model to assess each UI region, extracts CSS inference from visual analysis, tracks backend impact per component, and self-heals through iterative fix loops.

## Core principle

**Every visual gap has a root cause in specific component code.** The pipeline must: (1) divide screenshots into regions, (2) use a vision model to assess each region against the reference, (3) infer exact CSS/structural changes from visual feedback, (4) assess backend impact, (5) iterate until quality gates pass.

**CRITICAL: Colors are NOT the primary signal.** User said: "im not concerned about colours but elements, functionality and functional use." Priority order:
1. **Element presence** - does the component exist in the right location?
2. **Functional interactions** - can the user interact with it as expected?
3. **Layout structure** - are panels, docks, tiles arranged correctly?
4. **Color** - only after elements/functionality are confirmed correct

## Key Integrations

**This skill REUSES existing code wherever possible:**

| From | Use | How |
|------|-----|-----|
| `repo-transmute-v2` | `ScreenshotDef`, `VisionResult`, component bounding box extraction | Wire into `extract/screenshot.py` + `models.py` |
| `repo-transmute-v2` | Self-healing migration loop (`engine.py`) | Adapt for visual QA iteration |
| `vision_analyze` (built-in) | Per-region visual comparison | Multi-region prompting with structured output |
| `taste-skill` | Anti-slop bias correction | Apply during Phase 2 implementation |
| `subagent-driven-development` | Parallel delegation strategy | Same pattern for independent components |

**Do NOT write parallel implementations where existing code exists.**

## When to Use

- Building a new feature from a reference screenshot or description
- Iterating on visual design (CSS tokens, colors, layout)
- Performing visual QA and repair on an existing UI
- Autonomous work that requires minimal human steering

**Do NOT use for:** Tasks that need human judgment on design intent (glassmorphism vs solid is a design decision). Use this when the reference is clear and the gap is mechanical (wrong color, wrong spacing, missing element).

## The Pipeline (7-Phase Closed Loop with Vision-Driven Self-Healing)

```
PHASE 1: VISION-DRIVEN SPEC + REGION EXTRACTION
  Reference screenshot -> Component bounding boxes
  -> Vision model: describe each region
  -> Infer CSS tokens from visual analysis
  -> Map regions to source files + backend impact

PHASE 2: SUBAGENT IMPLEMENTATION
  delegate_task to fresh subagent per component
  - Parallel tracks for independent components
  - Build verification removed from subagent scope
  - Direct execution fallback if subagent times out

PHASE 3: BUILD VERIFICATION
  - go build ./... (backend)
  - npm run build (frontend)
  - Fail fast -- do not proceed with broken build

PHASE 4: COMPONENT-LEVEL SCREENSHOT CAPTURE
  Uses repo-transmute `screenshot.py` Playwright pipeline
  - Capture full page + individual component screenshots
  - Extract bounding boxes via getBoundingClientRect()
  - Same viewport as reference (1920x960)

PHASE 5: VISION MODEL COMPARISON (not pixel-diff)
  For each region:
    vision_analyze(region_crop, "describe colors, spacing,
    typography, what's correct, what's wrong")
  -> Structured VisionResult per region
  -> Exact CSS inference from visual description
  -> Backend impact: which API routes does this touch?

PHASE 6: CSS REPAIR + BACKEND IMPACT
  - Collect all patches before rebuilding
  - Apply to correct source file (from Phase 1 mapping)
  - Note any backend API changes needed for CSS fixes
  - Single rebuild + rescreenshot

PHASE 7: GATE CHECK + SELF-HEALING ITERATION
  - If overall_score >= 85% -> commit and push
  - If < 85% -> feed VisionResult.issues back into Phase 5
    (self-healing loop: re-ask vision model with context)
  - Max 3 iterations -> escalate with gap list
```

## Phase 5: Visual Comparison

### NOT Pixel-Diff

Pixel-diff (PIL `ImageChops.difference`) produces misleading scores (reported 81.9% vs human 5%). Instead, extract CSS tokens from both images and compare per-region.

### Perceptual Color Comparison (OKLab Delta-E)

```python
def oklab_delta(rgb1, rgb2):
    """Perceptual color difference. Delta-E < 1 = imperceptible, > 10 = obvious."""
    # Convert RGB to OKLab, compute Euclidean distance
    ...
```

### Focus on Elements and Functionality, Not Colors

**The user has explicitly stated: "im not concerned about colours but elements, functionality and functional use."**

For each screenshot region, the vision model should describe:
1. **What elements are present** (panels, docks, windows, buttons, inputs)
2. **What interactions are possible** (click, type, drag, keyboard shortcuts)
3. **Layout structure** (how elements are arranged spatially)
4. **Color** - only if it affects readability or visual hierarchy

Color matching (Delta-E) is a secondary check, not the primary signal. A region that matches the reference's elements but has slightly wrong colors is preferable to a region with correct colors but missing elements.

## Phase 2: Subagent Implementation

### Subagent Timeout Recovery

**After any subagent timeout on code task:**
```bash
# Check what was actually committed before re-implementing
git status --short
git diff --stat
grep -rn "feature_keyword" relevant_files/
```

## Design Taste Integration

### Anti-Slop Rules (apply during Phase 2)
- bg-white/5 -> bg-[#12121a]/80 (use exact dark tokens)
- text-purple-400 -> text-[#a78bfa] (match accent from spec)
- rounded-xl -> rounded-2xl (16px for floating panels)
- shadow-md -> shadow-[0_8px_32px_rgba(0,0,0,0.4)] (diffused panel shadow)
- Emojis -> SVG icons (no emoji in code)

### Color Consistency
- One base palette per project (do not mix warm/cool grays)
- Max 1 accent color, saturation less than 80%
- No neon gradients, no purple glows unless spec'd

### Typography Defaults
- Headers: tracking-tight leading-none
- Body: text-gray-400 leading-relaxed
- Mono: JetBrains Mono

## Common Pitfalls

1. **Wrong comparison method**: Pixel-diff produces meaningless scores. Always extract CSS tokens per-region and compute perceptual distance.

2. **Iterating screenshot per patch**: Collect ALL patches -> Apply all -> Rebuild once -> Screenshot once. Iterating per-patch wastes 10x time.

3. **Building on broken code**: Verify builds (Phase 3) before visual QA. QA on broken code is meaningless.

4. **Missing JS render time**: Svelte/React/Vue need 60s virtual-time-budget. Without it, screenshots show white/blank -- JS never executes.

5. **Reference is wrong app**: Before comparing, confirm the reference shows the SAME application type.

6. **Subagent timeouts on hermes-web-computer**: Build steps (npm run build, go build) cause subagent timeouts. Remove build verification from subagent instructions. Do builds yourself in controller session.

7. **SCP timeout on large images**: Use SSH heredoc instead of scp for image file transfers.

8. **vision_analyze cannot access /tmp from execute_code**: vision_analyze only works from agent runtime or subagents with `toolsets: ["vision"]`. If you need to analyze a local file, use `delegate_task` with vision toolset, not execute_code. See `references/vision-analyze-file-handling.md`.

9. **Documentation task delegation — don't trust the summary**: Subagents report "wrote file" but files may not exist at the expected path. Always verify with `git status --short` after documentation subagent tasks. See `references/documentation-task-delegation.md`.

10. **Subagent timeout ≠ work lost**: When a subagent times out, DO NOT immediately re-delegate. Check `git diff --stat HEAD` first — timed-out subagents often completed the work and committed it successfully. HWC Phase 3 (590s timeout, 580s actual) and Phase 5 both show subagents completing despite timeout warnings. The summary reports timeout even on success.

13. **HWC screenshot capture on host**: When taking screenshots of the HWC frontend for visual QA, use Playwright from the host:
   ```bash
   # Install chromium first (one-time)
   cd /home/sean/.hermes/hermes-web-computer && npx playwright install chromium
   # Then screenshot
   node -e "
   const { chromium } = require('playwright');
   (async () => {
     const browser = await chromium.launch({ headless: true });
     const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
     await page.goto('http://localhost:3005', { waitUntil: 'networkidle', timeout: 15000 });
     await page.screenshot({ path: '/tmp/hwc-screenshot.png', fullPage: false });
     await browser.close();
   })().catch(e => { console.error(e.message); process.exit(1); });
   "
   ```
   Then `scp` to container: `scp -i container_key sean@172.19.0.1:/tmp/hwc-screenshot.png /workspace/`

14. **X server on host for screenshot tools**: The host (EndeavourOS) may have Xvfb on display `:1` (check `/tmp/.X1-lock`). If `grim`/`import` fail with "failed to create display", use Playwright instead — it handles its own virtual display.

15. **Subagent screenshot tasks also need verification**: If a subagent is tasked with capturing a screenshot, verify it exists. A subagent may report success but the file ends up in the subagent's own `/tmp`, not the host's. Always check with `ls -la` on the host path immediately after the subagent returns.

16. **HWC process may already be running**: The HWC Go server (PID 682891) was already running on port 3005. After `go build` on the host, restart it: `kill PID; nohup ./server > /tmp/hwc.log 2>&1 &`

12. **git diff --stat shows changes git diff doesn't**: `git diff --stat` may show a file as modified while `git diff` shows nothing. This means the blob (inode) is different but the content is the same. Use `git ls-files -s file` to compare staged vs HEAD blob hashes. If hashes match, there is no actual change — `git add -A && git commit` will be a no-op for that file.

## Quality Pre-Flight Checklist (Before Commit)

- [ ] All spec color tokens match reference (Delta-E less than threshold)
- [ ] No structural element mismatches (panel exists, dock visible, etc.)
- [ ] Element presence confirmed via vision model
- [ ] Functional interactions described and verified present
- [ ] JS framework fully rendered (no white-flash-of-unstyled-content)
- [ ] Build passes (go build && npm run build)
- [ ] Screenshot taken at same viewport as reference
- [ ] Similarity >= 85% (or escaped with gap list after 3 iterations)
- [ ] Git commit message includes similarity score and reference name
- [ ] Push to remote

## Reference Resources

See `references/hwc-subagent-verification.md` for HWC-specific patterns: timeout≠work-lost, build verification after subagent, Playwright screenshot capture when X11 unavailable, host path vs container path mapping, and HWC v1.4 session state (ports, processes, key SSH commands).

### From repo-transmute-v2 (Vision Pipeline)
- `v2/models.py`: VisionResult, ScreenshotDef, ComponentDef -- re-use as data models
- `v2/extract/screenshot.py`: capture_page_screenshots() -- Playwright component-level capture with bounding boxes
- `v2/vision/analyzer.py`: analyze_layout(), match_components() -- layout analysis structure
- `v2/vision/scorer.py`: score_similarity() -- placeholder to wire vision_analyze into
- `v2/migrate/engine.py`: _migrate_component() self-healing loop pattern -- re-adapt for visual QA

### Hyprland Reference (2025-05-24)

Reference screenshot: `https://s96-ious.freeconvert.com/task/6a123a97a30a0f008670bc5d/end4-hyprland-config.png`

Key functional patterns observed (prioritize these in HWC implementation):

**Waybar (status bar):** Workspace indicators (1-5 clickable), window title display, network/volume/battery icons, clock (opens calendar/notifications), temperature monitoring.

**VSCode window:** Explorer sidebar (file tree), menu bar (File/Edit/View/Go/Run/Terminal/Help), editor area with line numbers, bottom panel tabs (Problems/Output/Debug Console/Terminal/Ports).

**Config variables:** $vm, $brow, $game, $chat, $term, $file -- workspace-to-app mappings. Mouse warping. External config sourcing via `source = ~/.config/hypr/...`.

**This is the functional depth the user expects:** workspace switching, app launching via shortcuts, config-driven layout, terminal integration in IDE. When auditing HWC against this reference, focus on whether HWC has equivalent: workspace indicators, app shortcut system, terminal panel, menu bar, file explorer panel.