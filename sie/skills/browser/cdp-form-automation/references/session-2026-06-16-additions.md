# Additional Pitfalls (June 2026 session adds)

## CDP Runtime.evaluate returns undefined
The return value is at `result.result.value` (nested), NOT `result.value`. The CDP response structure is:
```json
{"id": 1, "result": {"result": {"type": "string", "value": "ACTUAL_VALUE"}}}
```
Access as: `m.result.result.value` where `m` is the full CDP response message.

## Continue button may need 2 clicks
First click validates form and shows errors, second click (after filling missing fields) actually submits. Always check URL between clicks via /info endpoint.

## CV verification before submitting
Always show a screenshot of the CV PDF to the user before submitting any application so they can confirm the right version is being used. Use vision_analyze on the PDF screenshot. Do not assume the uploaded file is what SEEK will attach — SEEK may silently fall back to a stored profile resume.

## Cover letter
Never default to "Don't include a cover letter" without asking the user first. Ask explicitly.

## SEEK stored resume overrides upload
After uploading via DOM.setFileInputFiles, SEEK may briefly show "Loading..." then revert to the user's stored profile resume. Always verify what filename actually appears in the page text after the upload completes.
