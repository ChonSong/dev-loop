# Session Reference — 2026-06-16 Angular & SEEK Form Automation

## NGS Super (Elmo Portal — AngularJS)

- **URL**, step1: `/careers/careers/job/apply/160#/step1?jobAdId=160&channel=external&source=2`
- CV upload: `DOM.setFileInputFiles` on `#resumeFile` (use `DOM.querySelector` with `#resumeFile`)
- Step 2 fields: `[name="mobile"]`, `[name="addressLine1"]`, `[name="suburb"]`, `[name="state"]`, `[name="postcode"]`, `[name="country"]`
- Step 2 questions: `question_83` (background Yes), `question_96` (salary), `question_93` (notice), `question_95` (working rights), `question_107` (gender), `question_106[]` (how you heard)
- Country select values use `string:AU` prefix (not plain `AU`)
- Radio buttons use angular scope: `scope.data.question_107 = '4'`
- **Key finding**: After setting scope values, click "Save" first, THEN "Next". "Next" without "Save" triggers validation.
- Final: `#/step3` shows review + "Submit" button. Use scope.submitApplication() if button click doesn't navigate.
- Submit confirmation: `scope.$apply(function() { scope.submitApplication(); })` works when button click doesn't

## Qvest Australia (SEEK — React)

- Job: DevOps/Cloud Operations Engineer, `https://au.seek.com/job/92438405`
- Salary: $96-111k, Alexandria Sydney, posted 14d ago
- **Key finding**: First 3 questions use `<select>` dropdowns, not radio buttons.
  - Right to work: `select[name="questionnaire.AU_Q_6_V_10"]` — option `AU_Q_6_V_10_A_14970` = Australian citizen
  - Cloud Ops experience: `select[name="questionnaire.AU_Q_FD3CEFA7AEF24E4845203114B693FCC0_V_1"]` — ending in `_2` = "Less than 1 year"
  - DevOps experience: `select[name="questionnaire.AU_Q_BF1381DAF46D7A6E961649A50B9053EB_V_2"]` — ending in `_2` = "Less than 1 year"
- AWS Cloud Practitioner uses **radio buttons**: `name="questionnaire.AU_Q_28763_V_3"` — value ending `_28765` = "No"
- AWS Solutions Architect uses **checkboxes** (not radios): `name="questionnaire.AU_Q_28759_V_3"` — checkbox ID `AU_Q_28759_V_3_A_28762` = "No such certification"
- Police Check uses **radio buttons**: `name="questionnaire.AU_Q_15_V_5"` — value `AU_Q_15_V_5_A_1662` = "I am willing to undertake"
- The `/fill` endpoint works for `<select>` elements with value + change event dispatch
- Radio buttons: use exact value selectors: `input[type="radio"][name="..."][value="..."]`
- SEEK profile step: user has OneTag job, drivers licence, 17 skills pre-filled. Just click Continue.
- Submit uses `⁠Submit application` button (may include non-breaking space prefix)

## FinXL IT Professional Services (SEEK — React)

- Job: Associate Operations Engineer, `https://au.seek.com/job/92608968`
- Contract/Temp, Sydney, posted 6d ago with low app volume
- Quick Apply had NO employer screening questions — went directly choose-documents → profile → review → submit
- Fast flow: upload CV, set no cover letter, Continue through profile, Submit
- Same 4-step SEEK flow

## Junior Cloud Support Engineer (SEEK — React)

- Job: `https://au.seek.com/job/92737561`, $80-90k package, Sydney hybrid, via Dash Recruitment
- Posted 4h ago, Medium app volume
- Employer questions: 2 selects only (no radio buttons at all)
  - Right to work: `select[name="questionnaire.AU_Q_6_V_10"]` — option `AU_Q_6_V_10_A_14970` = Australian citizen
  - Experience: `select[name="questionnaire.AU_Q_6A8ACDCD42AF5301AFD1BFF68258DBED_V_1"]` — option ending in `_2` = "Less than 1 year"
- Straightforward flow: `/apply` → `/apply/role-requirements` → `/apply/profile` → `/apply/review` → `/apply/success`

## SEEK Job Search Tips

- OR operator: `keywords=junior+systems+engineer+OR+jr+devops+OR+graduate+devops&daterange=7&location=Sydney`
- Exact-match quotes for companies: `keywords=%22DMA+Global%22&location=Sydney`
- Extract job IDs from search results: find `<a>` tags with href containing `/job/`, job ID is the numeric segment
- Check the actual URL after search navigation to confirm the slug format

## SEEK Resume Upload Pitfall (Critical)

SEEK Quick Apply may swap your freshly uploaded CV for a pre-existing one from the user's profile:
- Upload shows `"CV - SRE.pdf"` in the upload field during progress
- After upload completes, review page may show an older filename like `"8/6/26 - Sean Cheong Software Engineer.pdf"`
- **Mitigation**: Navigate to the review step and read the page text to find which `.pdf` filename appears in the resume section BEFORE clicking Submit. Use CDP's Runtime.evaluate to extract `document.body.innerText` and search for `.pdf`.

## General Patterns

1. **AngularJS**: Use `scope.$apply()` to set model values. `ngModel.$setViewValue()` for individual fields.
2. **React (SEEK)**: Set `el.value + dispatch change event` for selects. Click + change event for radios/checkboxes.
3. **File uploads**: Always use `DOM.setFileInputFiles` — setting via DOM value never works.
4. **Multi-step**: Check `window.location.hash` (Angular) or URL path (SEEK React) for step transitions. Always save before next.
5. **Validation**: After filling, check `.ng-invalid` (Angular) or `.alert-danger`/`.error` count before continuing.
6. **SEEK flow**: `/apply` (documents) → `/apply/role-requirements` (questions) → `/apply/profile` (confirm) → `/apply/review` (review+submit) → `/apply/success` (confirmation).
7. **Verify before submit**: Read the review page text to check which resume filename is attached. Search for `.pdf` to find the actual document.
