# SMB Guest Access on TrueNAS SCALE 25.x

TrueNAS SCALE 25.x (Dragonfish/Electric Eel+) removed the per-share `guestok` parameter. Guest access is instead configured through global SMB service options combined with filesystem ACLs.

## Configuration Path

### 1. SMB Service Config
```python
call("smb.update", [{
    "smb_options": "map to guest = Bad User\nserver signing = disabled"
}])
call("service.restart", ["cifs"])
```

This sets two Samba parameters:
- `map to guest = Bad User` — maps failed authentications to the guest account
- `server signing = disabled` — required because guest sessions can't sign

### 2. Dataset ACL
Set the shared dataset to allow `everyone@` full control:
```python
call("filesystem.setacl", [{"/mnt/path/share": {
    "acl": [
        {"tag": "owner@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}},
        {"tag": "group@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}},
        {"tag": "everyone@", "type": "ALLOW", "perms": {"BASIC": "FULL_CONTROL"}, "flags": {"BASIC": "INHERIT"}}
    ],
    "options": {"recursive": false, "traverse": false}
}}])
```

### 3. SMB Service Already Has
- `guest: "nobody"` — the guest account user (default)
- SMB is running (`service.query` → `cifs`)

## Client Compatibility

| Client | Guest Access | Notes |
|--------|-------------|-------|
| Windows 10/11 | ❌ | Disables insecure guest auth by default — enable via Group Policy or registry |
| smbprotocol (Python) | ⚠️ | Works when signing disabled; truly anonymous auth fails with SPNEGO error |
| macOS Finder | ⚠️ | Connect as "Registered User" with username `nobody` and empty password |
| Linux smbclient | ⚠️ | `-U nobody%` or `-U guest%` |

## Recommended Alternative: Dedicated User

Instead of fighting with guest access, create a dedicated user with a simple password:

```python
call("user.create", [{
    "username": "shared",
    "full_name": "Shared Access",
    "password": "shared1",
    "group_create": True,
    "smb": True,
    "shell": "/usr/sbin/nologin",
    "home": "/var/empty",
    "home_create": False,
    "locked": False
}])
```

This is more reliable across different SMB clients and versions.

## Troubleshooting

- **"SMB encryption or signing was required"** — server signing is mandatory. Set `server signing = disabled` in smb_options and restart SMB.
- **"pututline() failed: No space left"** — TrueNAS root filesystem is full. Delete old boot environments or expand the disk.
- **"Extra inputs are not permitted" on `guestok`** — `guestok` was removed in TrueNAS SCALE 25.x. Use `map to guest = Bad User` in smb_options instead.
- **Guest user can't write** — the dataset ACL needs `everyone@` with FULL_CONTROL and INHERIT flags.
