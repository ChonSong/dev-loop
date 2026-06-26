# SEEK Quick Apply Workflow

## Overview
SEEK's Quick Apply is a multi-step wizard that pre-fills from the user's profile. The flow is consistent across jobs: Choose Documents → Role Requirements → Profile → Review → Submit.

## Step-by-Step

### 1. Navigate to Job
```bash
curl -X POST http://127.0.0.1:3099/navigate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://au.seek.com/job/JOB_ID"}'
```

### 2. Click Quick Apply
```bash
curl -X POST http://127.0.0.1:3099/click-text \
  -H "Content-Type: application/json" \
  -d '{"text":"Quick apply"}'
```

Wait 4-5 seconds for the apply page to load.

### 3. Upload Resume
Some jobs show a dropdown of stored resumes. Always upload fresh to control which version is used:

```javascript
// First click "Upload a resumé" label to show the file input
await page_evaluate(`[...document.querySelectorAll('label')]
  .find(l => l.textContent.includes('Upload a resumé'))?.click()`);

// Then upload via CDP
const doc = await send('DOM.getDocument');
const q = await send('DOM.querySelector', {
  nodeId: doc.result.root.nodeId,
  selector: '#resume-fileFile'
});
await send('DOM.setFileInputFiles', {
  nodeId: q.result.nodeId,
  files: ['/path/to/cv.pdf']
});
```

**⚠️ VERIFY**: After upload, check the page text shows your filename, not an old stored one. SEEK sometimes shows "Loading..." and reverts to a stored resume.

### 4. Cover Letter
```javascript
await page_evaluate(`[...document.querySelectorAll('label')]
  .find(l => l.textContent.includes("Don't include a cover letter"))?.click()`);
```

### 5. Click Continue
```javascript
await page_evaluate(`[...document.querySelectorAll('button')]
  .find(b => b.textContent.trim() === 'Continue')?.click()`);
```

### 6. Role Requirements (if present)
The page URL will contain `/role-requirements`. Fill all form elements:

**Selects:**
```javascript
document.querySelectorAll('select').forEach(s => {
  const o = Array.from(s.options).find(o => o.value && o.value.length > 0);
  if (o) { s.value = o.value; s.dispatchEvent(new Event('change', {bubbles:true})); }
});
```

**Radios (first in each group):**
```javascript
const groups = {};
document.querySelectorAll('input[type="radio"]').forEach(r => {
  if (!groups[r.name]) { r.click(); groups[r.name] = true; r.dispatchEvent(new Event('change', {bubbles:true})); }
});
```

**Checkboxes (first in each group):**
```javascript
const groups = {};
document.querySelectorAll('input[type="checkbox"]').forEach(c => {
  if (!groups[c.name]) { c.click(); groups[c.name] = true; c.dispatchEvent(new Event('change', {bubbles:true})); }
});
```

**Text inputs (including hidden `indirect_*` ones):**
```javascript
document.querySelectorAll('input[type="text"], input:not([type]), textarea').forEach(el => {
  if (!el.value || el.value.trim() === '') {
    el.value = 'Australian citizen';
    el.dispatchEvent(new Event('input', {bubbles:true}));
    el.dispatchEvent(new Event('change', {bubbles:true}));
  }
});
```

**Salary selects** — some roles ask for salary expectations. Set to reasonable value:
```javascript
// $70k option
s.value = 'AU_Q_8_V_2_A_14940';
```

If still stuck after filling, click Continue again — it sometimes takes two tries.

### 7. Profile Step
URL contains `/profile`. Just click Continue:
```javascript
await clickByText('Continue');
```

### 8. Review & Submit
URL contains `/review`. Click Submit:
```javascript
await clickByText('Submit application');
```

Success URL: `/apply/success` — "Good luck, [Name]" confirmation page.

## Common Role-Requirements Questions

| Question | Typical Answer | Element Type |
|----------|---------------|--------------|
| Right to work | Australian citizen | select |
| Years of experience | Less than 1 year / No experience | select |
| Salary expectation | $70,000 | select |
| AWS Cloud Practitioner cert | No | radio |
| AWS Solutions Architect cert | No such certification | checkbox |
| Police check | Willing to undertake | radio |
| Microsoft Office experience | (first checkbox) | checkbox |
| Technologies experience | Windows Server, AD/GPO, etc. | text input |
| Cisco certification | No such certification | select |

## Debugging Stuck Forms
When Continue doesn't advance the page:
1. Check for `[class*="error"]` elements — read their text for what's missing
2. Check for empty `input[type="text"]`, `textarea`, or `select` elements
3. Check for unchecked required radio/checkbox groups
4. Try clicking Continue again after 2-3 seconds — some forms validate async
5. If Angular, try `angular.element(el).scope().$digest()` after setting values
