---
name: security/forensics
description: Use when performing digital forensics — file analysis, metadata extraction, memory forensics with Volatility, disk forensics with Sleuthkit, steganography detection, and chain of custody documentation.
version: 1.0.0
author: OWL
license: MIT
metadata:
  hermes:
    tags: [security, forensics, memory, disk, volatility, sleuthkit, steganography, autopsy, metadata]
    related_skills:
      - security/workflow
      - security/packet-analysis
      - security/tool-setup
---

# Digital Forensics

## Overview

Digital forensics covers the collection, preservation, analysis, and reporting of digital evidence. This skill includes file forensics (metadata, carving, steganography), memory forensics (Volatility), disk forensics (Sleuthkit/Autopsy), and chain of custody documentation.

## When to Use

- You need to analyze a suspicious file or image
- You need to extract metadata from documents or media
- You need to analyze a memory dump (RAM capture)
- You need to perform disk forensics (file recovery, timeline analysis)
- You need to detect steganography
- You're investigating a security incident
- You need to establish or maintain chain of custody

## Tool Availability Check

```bash
file --version
exiftool --version 2>&1 | head -1
binwalk --version 2>&1 | head -1
strings --version | head -1
volatility3 --version 2>&1 | head -1 || vol.py --info 2>&1 | head -1
fls --version 2>&1 | head -1
steghide --version 2>&1 | head -1
foremost --version 2>&1 | head -1
stegdetect --version 2>&1 | head -1
```

Install: `sudo apt install exiftool binwalk volatility3 sleuthkit steghide foremost stegdetect autopsy`

## Phase 1: File Forensics

### Initial Triage
```bash
# Identify file type (don't trust extensions)
file suspicious_file

# Check for embedded content
binwalk suspicious_file

# Extract strings
strings suspicious_file | head -100
strings -n 8 suspicious_file | sort -u    # Min 8 chars, deduplicated

# Hex dump
xxd suspicious_file | head -50
hexdump -C suspicious_file | head -50

# Check file size anomalies
ls -la suspicious_file
stat suspicious_file
```

### Metadata Extraction
```bash
# ExifTool — extract all metadata
exiftool suspicious_file
exiftool -a -u -g1 suspicious_file    # All metadata including unknown

# Extract specific fields
exiftool -Author -Creator -Producer suspicious_file
exiftool -GPS* suspicious_file         # GPS coordinates (photos)
exiftool -DateTimeOriginal suspicious_file

# Remove metadata (sanitization)
exiftool -all= suspicious_file

# Batch metadata extraction
exiftool -r -csv ./evidence/ > metadata_report.csv

# Check for hidden data in metadata
exiftool -v suspicious_file | grep -iE 'comment|description|keyword|user'
```

### File Hashing (Evidence Integrity)
```bash
# Generate hashes for evidence integrity
md5sum evidence_file
sha1sum evidence_file
sha256sum evidence_file

# Hash all files in a directory
find evidence_dir -type f -exec sha256sum {} \; > hashes.txt

# Verify hash
sha256sum -c hashes.txt
```

### File Carving (Extract Embedded Files)
```binwalk
# Scan for embedded files
binwalk suspicious_file

# Extract embedded files
binwalk -e suspicious_file

# Recursive extraction
binwalk -Me suspicious_file
```

```bash
# Foremost — file carving based on headers/footers
foremost -t all -i evidence_file -o foremost_output

# Specific file types
foremost -t jpg,png,zip,doc,pdf -i evidence_dir -o carved_output

# Configuration file for custom types
foremost -c /etc/foremost.conf -i evidence_file -o output
```

```bash
# Scalpel — another file carving tool
scalpel evidence_file -o scalpel_output

# photorec — photo/file recovery
photorec /dev/sda
photorec evidence_file
```

## Phase 2: Steganography Detection

### StegHide
```bash
# Check if steghide data is present
steghide info suspicious_image.jpg

# Extract hidden data (will prompt for passphrase)
steghide extract -sf suspicious_image.jpg -xf extracted_data.txt

# Extract with passphrase
steghide extract -sf suspicious_image.jpg -p "password" -xf extracted.txt
```

### Stegdetect
```bash
# Detect steganography in JPEGs
stegdetect suspicious_image.jpg

# Check multiple files
stegdetect *.jpg

# Output interpretation:
# negative = no stego detected
# weak = possible stego (low confidence)
# positive = likely stego detected
```

