#!/usr/bin/env python3
"""Essay QA checker — run after every draft."""
import re, sys

path = sys.argv[1] if len(sys.argv) > 1 else '/workspace/essay.md'
with open(path) as f:
    text = f.read()

body = text.split('## References')[0] if '## References' in text else text
paras = [p.strip() for p in body.split('\n\n') if p.strip()
         and not p.startswith('#') and not p.startswith('**')
         and not p.startswith('---')]

quotes = re.findall(r'"([^"]+)"', text)
long_q = [q for q in quotes if len(q.split()) > 20]
ai_words = ['serves as','stands as','underscoring','showcasing',
            'vital role','pivotal','distinctive','exceptional',
            'groundbreaking','monumental','testament','underscores']

wc = len(body.split())
all_ok = True

checks = [
    ("Word count", wc, True),
    ("Semi-colons", ';' in body, False),
    ("Contractions", any(re.search(r"\b(don't|doesn't|can't|won't|it's|that's)\b", body)), False),
    ("Dot points", '§' in text or '•' in text, False),
    ("AI vocabulary", any(w in body.lower() for w in ai_words), False),
    (f"Long quotes ({len(long_q)})", bool(long_q), False),
]

for label, result, invert in checks:
    if invert:
        ok = isinstance(result, int) and 1100 <= result <= 1300
    else:
        ok = not result
    tag = "OK" if ok else "FAIL"
    print(f"  [{tag}] {label}: {result if not isinstance(result, bool) else ''}")
    if not ok:
        all_ok = False

print(f"\nParagraphs ({len(paras)}):")
for i, p in enumerate(paras, 1):
    w = len(p.split())
    tag = " <<< LONG" if w > 110 else (" <<< SHORT" if w < 25 else "")
    print(f"  [{w:3d}w] {p[:55]}...{tag}")
    if w > 110 or w < 25:
        all_ok = False

print(f"\n{'✅ All checks passed' if all_ok else '❌ Issues found'}")
sys.exit(0 if all_ok else 1)