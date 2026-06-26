# yt-dlp Usage for YouTube Transcripts

Alternative to youtube-transcript-api when:
- The API fails (age-restricted, member-only, region-locked videos)
- You need video metadata (title, description, upload date) before reading the transcript
- Auto-generated captions are needed (not just manual captions)
- The video has no transcript API available

## Install

```bash
uv pip install yt-dlp
# or: pip install yt-dlp
```

## Workflow

### 1. Fetch metadata first

```bash
yt-dlp --skip-download --print title --print description --print upload_date "URL"
```

This gives you context about the video before you invest time in reading the full transcript.

### 2. Fetch subtitles

```bash
# Auto-generated captions (best coverage)
yt-dlp --skip-download --write-auto-sub --sub-lang en --sub-format vtt -o '%(title)s' "URL"

# Manual captions (if auto fails or you want higher quality)
yt-dlp --skip-download --write-sub --sub-lang en --sub-format vtt -o '%(title)s' "URL"
```

### 3. Find the subtitle file

The filename may contain unicode characters (e.g., vertical bar `｜`, colons):

```bash
ls *.vtt
```

### 4. Read and summarize

Use `read_file` to load the VTT content, then summarize from the text.

## Pitfalls

- **Unicode filenames**: The `-o '%(title)s'` template produces filenames with special characters. Always use `ls *.vtt` to find the actual file.
- **VTT timing markup**: The VTT format includes `<timestamp><c> word</c>` markup. For clean reading, strip timing tags or use `--sub-format ttml` for XML-based output.
- **JS runtime warning**: `"No supported JavaScript runtime could be found"` — this is usually non-fatal for subtitle downloads since captions come from the API. If extraction fails, install deno.
- **Large transcripts**: Videos over ~30 minutes produce large VTT files. Use `read_file` with `offset` and `limit` for pagination, or process in chunks.
- **yout.be short URLs**: yt-dlp handles short URLs, shorts, embeds, and live links the same way — just pass the URL directly.