### StegSeek (Faster brute force for steghide)
```bash
# Brute force steghide with wordlist (much faster than manual)
stegseek suspicious_image.jpg /usr/share/wordlists/rockyou.txt

# If passphrase found, it extracts automatically
```

### Visual Steganography
```bash
# Extract LSB data with zsteg (PNG files)
zsteg suspicious_image.png

# Check specific bit planes
zsteg -b 1 suspicious_image.png     # LSB
zsteg -b 2 suspicious_image.png     # 2nd bit

# Common LSB extraction with Python
python3 -c "
from PIL import Image
img = Image.open('suspicious.png')
pixels = list(img.getdata())
bits = ''
for pixel in pixels:
    for channel in range(3):
        bits += str(pixel[channel] & 1)
# Convert bits to bytes
data = bytes([int(bits[i:i+8], 2) for i in range(0, len(bits), 8)])
print(data[:1000])
"
```

## Phase 3: Memory Forensics (Volatility 3)

> **Note:** Volatility 2 uses `vol.py`, Volatility 3 uses `volatility3`. This covers Volatility 3.

### Getting Started
```bash
# List available plugins
volatility3 -h

# Identify OS profile (Volatility 2)
vol.py -f memory.dmp imageinfo

# Volatility 3 auto-detects
volatility3 -f memory.dmp windows.info    # Windows
volatility3 -f memory.dmp linux.info      # Linux
volatility3 -f memory.dmp mac.info        # macOS
```

### Process Analysis
```bash
# List processes
volatility3 -f memory.dmp windows.pslist.PsList

# Process tree (parent-child relationships)
volatility3 -f memory.dmp windows.pstree.PsTree

# Detect hidden/unlinked processes
volatility3 -f memory.dmp windows.psscan.PsScan

# DLL list for a specific process
volatility3 -f memory.dmp windows.dlllist.DllList --pid 1234

# Command line arguments
volatility3 -f memory.dmp windows.cmdline.CmdLine
```

### Network Connections
```bash
# Active network connections
volatility3 -f memory.dmp windows.netscan.NetScan

# Network connections (Linux)
volatility3 -f memory.dmp linux.sockstat.SockStat

# Check for suspicious connections
volatility3 -f memory.dmp windows.netscan.NetScan | grep -E 'ESTABLISHED|LISTENING'
```

### Credential Extraction (Windows)
```bash
# Dump password hashes
volatility3 -f memory.dmp windows.hashdump.HashDump

# Dump cached domain credentials
volatility3 -f memory.dmp windows.lsadump.Lsadump

# Dump LSA secrets
volatility3 -f memory.dmp lsadump

#提取Vault凭证
volatility3 -f memory.dmp windows.vault.Vault
```

### Malware Detection
```bash
# Find injected code (hollowed processes)
volatility3 -f memory.dmp windows.malfind.Malfind

# Check for hooks
volatility3 -f memory.dmp windows.ssdt.SSDT

# Driver list (rootkits)
volatility3 -f memory.dmp modules

# Timeliner — create timeline of events
volatility3 -f memory.dmp timeliner.Timeliner
```

### File Extraction from Memory
```bash
# List files in memory
volatility3 -f memory.dmp windows.filescan.FileScan

# Extract a specific file
volatility3 -f memory.dmp windows.dumpfiles.DumpFiles --physaddr 0x12345678

# Extract all files matching a pattern
volatility3 -f memory.dmp filescan | grep "suspicious.exe" | \
  awk '{print $1}' | \
  xargs -I{} volatility3 -f memory.dmp dumpfiles --physaddr {}
```

### Linux Memory Forensics
```bash
# Process list
volatility3 -f memory.dmp linux.pslist.PsList

# Bash history
volatility3 -f memory.dmp linux.bash.Bash

# Check for LKM rootkits
volatility3 -f memory.dmp linux.check_modules.CheckModules

# Network connections
volatility3 -f memory.dmp linux.sockstat.SockStat
```

## Phase 4: Disk Forensics (Sleuthkit/Autopsy)

### Sleuthkit CLI
```bash
# List partitions
mmls evidence.disk

# File system info
fsstat evidence.disk

# List files in partition
fls -r -p evidence.disk

# List deleted files
fls -r -d -p evidence.disk

# Extract a file by inode
icat evidence.disk 12345 > extracted_file

# Extract a deleted file
icat -d evidence.disk 12345 > recovered_file

# Timeline analysis
fls -r -m / -p evidence.disk > bodyfile.txt
mactime -b bodyfile.txt > timeline.csv

# Find files by name
fls -r evidence.disk | grep -i "password\|secret\|confidential"
```

