# TrueNAS as a Container Host

## Docker Status on TrueNAS SCALE 25.x

- **Docker binary**: Present at `/usr/bin/docker` (v28.3.1)
- **Docker daemon**: Disabled at boot, `inactive (dead)` by default
- **Control**: Via systemd, NOT the TrueNAS middleware service list
- **Storage**: `/var/lib/docker` on `boot-pool/ROOT/25.10.3.1/var/lib` — overlay2 driver
- **Startup**: `systemctl start docker` — takes ~2 seconds
- **Enable at boot**: `systemctl enable docker`

## App API vs Raw Docker

| Action | Middleware API | Raw Docker (SSH) |
|--------|---------------|------------------|
| Install catalog app (Plex etc.) | ✅ `app.create` | ❌ |
| Run arbitrary container | ❌ `app.create` requires `catalog_app` | ✅ `docker run` |
| Pull image | ❌ | ✅ `docker pull` |
| Docker Compose | ❌ | ✅ |
| Manage volumes | ❌ | ✅ |

## API Probe Results

All methods confirmed to EXIST but fail for custom containers:

```python
# These ALL FAIL for custom images:
app.create({"image": "nginx", "name": "test"})
# → app_create.app_name: Field required
# → app_create.image: Extra inputs are not permitted
# → app_create.name: Extra inputs are not permitted

app.create({"app_name": "hermes", "version": "latest"})
# → Docker service is not running (if Docker not started)
# → Requires catalog_app if Docker IS running

# Working pattern:
app.create({"app_name": "inst", "catalog_app": "plex", ...})
```

## Boot Pool Capacity

- Size: ~42 GB (40 GB VDI in VirtualBox)
- Allocated: ~3.1 GB (includes system + Docker root at /var/lib/docker)
- Root dataset: 105 MB used, 36 GB free (ZFS compression hides actual on-disk size)
- Main concerns: tmpfs /run (KB-MB), not ZFS pool space
