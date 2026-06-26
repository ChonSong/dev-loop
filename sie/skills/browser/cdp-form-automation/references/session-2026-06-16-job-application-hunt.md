# Session: June 16 2026 — Job Application Sprint

## Summary
Applied to 8 jobs in one session using the Tandem shared browser + electron-viewer CDP automation. NGS Super used their own Elmo portal (AngularJS); Qvest, FinXL, and 4 other roles used SEEK Quick Apply.

## Key URLs
- NGS Super SRE application: https://ngssuper.elmotalent.com.au/careers/careers/job/view/160
- SEEK base search: https://au.seek.com/junior-systems-engineer-OR-jr-devops-OR-graduate-devops-jobs?daterange=7&location=Sydney

## NGS Super Elmo Portal (AngularJS)
- CV upload via DOM.setFileInputFiles worked first time
- Contact details + screening questions required Angular scope.$apply() to register values
- Gender identity question (optional but required by validation) — set to "Prefer not to say" (value 289)
- Final submit required clicking the actual Submit button via the Angular controller
- Password used for account creation: ApplySRE2026!

## SEEK Quick Apply Flow
- Always click "Upload a resume" label FIRST to make file input visible
- DOM.setFileInputFiles works but SEEK may revert to stored profile resume
- Must verify filename in page text after upload
- Cover letter: user's preference was "Don't include" but always ask
- Transitions: apply -> role-requirements -> profile -> review -> success
- role-requirements can have text inputs named `questionnaire.indirect_<uuid>` — fill via /fill endpoint

## Resume Issue
- SEEK stored "8/6/26 - Sean Cheong Software Engineer.pdf" on profile
- Uploaded "CV - SRE.pdf" via DOM.setFileInputFiles but may not have taken effect
- Lesson: always verify what filename appears after upload, show user before submitting

## Cover Letter
- User did NOT want cover letters for these applications
- But the lesson is to ask, not assume

## Roles Applied To
1. NGS Super — Site Reliability Engineer
2. Qvest Australia — DevOps/Cloud Operations Engineer ($96-111k)
3. FinXL — Associate Operations Engineer
4. Dash Recruitment — Junior Cloud Support Engineer ($80-90k)
5. NT Partners — Junior Software Support Engineer
6. Sirius Technology — L1 Support Engineer ($75k)
7. BlueScale — Service Desk Support Engineer
8. Harvey Robinson — Junior Systems Engineer ($105-115k) — sent previous day

## Blocked
- Level 3 Service Desk Engineer (EFEX) — Angular form validation for text inputs could not be bypassed programmatically
- DMA Global Jr SWE — listing expired
- Various non-Sydney roles filtered out (Brisbane, Melbourne, Central Coast, Ballarat)
