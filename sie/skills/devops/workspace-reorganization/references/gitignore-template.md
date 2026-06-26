# .gitignore Template for Workspace Reorganizations

## Usage
Paste this as `.gitignore` at workspace root after a reorganization.

```gitignore
# ===== Workspace .gitignore =====

# --- Node ---
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# --- Python ---
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/
*.egg

# --- OS ---
.DS_Store
Thumbs.db
*~
.~lock.*

# --- Secrets ---
.env
.env.*
*.token
*-token.json
*-creds.json
*-credentials.json
client_secret*.json
*.pem
*.key

# --- Media ---
*.mp4
*.mov
*.avi
*.mkv
*.webm
*.png
*.jpg
*.jpeg
*.gif
*.webp
*.pdf

# --- Fonts ---
*.otf
*.ttf
*.woff
*.woff2

# --- Databases ---
*.db
*.sqlite
*.sqlite3
*.csv

# --- Archives ---
*.zip
*.tar
*.tar.gz
*.tgz

# --- Logs ---
*.log
logs/

# --- Embedded git repos (customize per workspace) ---
agent-ops/
codi/
gto-wizard-clone/
hermes-guide/
hermes-knowledge-graph/
open-lovable/
screenshot-to-code/
seans-reporepo/

# --- Backup dirs ---
archive/
```
