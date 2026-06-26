#!/usr/bin/env python3
"""Audit skill library token consumption and produce a context budget report.
Usage: python3 /opt/data/skills/devops/context-budget/scripts/audit.py [skills_dir]
"""
import os, sys

skills_dir = sys.argv[1] if len(sys.argv) > 1 else '/opt/data/skills'
skills = []

for category in os.listdir(skills_dir):
    cat_path = os.path.join(skills_dir, category)
    if not os.path.isdir(cat_path):
        continue
    for skill_name in os.listdir(cat_path):
        skill_path = os.path.join(cat_path, skill_name, 'SKILL.md')
        if os.path.exists(skill_path):
            with open(skill_path, 'r') as f:
                content = f.read()
            lines = content.count('\n')
            words = len(content.split())
            tokens = int(words * 1.3)
            skills.append({
                'name': skill_name,
                'category': category,
                'lines': lines,
                'words': words,
                'tokens': tokens,
            })

skills.sort(key=lambda x: x['tokens'], reverse=True)
total_tokens = sum(s['tokens'] for s in skills)
total_lines = sum(s['lines'] for s in skills)
heavy = [s for s in skills if s['lines'] > 400]

print(f"Total skills: {len(skills)}")
print(f"Total lines: {total_lines:,}")
print(f"Total tokens: {total_tokens:,}")
print(f"Heavy skills (>400 lines): {len(heavy)}")
print(f"\nTop 10:")
for s in skills[:10]:
    print(f"  {s['name']:<35} {s['category']:<20} {s['lines']:>5}l  ~{s['tokens']:,}t")
