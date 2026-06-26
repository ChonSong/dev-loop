# Google Drive via ocamlfuse

## OAuth Credentials (Sean's account)

- **Client ID:** `596071327960-9be70fpnvvq8mlr5349epc1ur2r17hhn.apps.googleusercontent.com`
- **Client Secret:** `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` (correct — setup-google-drive.sh may have stale value `GOCSPX-IvbZ`)
- **Account:** `seanos1a@gmail.com`

These are stored in hermes-sync/setup-google-drive.sh and are the same credentials used for Google Workspace APIs (Gmail, Calendar, Drive).

## Setup Script

`setup-google-drive.sh` in hermes-sync root performs the full install + auth flow on Ubuntu/Debian.

## Key Commands

```bash
# Mount
google-drive-ocamlfuse ~/GoogleDrive

# Unmount
fusermount -u ~/GoogleDrive

# Remount (after reboot)
google-drive-ocamlfuse ~/GoogleDrive
```

## Prereqs

- Ubuntu/Debian (requires `add-apt-repository` → PPA)
- FUSE kernel module (`/dev/fuse`)
- Google account (no 2FA restriction since using OAuth client, not App Password)

## Limitations

- Read/write access — Google Docs/Drive files appear as binary blobs (not editable in-place)
- File changes made locally sync TO Drive (bidirectional)
- If `/dev/fuse` is missing, the host kernel doesn't support FUSE — use rclone as an alternative

## Alternative: rclone (works without FUSE)

If FUSE isn't available (some VPSes, containers), use rclone instead:

```bash
curl https://rclone.org/install.sh | sudo bash
rclone config  # choose: new remote → google drive → auto-config
rclone mount gdrive: ~/GoogleDrive --vfs-cache-mode full &
```

rclone can also do one-way sync (no mounting):
```bash
rclone sync gdrive: ~/GoogleDrive/ --drive-root-folder-id "" -P
```
