---
name: github-repo-management
description: Clone/create/fork repos; manage remotes, releases.
categories: [github]
description: Clone, create, fork, and manage GitHub repositories.
external_skill: github/github-repo-management  # authoritative version lives there
---

# GitHub Repository Management

Clone, create, fork, and manage GitHub repositories. For the comprehensive reference (API cheatsheet, branch protection, releases, Actions, secrets, Pages, gists, and cleanup workflows), load the external skill `github/github-repo-management`.

## Target Disambiguation — Critical

When the user provides an **explicit GitHub URL** (as a URL in their message, not just a repo name), that URL is the authoritative target — not the repo in your current working directory.

**Trap:** Your working directory may be in one repo, but the user's URL points to another. Operating on the wrong repo because it's convenient is a real failure mode.

**Fix:** Compare the user's URL against `git remote get-url origin` in your current directory. If they differ, clone the user's URL and operate there. A correction like "i mean <URL>" is a **replacement** — discard your previous assumption.

## Pushing a local repo to a new GitHub repo

Use this flow when you have a local git repo with no remote and need to create the GitHub repo and push it:

```bash
# 1. Create the repo on GitHub (replace OWNER/org and REPO-NAME as needed)
GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/orgs/ChonSong/repos \
  -d '{"name":"REPO-NAME","description":"...","private":false}'

# 2. Add remote and push (using token in URL for auth)
git remote add origin "https://ChonSong:$GITHUB_TOKEN@github.com/ChonSong/REPO-NAME.git"
git push -u origin main

# 3. SECURITY: clean the embedded token from the remote URL immediately
git remote set-url origin https://github.com/ChonSong/REPO-NAME.git
```

### Pitfall: credential-embedded remote URL

When you push using a token in the remote URL (step 2), the token gets written to `.git/config` in plaintext. Running `git remote -v` after push exposes your GitHub token. **Always run step 3 immediately after pushing.** Future pushes/pulls can use a credential helper or SSH instead.

For the full skill (API cheatsheet, cloning, forking, branch protection, releases, Actions, secrets, Pages, gists, repo cleanup workflows, and the `gh` CLI equivalents), load:
