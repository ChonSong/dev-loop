# Skill Retrieval Workflow

When you encounter a skill that is an empty stub (frontmatter only, no actual content), follow this order:

## 1. Try Registry Retrieval First

    hermes skills inspect <name>    # Preview without installing
    hermes skills search <query>    # Search registries
    hermes skills install <name>    # Install fresh from registry

## 2. If Registry Unreachable (Container Network Issues)

Try via host SSH:

    ssh sean@localhost "hermes skills install <name>"

## 3. Direct GitHub Clone

If GitHub is accessible, clone the source repo:

    git clone --depth 1 https://github.com/<owner>/<repo>.git /tmp/<repo>

Then copy the real SKILL.md over the stub:

    cp /tmp/<repo>/skills/<skill>/SKILL.md ~/.hermes/skills/<category>/<skill>/SKILL.md

## 4. Known Source Repos

| Repo | Skills | Notes |
|------|--------|-------|
| `deanpeters/Product-Manager-Skills` | 46 PM skills: PRD, personas, journeys, stories, metrics, etc. | Full content, well-structured |
| `phuryn/pm-skills` | 65 PM lifecycle skills: PRD, competitor analysis, prioritization, etc. | Full content, well-structured |
| `coreyhaines31/marketingskills` | 43 marketing skills: CRO, onboarding, customer research, etc. | Full content + CLI tools |
| `google-labs-code/stitch-skills` | 13 design/code skills: design-md, enhance-prompt, shadcn-ui, etc. | Under `plugins/` not `skills/` |
| `anthropics/skills` | doc-coauthoring, frontend-design, canvas-design, web-artifacts-builder | Under `skills/` subdir |
| `firecrawl/skills` | 5 build/integration skills | Under `skills/` subdir |
| `vercel-labs/next-skills` | 3 Next.js skills | Under `skills/` subdir |
| `mattpocock/mattpocock-skills` | to-prd, design-an-interface, request-refactor-plan | Source of truth for stubs with `source: mattpocock-skills` |
| `0xNyk` repos | hermes-skill-marketplace, hermes-skill-distillation | Mostly stubs; check individual repos |
| `VoltAgent/awesome-agent-skills` | Index only (README with 1000+ skill links) | Not a skill repo; use to find real sources |

## 5. GitHub API Approach (when git clone is blocked)

Use `execute_code` with `urllib.request` to fetch via GitHub API:

```python
import urllib.request, json

def fetch_skill(owner, repo, path):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    if isinstance(data, list):
        for item in data:
            if item["name"] == "SKILL.md":
                with urllib.request.urlopen(item["download_url"], timeout=10) as dl:
                    return dl.read().decode("utf-8")
    return None
```

## 6. Last Resort: Reconstruct

Only if all retrieval attempts fail. Mark at top of SKILL.md:

    > RECONSTRUCTED - original source unavailable. May not reflect author's intent.

Retain the original `source:` frontmatter field so future sessions know where it came from.

## 7. Known Empty Stub Patterns

Skills from voltagent, mattpocock-skills, and 0xNyk sources are systematically empty stubs (frontmatter-only). Assume they are stubs until proven otherwise. Always check the source repo first.
