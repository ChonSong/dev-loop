---
name: system-benchmarking
description: Measure disk I/O, RAM bandwidth, and assess swap viability for model inference or memory-bound workloads. Python-driven hardware benchmarking with cold-read techniques.
---

# System Benchmarking — Disk, RAM & Swap Viability

Measure real hardware performance when answering "how fast is X" or "will Y run on this hardware."

## Principle: Test, Don't Estimate

Never estimate or back-of-napkin system performance numbers. Always run the actual benchmark. Users asking about speed or capacity want measured data, not speculation. Guessing wastes time and undermines trust — a 30-second dd or Python benchmark is worth more than a paragraph of theory.

Default to running the test before summarizing what you expect to find. Include both sequential throughput and random I/O latency, since model/swap workloads are sensitive to both.

## When to Activate

- User asks "should I increase swap" or "how much swap do I need"
- User asks about running a model on this hardware (swap-backed inference)
- User asks "how fast is this disk" or wants RAM vs disk comparison
- User challenges an estimate with "don't estimate, test it"
- Debugging why a model or database is slow — check if I/O is the bottleneck

## Disk Sequential Throughput (cold reads)

```python
import os, time

# Write a test file of known size
with open('/tmp/diskbench', 'wb') as f:
    f.write(b'\0' * (2 * 1024 * 1024 * 1024))  # 2GiB
os.system('sync')

fd = os.open('/tmp/diskbench', os.O_RDONLY)

# Evict file from kernel page cache for truly cold measurement
os.posix_fadvise(fd, 0, 2*1024*1024*1024, os.POSIX_FADV_DONTNEED)

start = time.perf_counter()
total = 0
while True:
    d = os.read(fd, 1024*1024)  # 1MiB chunks
    if not d:
        break
    total += len(d)
elapsed = time.perf_counter() - start
os.close(fd)

print(f"Cold sequential read: {total/1024/1024:.0f} MiB in {elapsed:.3f}s = {total/1024/1024/elapsed:.0f} MB/s")
```

**PITFALL**: Without `posix_fadvise(..., POSIX_FADV_DONTNEED)`, reads hit the page cache and report unrealistically high speeds (RAM speed, not disk speed). Always evict for cold measurements.

**PITFALL**: `O_DIRECT` often fails in VirtualBox / container environments with EINVAL due to alignment constraints. Use `posix_fadvise(DONTNEED)` instead — it's more portable and works without root.

## Disk Sequential Write (sync'd)

```bash
dd if=/dev/zero of=/tmp/diskbench bs=1M count=2048 conv=fdatasync 2>&1
```

The `conv=fdatasync` flag is critical — without it `dd` reports unwritten cache speeds.

## Disk Random 4K Latency (model paging simulation)

This is the key metric for swap-backed model inference. Models page in 4K blocks; high latency means unusable generation speeds.

```python
import os, time, random

fd = os.open('/tmp/diskbench', os.O_RDONLY)
block = 4096
num_ops = 200
times = []

for _ in range(num_ops):
    off = random.randint(0, 2000 - 1) * 1024 * 1024
    os.posix_fadvise(fd, max(0, off - 1024*1024),
                     min(2*1024*1024*1024, off + 2*1024*1024),
                     os.POSIX_FADV_DONTNEED)
    start = time.perf_counter()
    os.pread(fd, block, off)
    elapsed = time.perf_counter() - start
    times.append(elapsed * 1000)

os.close(fd)
times.sort()
avg = sum(times) / len(times)
p50 = times[len(times)//2]
p99 = times[int(len(times)*0.99)]
print(f"Avg: {avg:.2f}ms  P50: {p50:.2f}ms  P99: {p99:.2f}ms  IOPS: {1000/avg:.0f}")
```

## RAM Bandwidth

```python
import time
size = 512 * 1024 * 1024
buf = bytearray(size)
# Page it in
for i in range(0, size, 4096):
    buf[i] = 1

step = 1024 * 1024
start = time.perf_counter()
for off in range(0, size, step):
    _ = len(buf[off:off+step])
elapsed = time.perf_counter() - start
print(f"RAM sequential read: {size/1024/1024:.0f} MiB in {elapsed:.3f}s = {size/1024/1024/elapsed:.0f} MB/s")
```

**PITFALL**: A single Python `bytearray()` loop underutilizes memory bandwidth because it's serialize-and-interpret overhead bound rather than pure memory bandwidth. This is fine for relative comparisons against disk speeds — you're measuring orders-of-magnitude differences, not micro-optimizing.

## Swap Viability Assessment

To decide whether swap-backed model inference is practical:

1. **Benchmark disk**: cold sequential read (MB/s) and 4K random latency (ms)
2. **Benchmark RAM**: sequential read bandwidth (MB/s)
3. **Estimate model I/O**:
   - Model weight size = params × bytes_per_param (Q4 = 0.5 bytes/param, Q8 = 1 byte/param, FP16 = 2 bytes/param)
   - **Prompt processing** (sequential access): `model_size / disk_seq_read_speed` — one-time cost per prompt
   - **Token generation** (full model sweep per token): `model_size / disk_seq_read_speed` per token
4. **Compare against RAM**: `model_size / ram_read_speed` per token — the target

### Interpretation Guide

| Disk Type | Seq Read | 4K Latency | Viable for model on swap? |
|-----------|----------|------------|---------------------------|
| NVMe SSD | 3-7 GB/s | ~0.05 ms | Marginal — 1-2 tok/s for 7B Q4 |
| SATA SSD | 400-600 MB/s | ~0.1 ms | No — 7-15s/token for 7B Q4 |
| SATA HDD | 100-200 MB/s | ~5-15 ms | No — 20-40s/token for 7B Q4 |
| RAM | 15-30 GB/s | ~0.0001 ms | Yes — baseline target |

### Practical Thresholds (7B Q4 model ~4 GiB)

- Disk slower than 2 GB/s sequential: swap-backed generation < 2 tokens/second — interactive unusable
- Random 4K latency above 0.5 ms: paging during sparse attention patterns causes perceptible stutter
- If model fits entirely in available RAM: always prefer RAM — disk is never worth it for real-time use