### Autopsy (GUI)
```bash
# Launch Autopsy
autopsy

# Workflow:
# 1. Create new case
# 2. Add data source (disk image, local disk, logical files)
# 3. Configure ingest modules:
#    - File Type Identification
#    - Extension Mismatch Detector
#    - Keyword Search
#    - PhotoRec Carver (deleted file recovery)
#    - Hash Lookup (known bad files)
#    - Email Parser
#    - Encryption Detection
#    - Interesting Files Finder
# 4. Analyze results
# 5. Tag and bookmark evidence
# 6. Generate report
```

### File Recovery
```bash
# Photorec — recover deleted files
photorec evidence.disk

# Testdisk — recover partitions
testdisk evidence.disk

# Foremost — carve files from disk
foremost -t all -i evidence.disk -o recovered_files

# Scalpel — advanced carving
scalpel evidence.disk -o carved_output
```

### Timeline Analysis
```bash
# Create bodyfile from disk
fls -r -m / -p evidence.disk > bodyfile.txt

# Add timeline entries
echo "0|/etc/passwd|12345|-r-xr-xr-x|0|0|1234|2024-01-15 10:30:00|2024-01-16 14:20:00|2024-01-14 08:15:00|0" >> bodyfile.txt

# Generate timeline
mactime -b bodyfile.txt -d > timeline.csv

# Filter timeline
mactime -b bodyfile.txt 2024-01-15..2024-01-16 > filtered_timeline.txt

# Using log2timeline (Plaso)
log2timeline.py evidence.plaso evidence.dump
psort.py -o l2tcsv evidence.plaso -w timeline.csv
pinfo.py evidence.plaso
```

## Phase 5: Chain of Custody

### Documentation Requirements
```markdown
## Evidence Item: ITEM-001

**Description:** Dell Laptop, Service Tag: ABC1234
**Acquired by:** [Name], [Title]
**Date/Time:** 2024-01-15 10:30 UTC
**Location:** [Address]
**Method:** Live acquisition via write-blocker

**Hashes:**
- MD5: `d41d8cd98f00b204e9800998ecf8427e`
- SHA1: `da39a3ee5e6b4b0d3255bfef95601890afd80709`
- SHA256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

**Chain of Custody:**
| Date/Time | From | To | Purpose |
|-----------|------|----|----------|
| 2024-01-15 10:30 | Investigator | Evidence Room | Secure storage |
| 2024-01-16 09:00 | Evidence Room | Lab | Analysis |
| 2024-01-16 17:00 | Lab | Evidence Room | Return to storage |
```

### Evidence Handling Rules
1. **Bit-for-bit copy** — always work on forensic images, never original media
2. **Write blockers** — use hardware or software write blockers
3. **Hash verification** — hash before and after every transfer
4. **Documentation** — every action, every tool, every finding
5. **Tamper evidence** — use tamper-evident bags for physical evidence
6. **Time synchronization** — use NTP for all forensic machines
7. **Work copies** — maintain original, working copy, and analysis copy

## Common Pitfalls

1. **Working on original media.** Always create a forensic image first (`dd`, `dcfldd`, `ftk-imager`). Never analyze the original.
2. **Not documenting hashes.** Without pre- and post-analysis hashes, your evidence is inadmissible.
3. **Volatility 2 vs 3 confusion.** Commands differ significantly. Verify which version you have.
4. **Not checking deleted files.** The most important evidence is often deleted. Always run `fls -d` or PhotoRec.
5. **Ignoring timestamps.** MAC times (Modified, Accessed, Created) are critical for timeline analysis. Always document them.
6. **Not using write blockers.** Even mounting a disk read-only can trigger writes (access time updates). Use hardware write blockers.
7. **Chain of custody gaps.** Every minute of undocumented custody is a vulnerability in court.

## Verification Checklist

- [ ] File type identified with `file` (not extension)
- [ ] Hashes generated (MD5, SHA1, SHA256) for all evidence
- [ ] Full metadata extracted with exiftool
- [ ] Embedded files checked with binwalk
- [ ] Strings extracted and reviewed
- [ ] Steganography checked (stegdetect, steghide, zsteg)
- [ ] Memory dump analyzed (processes, network, credentials, malfind)
- [ ] Disk image analyzed with Sleuthkit (files, deleted files, timeline)
- [ ] File carving performed (foremost/photorec)
- [ ] Timeline analysis completed
- [ ] Chain of custody documented for all evidence
- [ ] All findings documented with timestamps and tool versions
