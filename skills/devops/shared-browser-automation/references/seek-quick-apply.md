# SEEK Quick Apply Workflow

## Sequence (reliable path)

1. **Navigate to job listing**
   ```
   curl -s -X POST http://127.0.0.1:3099/navigate
     -H "Content-Type: application/json"
     -d '{"url":"https://au.seek.com/job/{JOB_ID}"}'
   ```

2. **Click Quick Apply** (wait 4s)
   ```
   curl -s -X POST http://127.0.0.1:3099/click-text
     -H "Content-Type: application/json"
     -d '{"text":"Quick apply"}'
   ```

3. **Upload resume**
   - Click "Upload a resumé" label via `click-text` or CDP
   - Wait 1-2s for file input to render
   - Use DOM.setFileInputFiles to upload `/tmp/cv-user-version.pdf`
   - ⚠️ SEEK may replace uploaded file with stored profile resume. Verify filename appears correctly.

4. **No cover letter**
   - Click "Don't include a cover letter" label

5. **Continue** — may need 2 clicks (first triggers validation, second proceeds)

6. **Role requirements** (if any)
   - Determine what's needed with `document.querySelectorAll('[class*="error"]')` and checking page text for "Before you can continue"
   - Set `<select>` values by dispatching `change` event
   - Fill text/textarea fields with sensible defaults ("Australian citizen", "Less than 1 year")
   - **Click first radio in each group**: `const g={};document.querySelectorAll('input[type="radio"]').forEach(r=>{if(!g[r.name]){r.click();r.checked=true;r.dispatchEvent(new Event('change',{bubbles:true}));g[r.name]=true;}});`
   - **Click first checkbox in each group**: same pattern but for checkboxes
   - Click Continue

7. **Profile step** — just click Continue

8. **Review step** — take screenshot, **show user via vision_analyze**, click "Submit application"

## Multi-Step Loop Pattern

```javascript
let u = '';
for (let i = 0; i < 6; i++) {
  // Click the appropriate button
  await send('Runtime.evaluate', { expression: `
    (() => {
      for (const b of document.querySelectorAll('button')) {
        const t = b.textContent.trim();
        if (t === 'Continue' || t.includes('Continue') || t === 'Submit application') {
          b.scrollIntoView({block:'center'}); b.click(); return 'clicked';
        }
      }
      return 'none';
    })()
  `});

  await new Promise(r => setTimeout(r, 5000));
  u = await getUrl(); // from send('Runtime.evaluate', {expression: 'window.location.href'})
  if (u.includes('success')) break;

  // If stuck on role-requirements, fill everything
  if (u.includes('role-requirements')) {
    await fillAllFormElements(send); // selects, radios, checkboxes, text inputs
  }
}
```

## Form Filling Helper

```javascript
// Call this when stuck on role-requirements
await send('Runtime.evaluate', { expression: `
  (() => {
    // 1. All selects
    document.querySelectorAll('select').forEach(s => {
      const o = Array.from(s.options).find(o => o.value && o.value.length > 0);
      if (o) { s.value = o.value; s.dispatchEvent(new Event('change', {bubbles:true})); }
    });
    // 2. First radio in each group
    const gn = {};
    document.querySelectorAll('input[type="radio"]').forEach(r => {
      if (!gn[r.name]) { r.click(); r.checked = true; r.dispatchEvent(new Event('change', {bubbles:true})); gn[r.name] = true; }
    });
    // 3. First checkbox in each group
    const cn = {};
    document.querySelectorAll('input[type="checkbox"]').forEach(c => {
      if (!cn[c.name]) { c.click(); c.checked = true; c.dispatchEvent(new Event('change', {bubbles:true})); cn[c.name] = true; }
    });
    // 4. Empty text inputs
    document.querySelectorAll('input[type="text"], input:not([type]), textarea').forEach(el => {
      if (!el.value || el.value.trim() === '') {
        el.value = 'N/A'; el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true}));
      }
    });
    return 'done';
  })()
` });
```

## Verification

**Before clicking Submit application**, always:
1. Take a screenshot of the review page
2. Pass it to `vision_analyze` to verify the correct CV filename is shown
3. Only then click Submit

## CDP Response Parsing

`Runtime.evaluate` with `returnByValue: true` returns:
```json
{"id": N, "result": {"result": {"type": "string", "value": "ACTUAL_VALUE"}}}
```
Access via: `response.result.result.value`

## Common Questions (from this session)

- **Right to work**: "I'm an Australian citizen" (first option, value `AU_Q_6_V_10_A_14970`)
- **Experience**: "Less than 1 year" (second option, value ending in `_2`)
- **Salary expectations**: $70k (value `AU_Q_8_V_2_A_14940`)
- **Cisco cert**: "No such certification" (value `AU_Q_950_V_3_A_16741`)
- **Police check**: "I am willing to undertake" (value `AU_Q_15_V_5_A_1662`)
