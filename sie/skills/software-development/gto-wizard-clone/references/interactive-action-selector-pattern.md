# Interactive Action Selector Pattern

For training-study pages where the user should pick their own action and compare vs GTO.

## The Gap

The study page was originally a **read-only solver visualizer**: it fetched GTO data, color-coded the hand matrix, and displayed action frequencies. The action cards (Fold/Call/Raise) were static `<div>` elements — display only. The user could see *what GTO says* but had no way to *choose their own action* and compare.

This is a common pattern across training platforms: the display layer works but the interactive training layer was never wired.

## The Fix

Replaced the static action cards with an `ActionSelector` component that makes 4 clickable buttons (Fold, Call, Raise, All In) with:

- **Selection state**: `useState<string | null>` tracks which button is pressed
- **GTO comparison**: `handleCheckAction` compares the user's selection against the solver's recommended action
- **Feedback state**: `'correct' | 'incorrect' | null` drives locked mode + visual result
- **Reset on hand change**: `useEffect` on `selectedCell` clears the user's choice
- **Try Again**: resets feedback state so user can re-pick

## Component API

```tsx
<ActionSelector
  selectedAction={userAction}
  onSelect={(action) => setUserAction(action)}
  gtoAction={gtoAction}         // solver's recommended action
  gtoFrequency={gtoFrequency}   // solver's frequency for that action
  disabled={!selectedHandData}  // grey out when no hand selected
  locked={actionFeedback !== null}  // lock selection after check
  feedback={actionFeedback}     // 'correct' | 'incorrect' | null
/>
```

## Where to Apply Next

Same pattern is missing on:
- **PostflopTraining** page — the scenario-based quiz (has submit endpoint but no inline action selector)
- **Train** page — `/train` uses a separate question-generation flow; could benefit from inline selector
- **Practice** page — `/practice` has no action selection at all

## Pattern to Detect

When you see these signals in a training/dashboard page:
1. Action data is fetched from an API but rendered as `<div>` elements, not `<button>`
2. A "Check" or "Submit" button is missing from the flow
3. The page shows solver results but has no way for the user to make their own choice

**That's the gap.** Every display-only action frequency card is a candidate for an interactive action selector.
