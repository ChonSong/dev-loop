# Real-World Example: VirtualBox SATA Disk + RAM Benchmark

Measured June 15, 2026 on a VirtualBox VM (VBOX_HARDDISK, SATA) with 7.8 GiB RAM.

## Environment

- Host: VirtualBox, VM with 7.8 GiB RAM, 110 GiB virtual disk (SATA)
- OS: Linux 5.4.0-216-generic
- Swap: 2 GiB swapfile, 874 MiB used (43%)

## Results

### RAM

| Metric | Value |
|--------|-------|
| Sequential read | 15,425 MB/s (15.4 GB/s) |
| Sequential write | 2,076 MB/s (2.1 GB/s) |

### Disk (cold reads via posix_fadvise DONTNEED)

| Metric | Value |
|--------|-------|
| Sequential read (cold) | 270-580 MB/s |
| Sequential write (sync'd) | 710 MB/s (dd conv=fdatasync) |
| Random 4K latency (avg) | 0.77 ms |
| Random 4K latency (P50) | 0.73 ms |
| Random 4K latency (P99) | 1.38 ms |
| Random 4K IOPS | ~1,300 |

### Ratio

| Comparison | Ratio |
|-----------|-------|
| RAM read vs Disk cold read | ~27-57x |
| RAM latency vs Disk latency | ~7,700x |

## Interpretation

A 7B Q4 model (~4 GiB) would:
- **From RAM**: load in ~0.26s, generate tokens at ~20-50ms each
- **From swap (this disk)**: load in ~7-15s, generate tokens at ~7-15s each

Conclusion: SATA virtual disk is too slow for swap-backed interactive model inference. Only models fitting entirely in RAM are practical on this hardware.
