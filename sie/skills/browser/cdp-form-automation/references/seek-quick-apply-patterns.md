# SEEK Quick Apply — Form Filling Patterns

## Role-Requirements: Fill ALL Input Types At Once

After clicking Continue on the document selection page, SEEK may show employer questions. These combine selects, radios, checkboxes, and text inputs. Fill them ALL at once:

**For Angular SEEK forms** (older UI, uses `angular.element`):
```javascript
await send('Runtime.evaluate', {
  expression: `(() => {
    // 1. SELECTS — pick first option with a value
    document.querySelectorAll('select').forEach(s => {
      const o = Array.from(s.options).find(o => o.value && o.value.length > 0);
      if (o && (!s.value || s.value === '')) {
        s.value = o.value;
        s.dispatchEvent(new Event('change', {bubbles:true}));
      }
    });

    // 2. RADIOS — click first in each group (click, not checked=true)
    const radioNames = {};
    document.querySelectorAll('input[type="radio"]').forEach(r => {
      if (!radioNames[r.name]) {
        r.click();
        r.checked = true;
        r.dispatchEvent(new Event('change', {bubbles:true}));
        radioNames[r.name] = true;
      }
    });

    // 3. CHECKBOXES — click first in each group
    const cbNames = {};
    document.querySelectorAll('input[type="checkbox"]').forEach(c => {
      if (!cbNames[c.name]) {
        c.click();
        c.checked = true;
        c.dispatchEvent(new Event('change', {bubbles:true}));
        cbNames[c.name] = true;
      }
    });

    // 4. TEXT INPUTS — fill empty ones
    document.querySelectorAll('input[type="text"], input:not([type]), textarea').forEach(el => {
      if (!el.value || el.value.trim() === '') {
        el.value = 'Australian citizen';
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
        try { angular.element(el).triggerHandler('input'); } catch(e) {}
      }
    });

    return 'ALL FILLED';
  })()`,
  returnByValue: true
});
```

**For React SEEK forms** (new SPA, no Angular — using native input setters):

SEEK has been migrating to a React SPA. The key difference: React intercepts the `value` property setter on inputs. Setting `el.value = 'x'` visibly changes the DOM but React doesn't see it — validation still fails.

```javascript
// React textareas — must use native prototype setter:
(() => {
    const ns = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
    ns.call(textareaElement, 'Yes');
    textareaElement.dispatchEvent(new Event('input', {bubbles: true}));
})();

// React radios — click the LABEL element, not the input:
(() => {
    const label = document.querySelector('label[for="' + radioInput.id + '"]');
    if (label) label.click();
})();

// React checkboxes — native setter for 'checked' property:
(() => {
    const ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
    ns.call(checkboxElement, true);
    checkboxElement.dispatchEvent(new Event('change', {bubbles: true}));
})();
```

See the SKILL.md "React Full-Fill Pattern" for the complete single-call function.

## Specific SEEK Question IDs (observed)

| Field | Name | Value to set |
|-------|------|-------------|
| Right to work | `questionnaire.AU_Q_6_V_10` | `AU_Q_6_V_10_A_14970` (Australian citizen) |
| Experience (Cloud Ops) | `questionnaire.AU_Q_FD3CEFA7...` | `..._2` (Less than 1 year) |
| Experience (DevOps) | `questionnaire.AU_Q_BF1381...` | `..._2` (Less than 1 year) |
| Experience (Service Desk) | `questionnaire.AU_Q_568_V_4` | `...A_22016` (Less than 1 year) |
| AWS Cloud Practitioner | `questionnaire.AU_Q_28763_V_3` | Radio Yes/No |
| AWS Solutions Architect | `questionnaire.AU_Q_28759_V_3` | Checkbox "No such certification" |
| Salary expectation | `questionnaire.AU_Q_8_V_2` | `AU_Q_8_V_2_A_14940` ($70k) |
| Cisco certification | `questionnaire.AU_Q_950_V_3` | `...A_16741` (No such certification) |

## Text Inputs with indirect names

Some SEEK employer questions use text inputs with names like:
```
questionnaire.indirect_<uuid>_<uuid>
```

These are hidden until validation fails. Find them with:
```javascript
document.querySelectorAll('input[name^="questionnaire.indirect"]')
```

Fill based on context:
```javascript
document.querySelectorAll('[name*="indirect"]').forEach(el => {
  const text = (el.closest('div')?.textContent || '').toLowerCase();
  if (text.includes('right to work') || text.includes('visa') || text.includes('citizen')) {
    el.value = 'Australian citizen';
  } else if (text.includes('msp') || text.includes('experience') || text.includes('years')) {
    el.value = 'Less than 1 year';
  } else if (text.includes('technologies') || text.includes('hands-on')) {
    el.value = 'Windows Server, AD/GPO, Microsoft 365';
  } else {
    el.value = 'N/A';
  }
  el.dispatchEvent(new Event('input', {bubbles:true}));
  el.dispatchEvent(new Event('change', {bubbles:true}));
});
```

## Verification After Fill

Check error state:
```javascript
document.body.innerText.includes('Before you can continue')
// Or:
document.querySelectorAll('[class*="error"]').length
// Or count invalid Angular fields:
document.querySelectorAll('.ng-invalid').length
```

## Continue Button Behavior

The Continue button often needs **two clicks** after setting values:
- First click: validates and shows "Before you can continue" with missing fields
- Second click (after filling missing fields): proceeds to next step
- Some forms need the Continue clicked via Runtime.evaluate + button text match rather than the `/click-text` endpoint, because button text includes zero-width characters

```javascript
// Reliable Continue click:
await send('Runtime.evaluate', {
  expression: `(() => {
    for (const b of document.querySelectorAll('button')) {
      if (b.textContent.trim().includes('Continue')) {
        b.scrollIntoView({block:'center'});
        b.click();
        return 'clicked';
      }
    }
    return 'none';
  })()`,
  returnByValue: true
});
```
