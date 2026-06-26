The reference file `references/blank-space-measure.js` contains a reusable Playwright script (`measureBlankSpace()`) for programmatic blank-space measurement of A4 documents.

The reference file `references/print-css.md` covers page sizing, font size tables, color theme, page break strategy, and container-specific pitfalls.

The reference file `references/qa-verification.md` covers structured QA prompts and vision model pitfalls.

The reference file `references/blank-space-measure.js` exports a `measureBlankSpace(page)` function returning `{pageHeight, footerTop, footerBottom, blankPx, blankPercent, overflow, overflowPx}`. Import via `const measure = require('./blank-space-measure.js')`.
