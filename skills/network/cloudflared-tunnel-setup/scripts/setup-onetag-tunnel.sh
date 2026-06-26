#!/bin/bash
# Setup script for onetag.codeovertcp.com tunnel credentials

CRED_FILE="$HOME/.hermes/cloudflared/onetag-creds.json"
CONFIG_FILE="$HOME/.hermes/cloudflared/onetag-config.yml"
SCRIPT_DIR="$HOME/.hermes/scripts"

# Create directories
mkdir -p "$(dirname "$CRED_FILE")"
mkdir -p "$SCRIPT_DIR"

# Create credentials with proper permissions
cat > "$CRED_FILE" << 'EOF'
{
  "username": "sa",
  "password": "dawnofdarren"
}
EOF

chmod 600 "$CRED_FILE"

# Create tunnel config template
cat > "$CONFIG_FILE" << EOF
tunnel: <TUNNEL-ID>
credentials-file: $CRED_FILE
ingress:
  - hostname: onetag.codeovertcp.com
    service: http://localhost:8501
  - service: http_status:404
EOF

echo "✓ Credentials and config created"
echo "  - Creds: $CRED_FILE"
echo "  - Config: $CONFIG_FILE"