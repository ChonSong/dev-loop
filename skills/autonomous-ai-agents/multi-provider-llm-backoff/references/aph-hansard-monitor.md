# APH Hansard Monitor — Reference Notes

## APH Website Behavior

**Azure WAF blocking:** Direct curl from container gets HTTP 200 but empty body (Azure JS challenge). The Watch_Read_Listen page loads in browser but returns empty to simple scrapers.

**Workaround:** Spoof browser user-agent + accept headers. Works from container without SSH:

```python
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}
```

**502 errors:** APH site returns 502/503 intermittently. Implement exponential backoff (5s → 10s → 20s).

## Hansard XML Structure (APH API)

**Endpoint:** `https://www.aph.gov.au/api/hansard/link/?id=chamber/hansardr/{ID}/toc&linktype=xml&fulltranscript=True`

- HoR: `chamber/hansardr/{ID}` → XML with `<date>`, `<debateinfo>`, `<subdebateinfo>`, `<question>`, `<answer>`
- Senate: `chamber/hansards/{ID}` → same structure

**Key XML elements:**
- `<question>` — question block with `<talk.start>` (asker) and `<talk.text>` (content)
- `<answer>` — answer block, same structure, follows corresponding `<question>` in document order
- `<name role="metadata">` inside `<talker>` — speaker name in format "Surname, Given MP"
- `<title>` — debate section titles (within `<debateinfo>`, `<subdebateinfo>`)
- CSS classes: `HPS-SubDebate` (section header), `HPS-Normal` (normal speech), `HPS-Small` (indented speech like questions), `HPS-SODJobDate` (date header)

**Parsing approach:** Regex more reliable than ElementTree for this XML — the namespace-heavy XML confuses ET's strict parsing. Use:
```python
question_blocks = re.findall(r'<question>(.*?)</question>', xml, re.DOTALL)
answer_blocks = re.findall(r'<answer>(.*?)</answer>', xml, re.DOTALL)
```

## Watch_Read_Listen Page ID Extraction

**URL:** `https://www.aph.gov.au/News_and_Events/Watch_Read_Listen`

IDs appear in static HTML (not JS-rendered):
- HoR: `chamber/hansardr/(\d+)` 
- Senate: `chamber/hansards/(\d+)`

Date context is in surrounding HTML (search 400 chars before ID link).

## Discord Message Format

- Limit: 2000 chars per message (hard limit, 400 error for exceed)
- Markdown: `**bold**`, `*italic*`, `__underline__`, emoji ✅🔴⚖️🏛️
- No `:emoji:` shortcode syntax (use Unicode or `<:name:id>` for custom)
- User-Agent header required or Discord rejects

## State Persistence

Track processed IDs in `aph-hansard-state.json` to avoid duplicate posts. Store last 50 IDs.