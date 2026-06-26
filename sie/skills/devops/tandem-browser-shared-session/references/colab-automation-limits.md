# Colab Automation Limits (June 2026)

Google Colab uses Web Components (Lit-based `<mwc-dialog>`, `<colab-*>`, `<md-icon>`) extensively. These render their internal DOM in open Shadow Roots, but CDP's `Runtime.evaluate` cannot access shadow root content via standard DOM queries.

## What doesn't work

| Attempt | Result |
|---------|--------|
| `querySelector('[role="tab"]')` to find the Upload tab | Returns null — tab elements are in shadow DOM |
| JavaScript `.click()` on menu items | No effect — React/Lit event handlers don't respond |
| `KeyboardEvent` dispatch (Alt+F, Ctrl+O) to trigger menus | No effect — Colab's custom menu system ignores synthesized events |
| Setting Monaco editor textarea via native value setter | The editor doesn't reflect changes — Colab's code cell uses its own bindings |
| `DOM.setFileInputFiles` for the upload file input | The file input is in shadow DOM — can't reach it |

## What works

- **Navigation**: `POST /navigate` works fine — Colab is a standard web app at the page level
- **`/screenshot.png` + `vision_analyze`**: Reliable for reading page state
- **Coordinate-based clicks via `/click`**: Works if you know exact pixel coordinates (use vision_analyze to find them)
- **Waiting for page load**: Colab can take 5-10s to fully render after navigation. Set 8s+ sleep after navigate.

## Reliable workflow

1. Navigate to `https://colab.research.google.com/` and wait 8s
2. Use `screenshot.png` + `vision_analyze` to confirm sign-in state and current page
3. If a dialog is blocking, try coordinate clicks on Cancel/New Notebook buttons
4. If the dialog's buttons are in shadow DOM and clicks don't land → stop automating
5. Give the user a one-step instruction: "Click File → Upload Notebook in your Tandem window, select the file at path, then click Runtime → Run all"

## Why this matters

Trying 10+ approaches to automate a single UI interaction wastes 50+ turns. Three strikes and you're out — Shadow DOM automation is not reliably achievable via CDP evaluate. The user needs to know what step requires them, not watch you try increasingly creative workarounds.
