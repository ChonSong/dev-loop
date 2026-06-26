# SSH Troubleshooting — Roadmap Engine Access

## What was tested

| Target | Command | Result |
|--------|---------|--------|
| `sean@localhost` | `ssh -i /opt/data/home/.ssh/id_ed25519 sean@localhost` | Permission denied — key offered but rejected |
| `sean@172.19.0.1` | `ssh -i /opt/data/home/.ssh/id_ed25519 sean@172.19.0.1` | Permission denied |
| `sean@192.168.1.117` | `ssh -i /opt/data/home/.ssh/id_ed25519 sean@192.168.1.117` | Permission denied |
| Verbose trace | `ssh -v -i ... sean@localhost` | Key SHA256 offered, server responds "Authentications that can continue: publickey,password" then rejects without trying password |

## Key facts established

- **Actual SSH key:** `/opt/data/home/.ssh/id_ed25519` (container `$HOME=/opt/data/home`)
- **Key comment:** `hermes-container`
- **Fingerprint:** `SHA256:sue0wfFk9mnlVvsKYtYbzGPFBphUNnkgeRE+Ffw1e+0`
- **In authorized_keys:** Yes — `hermes-container` key appears 4× in `/home/sean/.ssh/authorized_keys`
- **OpenSSH version mismatch:** Container client 10.0 vs host server 10.3
- **SHA256 matches:** Key offered by client === key in authorized_keys (confirmed)

## Root cause hypothesis

The server is actively blocking authentication for the `hermes-container` key — not failing to find it. The server:
1. Accepts the TCP connection
2. Offers auth methods (publickey, password)
3. Receives the key
4. Immediately rejects it — without attempting to verify it against authorized_keys

This pattern strongly suggests a `Match` block in `/etc/ssh/sshd_config` that explicitly blocks or limits the `hermes-container` key, or the authorized_keys entry has a forced-constraint (from-prefix directive, `restrict` command, etc.) that makes the key unusable in this direction.

**To fix on the host:**
1. Check `/etc/ssh/sshd_config` for `Match` blocks affecting this key or user
2. Verify the key entry in `/home/sean/.ssh/authorized_keys` is not prefixed with options that restrict it
3. Try adding the key to a different user account's `authorized_keys` as a test
4. Consider switching to password auth (temporary) or deploying a new key pair with a known-good format

## Fallback procedure

When SSH fails consistently:
1. Read `roadmap.json` from the host via one-shot SSH: `ssh -i /opt/data/home/.ssh/id_ed25519 sean@localhost "cat /home/sean/.hermes/hermes-sync/workspace/plans/roadmap.json"`
2. Generate Phase 3 narrative report from the roadmap data
3. Mark the report `[ENGINE STOPPED — SSH unreachable]` in the header
4. Deliver as the cron output

Do NOT fall back to running the engine against the container's `/opt/data/hermes-sync/` snapshot — it is stale and read-only.