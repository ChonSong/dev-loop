# D3 Graph Deployment Verification Recipes

## Playwright Headless Testing on Remote Hosts

When running Playwright tests against a deployed page on a remote Linux host (where `google-chrome-stable` is installed but display-server access is unavailable), use this pattern:

### 1. Write the test script to a local file first

```javascript
// /tmp/pw_check.js
const { chromium } = require('/tmp/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome-stable',
    args: ['--no-sandbox', '--disable-gpu', '--headless=new'],
  });
  const page = await browser.newPage();
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  await page.goto('https://chonsong.github.io/hermes-guide/skills-graph.html', { waitUntil: 'networkidle', timeout: 20000 });
  await page.waitForTimeout(3000);
  const svgExists = await page.evaluate(() => !!document.querySelector('svg'));
  const circles = await page.evaluate(() => document.querySelectorAll('circle').length);
  const lines = await page.evaluate(() => document.querySelectorAll('line').length);
  console.log('TITLE:', await page.title());
  console.log('SVG exists:', svgExists);
  console.log('Circles (nodes):', circles);
  console.log('Lines (links):', lines);
  console.log('ERRORS:', JSON.stringify(errors));
  await browser.close();
})();
```

### 2. Copy to remote host and execute with timeout

```bash
cat /tmp/pw_check.js | ssh -i ~/.hermes/container_key sean@172.19.0.1 "cat > /tmp/pw_check.js && timeout 30 node /tmp/pw_check.js"
```

### 3. Expected output (good state)

```
TITLE: Hermes Skills — Interactive Graph
SVG exists: true
Circles (nodes): 1204
Lines (links): 1
ERRORS: []
```

### Why this pattern works

- `ssh host "python3 -c '...complex code...'"` hits shell quote escaping limits with complex Python strings
- Inline `node -e` has the same problem
- Writing to file first and piping via stdin avoids escaping issues
- `timeout 30` wrapper prevents hangs from becoming long blocks
- `google-chrome-stable` (full browser) hangs in `--headless=new` mode on some Linux without display server — `timeout` saves you

## Skill Data Extraction (Python, Remote Host)

When you need to extract/process JSON data on the remote host:

```python
#!/usr/bin/env python3
# /tmp/get_skills.py — example: extracting skill metadata
import json

meta = json.load(open('/home/sean/.hermes/skill-selector-cache/skill_metadata.json'))
# metadata.json is a list, not dict
skills = [
    {'name': s['name'], 'description': s.get('description', ''),
     'category': s.get('category', 'uncategorized'),
     'tags': s.get('tags', []),
     'size_mb': s.get('size_mb', 0),
     'is_local': s.get('is_local', False),
     'source': s.get('source', '')}
    for s in meta
]
lines = ['const SKILLS = [']
for s in skills:
    lines.append(json.dumps(s, separators=(',', ':')) + ',')
lines.append(' ];')
open('/tmp/full_skills_raw.txt', 'w').write('\n'.join(lines))
print(len(skills), 'skills written')
```

## Merging Large Skill Arrays Into HTML Files

When replacing a large embedded data array in an HTML file:

```python
#!/usr/bin/env python3
import re
SKILLS_FILE = '/tmp/full_skills_raw.txt'
RADIAL_FILE = '/home/sean/workspace/hermes-guide/docs/skills-graph.html'
OUT = '/tmp/skills-graph-merged.html'

# Load full skills array
with open(SKILLS_FILE) as f:
    raw = f.read()
m = re.search(r'(const SKILLS = \[.*?\];)', raw, re.DOTALL)
full_skills = m.group(1)

# Load HTML shell and replace the old (small/broken) SKILLS block
with open(RADIAL_FILE) as f:
    html = f.read()
m2 = re.search(r'(const SKILLS = \[.*?\];)', html, re.DOTALL)
new_html = html[:m2.start()] + full_skills + html[m2.end():]

with open(OUT, 'w') as f:
    f.write(new_html)

skill_count = len(re.findall(r'"name":', new_html))
print(f"Skills: {skill_count} (should be 3928)")
```

## Signatures of a Broken Graph (before fixes)

| Symptom | Root Cause |
|---------|------------|
| Browser 5GB RAM on load | O(n²) edge creation (full pair grid) |
| Page unresponsive | D3 force simulation on 4000+ nodes |
| 0 nodes in SVG | JS exception before graph build |
| Nodes all in center | simulation.alpha never restarted |
| Duplicate CATEGORY_MAP | `const CATEGORY_MAP = {...}` declared twice → syntax error |