#!/usr/bin/env python3
"""Validate single-file HTML app structure after inline data injection.

Usage:
    python3 validate-html-structure.py index.html

Checks:
    1. const GRAPH_DATA marker exists
    2. </script> exists after GRAPH_DATA
    3. </body> exists after </script>
    4. </html> exists after </body>
    5. JSON data is parseable (extracts and validates node/edge counts)
"""

import json
import re
import sys

def validate(html_path: str) -> dict:
    with open(html_path) as f:
        content = f.read()
    lines = content.split('\n')
    
    # Find line numbers
    def find_line(pattern):
        for i, line in enumerate(lines, 1):
            if pattern in line:
                return i
        return -1
    
    graph_line = find_line('const GRAPH_DATA')
    script_line = find_line('</script>')
    body_line = find_line('</body>')
    html_line = find_line('</html>')
    
    print(f"const GRAPH_DATA at line {graph_line}")
    print(f"</script> at line {script_line}")
    print(f"</body> at line {body_line}")
    print(f"</html> at line {html_line}")
    
    errors = []
    if graph_line == -1:
        errors.append("FAIL: const GRAPH_DATA not found")
    if script_line == -1:
        errors.append("FAIL: </script> not found")
    if body_line == -1:
        errors.append("FAIL: </body> not found")
    if html_line == -1:
        errors.append("FAIL: </html> not found")
    
    if not errors:
        if not (graph_line < script_line < body_line < html_line):
            errors.append(f"FAIL: incorrect ordering (expected {graph_line} < {script_line} < {body_line} < {html_line})")
        else:
            print("PASS: correct ordering")
    
    # Extract and validate JSON
    marker = 'const GRAPH_DATA ='
    start = content.find(marker)
    if start != -1:
        brace_start = content.find('{', start)
        depth = 0
        end = brace_start
        for i, ch in enumerate(content[brace_start:], brace_start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            if depth == 0:
                end = i + 1
                break
        json_str = content[brace_start:end]
        try:
            data = json.loads(json_str)
            nodes = len(data.get('nodes', []))
            edges = len(data.get('edges', []))
            print(f"Nodes: {nodes}")
            print(f"Edges: {edges}")
            return {"ok": len(errors) == 0, "errors": errors, "nodes": nodes, "edges": edges}
        except json.JSONDecodeError as e:
            errors.append(f"FAIL: JSON parse error: {e}")
    
    for e in errors:
        print(e)
    return {"ok": False, "errors": errors, "nodes": 0, "edges": 0}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 validate-html-structure.py <index.html>")
        sys.exit(1)
    result = validate(sys.argv[1])
    sys.exit(0 if result["ok"] else 1)
