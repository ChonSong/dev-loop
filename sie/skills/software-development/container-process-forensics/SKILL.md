---
name: container-process-forensics
description: Debug processes in Linux containers with no ps/fuser/lsof/kill — using Python /proc traversal
tags: [debugging, containers, linux, process, port-conflict, forensics]
related_skills: [systematic-debugging, debug-live-website, debug-mantra]
---

# Container Process Forensics

Debug processes in Linux containers where standard tooling (ps, fuser, lsof, kill, netstat, ss) is missing. Use Python + /proc as the universal fallback.

## Quick Commands

### Check if a port is in use
```python
import socket
s = socket.socket()
s.settimeout(2)
r = s.connect_ex(('0.0.0.0', 8000))
s.close()
print('BUSY' if r == 0 else 'FREE')
```

### Find raw TCP listeners
```bash
# :1F40 = port 8000 hex, :0BB8 = port 3000 hex
cat /proc/net/tcp | awk '$2 ~ /:1F40/'
# Column 10 has the inode → use to find PID
```

### Find all processes by /proc traversal
```python
import os
for pid in os.listdir('/proc'):
    if not pid.isdigit(): continue
    try:
        cmdline = open(f'/proc/{pid}/cmdline', 'rb').read().decode('utf-8','ignore')
        if 'uvicorn' in cmdline and '8000' in cmdline:
            print(f'PID {pid}: {cmdline.replace(chr(0), " ")[:100]}')
    except: pass
```

### Kill a process without the kill command
```python
import os, signal
os.kill(int(pid), signal.SIGKILL)  # or 9
```

### Find which PID owns a socket
```python
import os
for pid in os.listdir('/proc'):
    if not pid.isdigit(): continue
    base = f'/proc/{pid}'
    try:
        for fd in os.listdir(f'{base}/fd'):
            lnk = os.readlink(f'{base}/fd/{fd}')
            if 'socket' in lnk:
                cmdline = open(f'{base}/cmdline', 'rb').read()[:200]
                # Check if it's the port we care about via /proc/net/tcp
    except: pass
```

### Check /proc/net/tcp format
Format: `sl local_addr:port rem_addr:port st tx_queue:rx_queue tr tm->when retrnsmt uid timeout inode`
- `local_addr:port` = hex IP and hex port (e.g. `00000000:1F40` = 0.0.0.0:8000)
- `st` = socket state (0A = TCP_LISTEN)
- `inode` = socket inode, matches `/proc/*/fd/*` readlink

### Port hex reference
| Port | Hex |
|------|-----|
| 3000 | 0BB8 |
| 3001 | 0BB9 |
| 3002 | 0BBA |
| 5432 | 1538 |
| 6379 | 18EB |
| 8000 | 1F40 |
| 8001 | 1F41 |
| 8002 | 1F42 |

## Pitfalls

- **os.kill needs permission**: OSError: [Errno 1] Operation not permitted → container may not have CAP_KILL
- **TIME_WAIT**: Socket appears in /proc/net/tcp but PID=0. The owning process already exited. Port won't be reusable until TIME_WAIT expires (~60s) or you set `net.ipv4.tcp_tw_reuse`.
- **Race condition**: /proc entries can vanish between stat and read — wrap in try/except
- **Symlink resolution**: /proc/PID/fd/* symlinks may point to 'socket:[inode]' — parse the inode, grep /proc/net/tcp for it

## When to Use

- Container has no ps/fuser/lsof/netstat
- Port conflict after restart (EADDRINUSE)
- Zombie process holding a port after being killed
- Process crashed silently and left the port bound
- Background task started with `background=true` exited but port is still held
