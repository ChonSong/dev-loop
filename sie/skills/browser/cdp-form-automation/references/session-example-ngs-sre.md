# Session Example: NGS Super SRE Application

## Target
https://ngssuper.elmotalent.com.au/careers/careers/job/view/160

## Form Type
AngularJS SPA with hash-based routing (`#/step1`, `#/step2`, `#/step3`)

## Key Techniques

### File Upload
```javascript
// After clicking "Upload" to show file input
const doc = await send('DOM.getDocument');
const query = await send('DOM.querySelector', { nodeId: doc.result.root.nodeId, selector: '#resumeFile' });
await send('DOM.setFileInputFiles', { nodeId: query.result.nodeId, files: ['/tmp/cv.pdf'] });
```

### Angular Scope Manipulation
```javascript
const scope = angular.element(document.querySelector('[name="mobile"]')).scope();
scope.$apply(function() {
  scope.data.contact.mobile = '0434968983';
  scope.data.contact.country = 'string:AU';  // Note: "string:" prefix required
  scope.data.question_X = '1';  // For radio button questions
});
```

### Finding Hidden Fields
Angular forms have `<select>` elements with auto-generated names, not radio buttons:
- Query: `document.querySelectorAll('input, select')`
- Check names for patterns like `questionnaire.AU_Q_*`

### Select Manipulation
```javascript
const sel = document.querySelector('select[name="questionnaire.AU_Q_6_V_10"]');
sel.value = 'AU_Q_6_V_10_A_14970';
sel.dispatchEvent(new Event('change', {bubbles:true}));
```

## Application Data
| Field | Value |
|-------|-------|
| Role | Site Reliability Engineer |
| Resume | CV - SRE.pdf |
| Mobile | 0434 968 983 |
| Address | 153 Williams St, Granville NSW 2142 |
| Salary | $70,000-$90,000 |
| Notice | Immediately available |
| Working Rights | Full — Australian Citizen |
