# Cloudflared Tunnel Setup - Reference

## Session Context
Setup of persistent Cloudflared tunnel for onetag.codeovertcp.com with secure authentication using provided credentials (sa/dawnofdarren).

## Key Configuration Files
- **Credentials**: `/home/hermeswebui/.hermes/cloudflared/onetag-creds.json`
- **Tunnel Config**: `/home/hermeswebui/.hermes/cloudflared/onetag-config.yml`
- **Binary**: `/home/hermeswebui/.hermes/bin/cloudflared`
- **Logs**: `/home/hermeswebui/.hermes/logs/onetag-tunnel.log`

## Troubleshooting Guide
### Error: "Failed to get tunnel"
**Cause**: Cloudflared cannot communicate with Cloudflare API or tunnel ID is incorrect.
**Fix**:
1. Verify tunnel ID in config matches Cloudflare dashboard
2. Ensure credentials file path is correct
3. Check network connectivity

### Error: "control stream encountered a failure"
**Cause**: Protocol negotiation issues
**Fix**:
1. Use HTTP/2 fallback (already configured)
2. Check firewall rules
3. Verify service on localhost:8501 is responding

## Credential Security
- File permissions: `chmod 600 onetag-creds.json`
- Never commit to version control
- Rotate after initial setup

## Verification Commands
```bash
# Check tunnel status
/home/hermeswebui/.hermes/bin/cloudflared tunnel --config /home/hermeswebui/.hermes/cloudflared/onetag-config.yml tunnel-status

# Test endpoint
curl -I http://onetag.codeovertcp.com

# Check logs
tail -f /home/hermeswebui/.hermes/logs/onetag-tunnel.log
```

## Related Sessions
- Initial tunnel setup with persistent requirements
- Credential management for secure authentication
- Background process management using Hermes terminal tool