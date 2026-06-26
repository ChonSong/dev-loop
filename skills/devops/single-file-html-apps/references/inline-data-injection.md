# Inline Data Injection: Reproduction Recipe

## Problem Signature

- Site deployed to GitHub Pages shows black screen / no nodes / empty graph
- Browser DevTools shows no errors, but data appears absent
- `curl` shows data exists in the file, but after `</html>`

## Root Cause

The inline JSON data (`var D={...}` or `const GRAPH_DATA = {...}`) was placed **after** the closing `</html>` tag. HTML parsers stop at `</html>`; everything after is ignored.

## Detection

```bash
curl -s https://user.github.io/repo/index.html | grep -n '</html>'
curl -s https://user.github.io/repo/index.html | grep -n 'var D='   # or 'const GRAPH_DATA'
```

If `var D=` line number > `</html>` line number, the data is invisible.

## Fix: Rebuild with Proper Structure

### 1. Identify the base template

Find the last known-good commit with correct HTML structure:

```bash
git log --oneline -- index.html | head -20
# Check each commit for proper ordering:
git show COMMIT:index.html | grep -n 'const GRAPH_DATA\|</script>\|</body>\|</html>'
```

### 2. Use brace-counting replacement

See `scripts/validate-html-structure.py` for the full replacement function.

Key algorithm:
1. Find `const GRAPH_DATA =` marker
2. Start counting braces at first `{`
3. Increment on `{`, decrement on `}`
4. When depth returns to 0, you have found the matching `}`
5. Replace everything from marker through matching `}` with new JSON

### 3. Validate the output

Run the validation script from `scripts/validate-html-structure.py`:

```bash
python3 validate-html-structure.py index.html
```

Expected output:
```
const GRAPH_DATA at line 4623
</script> at line 1013954
</body> at line 1013964
</html> at line 1013971
PASS: correct ordering
Nodes: 821
Edges: 1298
```

### 4. Commit, push, wait

```bash
git add index.html
git commit -m "fix: correct inline data placement, N nodes, charge=C"
git push origin main
sleep 180  # Wait for CDN propagation
```

### 5. Verify live

```bash
curl -s "https://user.github.io/repo/?_=$(date +%s)" | grep -c 'const GRAPH_DATA'
```

Should return `1`.

## Historical Context

This pattern was discovered while fixing the Hermes Knowledge Graph deployment. The `rebuild-v3.py` script used naive string concatenation that appended data after `</html>`. The fix required switching to a brace-counting algorithm that operates inside the existing HTML structure rather than concatenating strings.