# dockerode Async/Sync Discrepancy: container.logs() and container.stats()

## The Problem

`dockerode` methods `container.logs()` and `container.stats()` return **synchronous `ReadableStream` locally** (Node.js direct return), but **CI's `@types/dockerode` types them as `Promise<ReadableStream>`** — async.

**CI error when using `await`:**
```
error TS2345: Argument of type 'Promise<ReadableStream>' is not assignable
to parameter of type 'ReadableStream'.
error TS2339: Property 'on' does not exist on type 'Promise<ReadableStream>'.
```

**Root cause:** Different `@types/dockerode` versions between local and CI. CI resolves `^latest`, local has an older pinned version.

## The Fix: Use `.then()` Instead of `await`

Always use `.then()` when writing dockerode stream code. It works synchronously locally AND passes CI's async types.

```typescript
// WRONG — fails in CI even though it works locally:
const stream = await docker.getContainer(name).logs({
  stdout: true, stderr: true, follow: true, timestamps: true, tail: 0,
});
stream.on('data', (chunk: Buffer) => { ... });
stream.on('end', () => { ... });

// RIGHT — works in both:
docker.getContainer(name).logs({
  stdout: true, stderr: true, follow: true, timestamps: true, tail: 0,
}).then((stream: NodeJS.ReadableStream) => {
  let buffer = '';
  let timer: ReturnType<typeof setTimeout> | null = null;

  const flush = () => {
    // emit buffered lines
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    const now = new Date().toISOString();
    lines.forEach(msg => {
      if (!msg.trim()) return;
      io.emit('log', { ts: now, level: 'INFO', component: name, msg });
    });
  };

  stream.on('data', (chunk: Buffer) => {
    // Docker stream framing: 8-byte header per line
    let offset = 0;
    const buf = Buffer.from(chunk);
    while (offset < buf.length) {
      if (buf.length - offset < 8) { buffer += buf.slice(offset).toString(); break; }
      const header = buf.slice(offset, offset + 8);
      const size = header.readUInt32BE(4);
      offset += 8;
      if (offset + size > buf.length) { buffer += buf.slice(offset).toString(); break; }
      const line = buf.slice(offset, offset + size).toString();
      offset += size;
      // Strip Docker ISO timestamp prefix
      const tsMatch = line.match(/^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s*([\s\S]*)/);
      if (tsMatch?.[2].trim()) buffer += tsMatch[2] + '\n';
      else if (line.trim()) buffer += line + '\n';
    }
    // Batch emit every 500ms
    if (!timer) timer = setTimeout(() => { flush(); timer = null; }, 500);
  });

  stream.on('end', () => { flush(); containerStreams.delete(name); });
  stream.on('error', () => { flush(); containerStreams.delete(name); });
}).catch(() => { containerStreams.delete(name); });
```

## Same Pattern for `container.stats({ stream: false })`

```typescript
// WRONG in CI:
const stats = await docker.getContainer(id).stats({ stream: false });
const cpu = stats.cpu_stats?.cpu_usage?.total_usage ?? 0;

// RIGHT:
docker.getContainer(id).stats({ stream: false }).then((stats: StatsInfo) => {
  const cpu = stats.cpu_stats?.cpu_usage?.total_usage ?? 0;
  const pre = stats.precpu_stats?.cpu_usage?.total_usage ?? 0;
  const sys = stats.cpu_stats?.system_cpu_usage ?? 1;
  const preSys = stats.precpu_stats?.system_cpu_usage ?? 1;
  const cpuPercent = sys > 0 ? ((cpu - pre) / (sys - preSys)) * 100 : 0;
}).catch(() => null);
```

## Key Insight

**Always use `.then()` when writing new dockerode stream code.** It is the CI-safe pattern regardless of what your local types say. `await` may work locally but will fail CI.

If CI fails with TS2345 on any dockerode method, switch from `await` to `.then()` — that is always the fix.

## History

This pattern caused **two consecutive CI failures** (commits `7022d6d` and `d2a3d45`) before being diagnosed. The first failure was patched with module-level stream functions, which was correct but not the real cause. The actual cause was `await container.logs()` in `startLogStream()` — the `.then()` fix resolved it. The module-level refactor was still correct architecture but unrelated to the TS error.
