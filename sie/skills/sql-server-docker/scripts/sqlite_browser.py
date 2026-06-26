#!/usr/bin/env python3
"""
Lightweight SQLite web browser for ad-hoc database exploration.
Serves any SQLite database as a browsable web UI with:
  - Table listing (sorted by row count, searchable)
  - Paginated data browsing per table (100 rows/page)
  - Column headers displayed as sticky table headers

Usage:
  python3 sqlite_browser.py [--db /path/to/database.db] [--port 8765]
  socat TCP-LISTEN:8765,fork,reuseaddr TCP:172.19.0.2:8765 &  # expose from host
  # Open http://localhost:8765 in browser
"""

import sqlite3
import json
import argparse
import urllib.parse
import html
from http.server import HTTPServer, SimpleHTTPRequestHandler

def get_tables(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '\\_%' ESCAPE '\\' ORDER BY name")
    tables = [r[0] for r in c.fetchall()]
    conn.close()
    return tables

def get_table_info(db_path, table_name):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f'PRAGMA table_info("{table_name}")')
    columns = c.fetchall()
    c.execute(f'SELECT COUNT(*) FROM "{table_name}"')
    count = c.fetchone()[0]
    conn.close()
    return columns, count

def get_table_data(db_path, table_name, limit=100, offset=0):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f'PRAGMA table_info("{table_name}")')
    columns = [col[1] for col in c.fetchall()]
    c.execute(f'SELECT * FROM "{table_name}" LIMIT {limit} OFFSET {offset}')
    rows = c.fetchall()
    c.execute(f'SELECT COUNT(*) FROM "{table_name}"')
    total = c.fetchone()[0]
    conn.close()
    return columns, rows, total

def build_handler(db_path):
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            params = urllib.parse.parse_qs(parsed.query)

            if path == "/" or path == "/index.html":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()

                tables = get_tables(db_path)
                table_rows = [(t, get_table_info(db_path, t)[1]) for t in tables]
                total_rows = sum(r[1] for r in table_rows)

                html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SQLite Database Browser</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'SF Mono', 'Fira Code', monospace; background: #0d1117; color: #c9d1d9; padding: 1rem; }}
