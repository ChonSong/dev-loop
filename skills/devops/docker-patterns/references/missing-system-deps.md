# Missing System Dependencies in Minimal Containers

A tool binary is installed (via npm, pip, or bundled by an npm package like Puppeteer) but fails at runtime in the Hermes Docker container (Debian 13 Trixie, no `apt` write access, no `sudo`).

## Diagnosis

```bash
# 1. Verify the binary exists
ls -la /path/to/binary

# 2. Find missing shared libraries
ldd /path/to/binary | grep "not found"
# Example output:
#   libglib-2.0.so.0 => not found
#   libnss3.so => not found
#   libcups.so.2 => not found
#   libdbus-1.so.3 => not found
#   libatk-1.0.0 => not found
#   libgbm.so.1 => not found
#   ... (typically 15+ libraries for Chromium-based tools)

# 3. Confirm the binary truly can't start
/path/to/binary --version
# error while loading shared libraries: libglib-2.0.so.0: cannot open shared object file
```

**Key insight:** `error while loading shared libraries` means the linker can't find the library at runtime. It does NOT mean the library isn't present somewhere — it may just not be on the standard search path. But in this minimal container, the libraries genuinely aren't installed.

## Workaround A: Local Deb Extraction (No Root)

Debian Trixie packages can be downloaded and extracted to a custom prefix, then pointed at via `LD_LIBRARY_PATH`:

```bash
# Create a local deps directory
mkdir -p ~/local-deps/lib

# Download the missing .deb packages from Debian mirrors
# (you need the full dependency chain — libglib2.0 depends on libffi8, etc.)
cd /tmp
wget http://deb.debian.org/debian/pool/main/libg/libglib2.0/libglib2.0-0_2.84.0-1_amd64.deb
# ... repeat for each missing library

# Extract to the local prefix
for deb in *.deb; do
    dpkg -x "$deb" ~/local-deps
done

# Use it
export LD_LIBRARY_PATH=$HOME/local-deps/usr/lib/x86_64-linux-gnu
/path/to/binary --version  # should now work
```

**Caveats:**
- You need to resolve the full transitive dependency tree manually (which debs each library comes from)
- Brittle across distro updates — prefer option B for anything production

## Workaround B: SSH to Host (Recommended)

The host system (Arch Linux) has all system libraries. Use the pre-configured SSH key to run the tool on the host:

```bash
ssh -i /home/hermes/.ssh/id_ed25519 sean@localhost "
  cd /tmp && \
  npm init -y && \
  npm install puppeteer && \
  node -e '
    const p = require(\"puppeteer\");
    p.launch({headless: true, args: [\"--no-sandbox\"]})
     .then(b => { console.log(\"Browser works on host\"); return b.close(); })
     .catch(e => console.error(e.message));
  '
"
```

For recurring needs, place a helper script on the host and invoke via SSH.

## Applied: Puppeteer in the Hermes Container

**Symptom:** `Failed to launch the browser process! / error while loading shared libraries: libglib-2.0.so.0`

**Actual state (June 2026):**
- `puppeteer` npm package: installed in `/workspace/open-lovable/node_modules/puppeteer/`
- Bundled Chromium binary: exists at `~/.hermes/home/.cache/puppeteer/chrome/linux-131.0.6778.204/chrome-linux64/chrome` (~250MB)
- Missing libraries: ~15 (confirmed via `ldd`)
- Container has no `sudo`, no `apt-get install` write access

Puppeteer is commonly needed for web scraping, PDF generation, screenshot capture, and visual regression testing — all tasks the agent may be asked to do.
