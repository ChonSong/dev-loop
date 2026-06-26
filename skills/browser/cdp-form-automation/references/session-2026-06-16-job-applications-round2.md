# Session — June 16, 2026: Job Applications Round 2

## What was in play

Used the Tandem Browser (Electron app) to apply to SEEK Quick Apply roles from the container. The Hermes browser tool hits Cloudflare from the container IP, so Tandem is the only way to access SEEK.

## Outcomes

**11 Quick Apply submissions** in this session:
1. Junior Engineer (DevOps) @ Woods & Co — $70-75K
2. Junior Systems Engineer @ NSW Land Registry Services
3. Cloud Support Engineer @ Networx Australia — $80-110K
4. Technical Support Engineer @ Hyve Managed Hosting — $80-95K
5. Level 1 Support Engineer @ Arxis Group — $60-80K
6. Platform Support Engineer
7. Junior Full-Stack Software Engineer
8. Cloud Engineer @ Shield Recruitment
9. Azure DevSecOps Engineer
10. Junior Java Engineer @ Launch Recruitment
11. Cloud Platform Engineer

## Key learns for the skill

### React SPA form fields — new territory

Not all SEEK Quick Apply forms are AngularJS anymore. Some use a React SPA with different input handling needs:

- **Textareas**: `el.value = 'Yes'` does NOT update React state. Needed the native prototype setter:
  ```js
  const ns = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
  ns.call(el, 'Yes');
  ```

- **Radio buttons**: Calling `.click()` or setting `.checked = true` on the `<input>` doesn't register with React. Need to click the associated `<label>` element or use native setter for the `checked` property.

- **Checkboxes (privacy policy)**: Same native setter approach needed for the `checked` property at the review/submit step.

- **The `fill_all_fields` pattern** that handles all 4 input types (selects, textareas, radios, checkboxes) in one pass was developed this session and works reliably.

### Specific failures

- **AWS Cloud Engineer** (92656803) — No Quick Apply available
- **Junior Digital Solutions Engineer** (92624583) — No Quick Apply available
- **Cloud Engineer** (92576546) — Had Quick Apply but the first attempt timed out because we hadn't learned the label-click approach for radios. Second attempt succeeded after using the Full-Fill pattern.
- **Cloud Platform Engineer** (92265824) — Same story, first attempt timed out, second succeeded.

### Resume handling

SEEK's React UI pre-selects the resume via UUID in the hidden `<select>`. The visible text still says "Please select a resume" as placeholder but the value is set. No upload needed — just verify value is non-empty and Continue.

### URLs

Search URL pattern used: `https://www.seek.com.au/jobs?keywords=KEYWORDS&location=Sydney`
