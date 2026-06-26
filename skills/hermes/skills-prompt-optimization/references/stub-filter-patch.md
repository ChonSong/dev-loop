# Stub Filter Patch for prompt_builder.py

## Problem

2,538 of 2,761 skills are empty stubs (fewer than 10 body lines after frontmatter). They inflate the skill index by ~75K chars (~18K tokens) with zero informational value.

## Solution

Filter stubs from skills_by_category before building the index.

## Where

File: `/app/venv/lib/python3.12/site-packages/agent/prompt_builder.py`
Location: After skills are collected into skills_by_category (~line 1162), before the index-building logic.

## Code

```python
STUB_THRESHOLD = 10

def _is_stub(skill_name, category):
    for base in [SKILLS_DIR, *EXTERNAL_SKILLS_DIRS]:
        path = base / category / skill_name / "SKILL.md"
        if not path.exists():
            path = base / f"{category}-{skill_name}" / "SKILL.md"
        if path.exists():
            lines = path.read_text().split('\n')
            body = 0
            in_front = False
            for l in lines:
                if l.strip() == '---':
                    in_front = not in_front
                    continue
                if not in_front and l.strip():
                    body += 1
            return body < STUB_THRESHOLD
    return True

if skills_by_category:
    for cat in list(skills_by_category.keys()):
        skills_by_category[cat] = [
            (n, d) for n, d in skills_by_category[cat]
            if not _is_stub(n, cat)
        ]
        if not skills_by_category[cat]:
            del skills_by_category[cat]
```

## Expected Impact

- Skills in index: 2,761 -> ~223 (non-stub)
- Index chars: 83,701 -> ~20K-25K
- Index tokens: ~20,925 -> ~5K-6K
- Total prompt savings: ~14K tokens per turn

## Verification

1. build_skills_system_prompt() < 30K chars for index
2. skill_view("hermes-agent") still works
3. Only non-stub entries in index
4. Wrapper tags still present

## Re-application

Re-apply after each hermes-agent update. Same location as vendor grouping patch.
