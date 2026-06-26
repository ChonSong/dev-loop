# Session Example: SEEK Quick Apply

## Flow
1. Navigate to job page → `/click-text` with "Quick apply"
2. Resume step: click "Upload a resumé" label → upload via `DOM.setFileInputFiles` for `#resume-fileFile`
3. Cover letter: click "Don't include a cover letter" label
4. Click "Continue" (may need 2 attempts if loading)
5. Employer questions (React): fill `<select>` dropdowns + radio/checkbox clicks
6. Profile step: click "Continue"
7. Review step: click "Submit application"

## Hidden Selects (React)
```javascript
// Get options
const opt = document.querySelector('select[name="questionnaire.AU_Q_6_V_10"]');
Array.from(opt.options).map(o => ({value: o.value, text: o.text}));

// Set value
opt.value = 'AU_Q_6_V_10_A_14970';
opt.dispatchEvent(new Event('change', {bubbles:true}));
```

## Radio Buttons
```javascript
document.querySelector('input[type="radio"][name="questionnaire.X"][value="Y"]').click();
```

## URLs After Each Step
- `/apply` → document selection
- `/apply/role-requirements` → employer questions
- `/apply/profile` → SEEK profile
- `/apply/review` → review & submit
- `/apply/success` → confirmation
