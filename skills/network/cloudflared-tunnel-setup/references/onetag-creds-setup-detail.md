# Onetag Credential Setup

## Purpose
Secure credential storage for Cloudflare tunnel to onetag.codeovertcp.com

## Configuration File
Set up with:
```bash
cat > ~/.hermes/cloudflared/onetag-creds.json << 'EOF'
{
  "username": "sa",
  "password": "dawnofdarren"
}
EOF
```

## Permission Check
```bash
chmod 600 ~/.hermes/cloudflared/onetag-creds.json
```

## Integration
Reference in tunnel config:
```yaml
credentials-file: /home/hermeswebui/.hermes/cloudflared/onetag-creds.json
```