h1 {{ color: #58a6ff; font-size: 1.3rem; margin-bottom: 0.3rem; }}
.subtitle {{ color: #8b949e; font-size: 0.8rem; margin-bottom: 1rem; }}
.stats {{ display: flex; gap: 2rem; margin-bottom: 1.5rem; padding: 0.8rem; background: #161b22; border-radius: 8px; border: 1px solid #30363d; }}
.stat {{ text-align: center; }}
.stat-num {{ font-size: 1.5rem; color: #3fb950; font-weight: bold; }}
.stat-label {{ color: #6e7681; font-size: 0.7rem; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.75rem; }}
th {{ background: #161b22; color: #58a6ff; padding: 0.5rem; text-align: left; border-bottom: 2px solid #30363d; position: sticky; top: 0; }}
td {{ padding: 0.4rem 0.5rem; border-bottom: 1px solid #21262d; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
tr:hover td {{ background: #1c2128; }}
a {{ color: #58a6ff; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.search {{ margin-bottom: 1rem; }}
.search input {{ background: #161b22; border: 1px solid #30363d; color: #c9d1d9; padding: 0.5rem; border-radius: 6px; width: 300px; font-size: 0.8rem; }}
.search input:focus {{ outline: none; border-color: #58a6ff; }}
</style>
</head>
<body>
<h1> Database Browser</h1>
<p class="subtitle">{len(tables)} tables, {total_rows:,} rows</p>

<div class="stats">
<div class="stat"><div class="stat-num">{len(tables)}</div><div class="stat-label">Tables</div></div>
<div class="stat"><div class="stat-num">{total_rows:,}</div><div class="stat-label">Total Rows</div></div>
</div>

<div class="search">
<input type="text" id="search" placeholder="Search tables..." onkeyup="filterTables()">
</div>

<table id="tables">
<tr><th>Table</th><th>Rows</th><th>Columns</th></tr>
"""
                for t, count in sorted(table_rows, key=lambda x: -x[1]):
                    cols, _ = get_table_info(db_path, t)
                    html_content += f'<tr><td><a href="/table?name={urllib.parse.quote(t)}">{html.escape(t)}</a></td><td>{count:,}</td><td>{len(cols)}</td></tr>\n'

                html_content += """</table>
<script>
function filterTables() {
    var q = document.getElementById('search').value.toLowerCase();
    var rows = document.querySelectorAll('#tables tr:not(:first-child)');
    rows.forEach(function(row) {
        var name = row.cells[0].textContent.toLowerCase();
        row.style.display = name.includes(q) ? '' : 'none';
    });
}
</script>
</body>
</html>"""
                self.wfile.write(html_content.encode())

            elif path == "/table":
                table_name = params.get("name", [""])[0]
                if not table_name:
                    self.send_response(302)
                    self.send_header("Location", "/")
                    self.end_headers()
                    return

                page = int(params.get("page", [0])[0])
                limit = 100
                offset = page * limit

                try:
                    columns, rows, total = get_table_data(db_path, table_name, limit, offset)
                except Exception as e:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(f"<h1>Error: {html.escape(str(e))}</h1>".encode())
                    return

                total_pages = max(1, (total + limit - 1) // limit)

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()

                html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(table_name)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'SF Mono', 'Fira Code', monospace; background: #0d1117; color: #c9d1d9; padding: 1rem; }}
h1 {{ color: #58a6ff; font-size: 1.2rem; margin-bottom: 0.3rem; }}
.back {{ color: #58a6ff; font-size: 0.8rem; text-decoration: none; }}
.back:hover {{ text-decoration: underline; }}
.info {{ color: #8b949e; font-size: 0.8rem; margin-bottom: 1rem; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.7rem; }}
th {{ background: #161b22; color: #58a6ff; padding: 0.4rem; text-align: left; border-bottom: 2px solid #30363d; position: sticky; top: 0; white-space: nowrap; }}
td {{ padding: 0.3rem 0.4rem; border-bottom: 1px solid #21262d; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
tr:hover td {{ background: #1c2128; }}
.pagination {{ margin-top: 1rem; display: flex; gap: 0.5rem; align-items: center; }}
.pagination a {{ color: #58a6ff; text-decoration: none; padding: 0.3rem 0.6rem; background: #161b22; border-radius: 4px; }}
.pagination a:hover {{ background: #21262d; }}
.pagination span {{ color: #8b949e; }}
</style>
</head>
<body>
<a href="/" class="back">← Back to tables</a>
<h1>{html.escape(table_name)}</h1>
<p class="info">{total:,} rows, {len(columns)} columns — Page {page+1} of {total_pages}</p>

<table>
<tr>{''.join(f'<th>{html.escape(c)}</th>' for c in columns)}</tr>
"""
                for row in rows:
                    html_content += "<tr>" + "".join(
                        f"<td>{html.escape(str(v)) if v is not None else '<em style=\"color:#6e7681\">null</em>'}</td>" for v in row
                    ) + "</tr>\n"

                html_content += "</table>\n<div class='pagination'>"
                if page > 0:
                    html_content += f"<a href='/table?name={urllib.parse.quote(table_name)}&page={page-1}'>← Prev</a>"
                html_content += f"<span>Page {page+1} of {total_pages}</span>"
                if page < total_pages - 1:
                    html_content += f"<a href='/table?name={urllib.parse.quote(table_name)}&page={page+1}'>Next →</a>"
                html_content += "</div></body></html>"
                self.wfile.write(html_content.encode())

            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Suppress HTTP request logs

    return Handler

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQLite Database Browser")
    parser.add_argument("--db", default="/workspace/forrest-plan-and-track/data/onetag.db", help="Path to SQLite database")
    parser.add_argument("--port", type=int, default=8765, help="Port to serve on")
    args = parser.parse_args()

    handler = build_handler(args.db)
    server = HTTPServer(("0.0.0.0", args.port), handler)
    print(f"Server: http://localhost:{args.port}")
    print(f"DB:     {args.db}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
