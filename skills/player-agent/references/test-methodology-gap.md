# Self-Referential Testing Gap

## The Problem

The Player writes tests alongside implementation code. A test written by the same agent that wrote the code validates the implementation, not the requirement. The test passes because the code does what the test expects — but neither is checked against what *should* happen.

This is the most common quality failure in the dev loop.

## Why It Happens

The AGENTS.md task format drives it. When the Coach or Task Exhaustion Recovery generates tasks like:

```
### Task: add-e2e-pause-resume-test
- **Description**: Add a Playwright test that... verifies the PAUSED overlay appears
```

The task itself tells the Player to write a test. But the feature (pause/resume overlay) was built in the same or an adjacent tick by the same Player. The test validates the implementation, not a specification.

## Evidence

### Polytopia E2E tests (gameplay.spec.ts, 467 lines)

| Test | Written By | Written When | Verdict |
|------|-----------|-------------|---------|
| tribe sort alphabetical | Player | 8h after feature (separate tick) | ✅ Reference-based — hardcodes expected order from GDD |
| pause/resume Escape key | Player | Same session as feature | ❌ Self-referential — uses wrong Phaser API, keyboard unreliable in headless |
| mute button persistence | Player | Same session as feature | ❌ Comment acknowledges headless mode audio isn't unlocked — test can't actually verify the feature |
| city menu open/close | Player | After feature | ⚠️ Click at (400,300) overlaps city position — test bug inherited from implementation assumptions |

The pause/resume test fails not because the feature is broken (it works on live site), but because the test uses `gs.pauseOverlay.children.list` on a Phaser `Group` (which has `children` as a `Set`, not a `Container` — `children.list` doesn't exist). The Player wrote both the feature code and the test in the same session, so the test inherited the same API assumptions. If a separate agent had written the test against the GDD specification, this bug would have been caught before the feature was approved.

### GTO Wizard E2E (18 spec files, ~431 lines POM)

The entire suite was written by the Player alongside feature code. The E2E runner is currently broken (nested `@playwright/test` version conflict) — no E2E tests can run. This means 18 spec files are dead weight while the methodology issue remains unaddressed.

## The Fix

1. **Task generation must stop asking for self-referential tests.** Tasks should say "Verify [feature] against [reference]" not "Add E2E test for [feature]."
2. **Tests must be defined against an independent reference** before the implementation exists: original app behavior, GDD requirements, or reference screenshots.
3. **The Coach must flag self-referential tests as a methodology failure** — not just note the resulting test bugs.
4. **When the E2E runner is broken for a project, document it in the checkpoint** as an infra_gap so the Player knows test results are unreliable and skips E2E steps.

## Reference: What a Well-Formed Test Looks Like

From the tribe sort test (47c203f), which follows the methodology correctly:

```typescript
test('tribe cards are sorted alphabetically on SelectScene', async ({ page }) => {
    await loadGame(page);
    await page.waitForFunction(() => {
      return !!(window as any).__PHASER_GAME__?.scene?.isActive('SelectScene');
    }, { timeout: 10000 });
    const tribeNames = await page.evaluate(() => {
      const g = window as any;
      const ss = g.__PHASER_GAME__?.scene?.getScene('SelectScene');
      if (!ss) return [];
      const TRIBE_NAMES = ['Bardur', 'Cymanti', 'Elyrion', 'Imperius', 'Oumaji', 'Polaris', 'Xin-xi'];
      const texts: string[] = [];
      const list = ss.children.list || [];
      for (const child of list) {
        if (child.type === 'Text' && child.text && TRIBE_NAMES.includes(child.text)) {
          texts.push(child.text);
        }
      }
      return texts;
    });
    expect(tribeNames.length).toBe(7);
    const expected = ['Bardur', 'Cymanti', 'Elyrion', 'Imperius', 'Oumaji', 'Polaris', 'Xin-xi'];
    expect(tribeNames).toEqual(expected);
});
```

Key traits: (1) reads actual page state, (2) asserts against hardcoded expected order from GDD, (3) does not depend on implementation internals, (4) was written in a separate tick from the feature.
