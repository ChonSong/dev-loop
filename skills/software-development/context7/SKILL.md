---
name: context7
description: Context7 MCP tools — resolve library IDs and query up-to-date documentation for any programming library or framework. Use when you need current API docs, code examples, migration guides, or best practices.
category: software-development
---

# Context7 — Live Documentation for Hermes

Context7 provides up-to-date code documentation and examples for 5700+ libraries and frameworks. It's available as MCP tools in this session.

## Tools Available

- **`mcp_context7_resolve_library_id(query, libraryName)`** — Find the exact Context7 library ID for a package. Call this FIRST before querying.
- **`mcp_context7_query_docs(libraryId, query)`** — Get documentation and code examples for a specific library. Max 3 calls per question.

## When to Use

Use Context7 whenever you need to:

- Write code against an unfamiliar API (any npm/pip/crate/gem package)
- Check the latest API for a library you know (things change between versions)
- Compare approaches between libraries (e.g., "how does Express vs Fastify handle auth")
- Find migration guides (e.g., "React 18 to React 19 changes")
- Get best practices from official documentation
- Resolve deprecation warnings or breaking changes

Do NOT use for:
- General web searches (use web_search instead)
- Questions about Sean's own code or projects
- Debugging existing application code

## Workflow

### Step 1: Resolve Library ID

```python
# Call resolve_library_id first with the library name
mcp_context7_resolve_library_id(
    libraryName="Express.js",
    query="How to set up JWT authentication in Express.js"
)
```

The tool returns matching libraries with their Context7 IDs (format: `/org/project`), code snippet counts, benchmark scores, and version info.

### Step 2: Query Documentation

```python
# Use the library ID from step 1
mcp_context7_query_docs(
    libraryId="/expressjs/express",
    query="JWT authentication middleware with async/await patterns"
)
```

### Step 3: Apply the knowledge to the task

Use the documentation to inform the code you're writing. Context7 returns real, up-to-date code examples from the library's actual docs — not model-generated approximations.

## Library Resolution Tips

| If you want docs for | Search with libraryName |
|---|---|
| Any npm package | The exact npm package name (e.g. "zod", "express", "next") |
| Python packages | The PyPI name (e.g. "fastapi", "pydantic", "sqlalchemy") |
| Rust crates | The crate name (e.g. "tokio", "serde") |
| Go modules | The module path (e.g. "gin-gonic/gin") |
| Major frameworks | The framework name (e.g. "React", "Vue.js", "Angular") |
| Databases | "MongoDB", "PostgreSQL", "Redis" |
| Cloud providers | "AWS SDK", "Google Cloud", "Azure SDK" |

## Limitations

- Max 3 query_docs calls per question
- Library ID must be resolved before querying (unless user provides explicit `/org/project/version` format)
- Best results with specific queries (not "how do I use this" but "how do I set up JWT auth with async/await")
- Works best for well-documented libraries with active maintenance

## Related Skills

- seans-reporepo-query — find similar libraries from the catalog
- e2e-testing — writing tests against library APIs
