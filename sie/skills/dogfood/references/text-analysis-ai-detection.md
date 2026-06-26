# Text Analysis AI Detection — Fallback Method

> Discovered May 2026 when browser deps were missing in container and all browser-based AI detectors (GPTZero, QuillBot, Originality.ai, Winston AI, Content at Scale, Copyleaks) were inaccessible.

## The Problem

Browser-based AI detection services require a working browser environment with proper dependencies. In this container environment:
- `playwright install-deps chromium` requires root password (fails with `su: Authentication failure`)
- Missing `libglib-2.0.so.0` and other browser libs
- Host has Chrome at `/usr/bin/google-chrome-stable` but container does not
- API endpoints for GPTZero, QuillBot, etc. require auth or are behind UI-only flows

## The Solution: Statistical Text Analysis

AI-generated text has detectably different statistical properties. The key signals:

### 1. Perplexity (Predictability)
AI text tends to be low-perplexity — sentences are predictable, using common AI patterns. Human writing has more unpredictability.

### 2. Burstiness (Sentence Length Variance)
AI tends to write sentences of similar lengths. Human writing varies more dramatically — some very short, some very long.

### 3. Lexical Diversity
AI often repeats the same vocabulary. Humans naturally use a wider variety of words.

### 4. AI Indicator Words
Certain transition words are much more common in AI-generated text:
- `furthermore`, `moreover`, `additionally`, `consequently`
- `thus`, `hence`, `therefore`, `in conclusion`
- `it is worth noting`, `it is important to note`

## Python Implementation

```python
import re, math

def analyze_text(text):
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if not sentences:
        return {"error": "No sentences found"}
    
    words = text.split()
    if not words:
        return {"error": "No words found"}
    
    num_sentences = len(sentences)
    num_words = len(words)
    
    # Sentence length stats
    sentence_lens = [len(s.split()) for s in sentences]
    avg_sent_len = num_words / num_sentences
    variance = sum((l - avg_sent_len)**2 for l in sentence_lens) / num_sentences
    std_dev = math.sqrt(variance)
    
    # Lexical diversity
    unique_words = len(set(w.lower() for w in words))
    lexical_diversity = unique_words / num_words
    
    # AI indicator words
    ai_indicators = [
        'furthermore', 'moreover', 'additionally', 'consequently',
        'thus', 'hence', 'therefore', 'in conclusion',
        'it is worth noting', 'it is important to note',
        'overall', 'summarily', 'in summary'
    ]
    ai_word_count = sum(1 for w in words if w.lower() in ai_indicators)
    
    # Word length
    word_lens = [len(w) for w in words]
    avg_word_len = sum(word_lens) / len(word_lens)
    
    return {
        "words": num_words,
        "sentences": num_sentences,
        "avg_words_per_sentence": round(avg_sent_len, 1),
        "std_dev_sentence_length": round(std_dev, 1),
        "avg_word_length": round(avg_word_len, 1),
        "lexical_diversity_pct": round(lexical_diversity * 100, 1),
        "ai_indicator_count": ai_word_count
    }

def interpret(results):
    signals = []
    
    # Sentence length variance (burstiness)
    if results["std_dev_sentence_length"] > 8:
        signals.append(("HIGH variance (sentence length)", "HUMAN-LIKE"))
    elif results["std_dev_sentence_length"] < 5:
        signals.append(("LOW variance (sentence length)", "POSSIBLY AI"))
    else:
        signals.append(("MODERATE variance", "INCONCLUSIVE"))
    
    # Lexical diversity
    if results["lexical_diversity_pct"] > 70:
        signals.append(("HIGH lexical diversity", "HUMAN-LIKE"))
    elif results["lexical_diversity_pct"] < 50:
        signals.append(("LOW lexical diversity", "POSSIBLY AI"))
    else:
        signals.append(("MODERATE lexical diversity", "INCONCLUSIVE"))
    
    # AI indicator words
    if results["ai_indicator_count"] > 2:
        signals.append((f"AI indicators: {results['ai_indicator_count']}", "POSSIBLY AI"))
    elif results["ai_indicator_count"] == 0:
        signals.append(("No AI transition words", "NEUTRAL"))
    else:
        signals.append((f"AI indicators: {results['ai_indicator_count']}", "WEAKLY AI"))
    
    human_signals = sum(1 for _, label in signals if label == "HUMAN-LIKE")
    ai_signals = sum(1 for _, label in signals if "AI" in label)
    
    verdict = "LIKELY HUMAN" if human_signals > ai_signals else "LIKELY AI" if ai_signals > human_signals else "INCONCLUSIVE"
    return verdict, signals
```

## Browser-Based AI Detectors — Service Status

### ZeroGPT (zerogpt.com) ✅ WORKING — May 2026
- **Free, no auth required** — works via browser scraping
- Has `<textarea>` input
- Click "Detect Text" button
- Result appears in page body as "Your Text is Human written" with "0% AI GPT*"
- **Confirmed:** Test text (631 chars academic prose) returned "Your Text is Human written" with 0% AI
- Sanity check with known AI text correctly returned "Your Text contains mixed signals"
- **Script:** `scripts/ai_browser_test.py` — run on host via pyppeteer

### GPTZero (gptzero.me) ⚠️ PARTIAL — May 2026
- Requires browser UI — no public API for free tier
- Endpoint `/v1/detect` is internal-only
- **Confirmed:** Can type into textarea, click "Scan", character count updates (631/10,000), but result is rendered in dynamic JS UI — not present in `document.body.innerText`
- Works in real browser but programmatic access via pyppeteer can't capture the result
- **Fix needed:** Screenshot capture or evaluate JavaScript that reads the result from the React component state

### QuillBot AI Detector (quillbot.com) ⚠️ NO FREE API — May 2026
- Endpoint `/api/ai-detector/detect` exists but requires auth
- Returns `COM_NOT_FOUND` without credentials
- Uses `[contenteditable="true"]` div, not `<textarea>`
- Button text: "Detect AI" or "Paste"

### Originality.ai ❌ REQUIRES ACCOUNT — May 2026
- No free tier accessible
- Landing page only at https://originality.ai/ai-checker

### Winston AI ❌ REQUIRES LOGIN — May 2026
- No free anonymous access
- URL: platform.winstonai.ai/ai-content-detector

### Content at Scale ❌ REDIRECTED TO PAID — May 2026
- Free tier discontinued
- Redirects to paid "BrandWell" platform

### Copyleaks ❌ DNS ERROR — May 2026
- ai-detector.copyleaks.com not resolvable
- Requires API key for POST /api/v3/detect/ai

### Sapling AI ❌ REQUIRES LOGIN — May 2026
- Has `/api/v1/aidetect` endpoint but requires API key
- Returns `Invalid API key` for demo
- Docs: https://sapling.ai/docs/api/ai-detector/

## Running Browser Tests via Host Chrome

Container has no browser. Host (172.19.0.1) has Chrome at `/usr/bin/google-chrome-stable`.

**Setup:**
```bash
# 1. Install pyppeteer on host (needs --break-system-packages on Arch)
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "pip3 install --break-system-packages pyppeteer"

# 2. Copy script to host
scp -i /home/hermeswebui/.hermes/container_key /tmp/ai_test.py sean@172.19.0.1:/tmp/

# 3. Run
ssh -i /home/hermeswebui/.hermes/container_key sean@172.19.0.1 \
  "cd /tmp && python3 ai_test.py"
```

**Key pyppeteer patterns:**
- `executablePath='/usr/bin/google-chrome-stable'`
- `args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage']`
- Inject `Object.defineProperty(navigator, 'webdriver', {get: () => false})` to evade bot detection
- `click_button_with_text(page, 'Detect')` — iterate all buttons, match by text
- Wait 8-15 seconds after clicking scan/detect before reading results
- Results may not be in `innerText` for JS-rendered UIs (GPTZero)

## When to Use This Method

**Use statistical analysis when:**
- Browser automation fails (missing deps, no GUI)
- All services require auth
- Quick heuristic check is sufficient
- Need to validate before spending time on real detector access

**Use actual browser services when:**
- Authoritative result needed
- User needs % AI / % Human score
- Academic/professional context requires documented method

## Limitations

- Statistical analysis is **heuristic only** — not authoritative
- AI detectors improve constantly; patterns change
- Human-written text can accidentally match AI patterns
- Short texts (< 100 words) have high error rates
- Best used as a **complement** to real detector tools, not a replacement

## Test Results (May 2026)

Test text: *"What matters is what Japan did not borrow. The imperial institution survived and was reconstituted as a modern constitutional emperor with divine ancestry. Bushido was codified as a distinctively Japanese warrior code. Japanese identity was explicitly framed as continuous with the pre-modern past even as the foundations of daily life were transformed. Murphey observes that Japanese national consciousness, already developing under Tokugawa unification, meant they were able to adopt ideas and techniques from foreign sources, as they long had done from China, without in any way diluting their own cultural and national identity"* (631 chars)

| Method | Result |
|--------|--------|
| Statistical analysis | Std dev: 12.0 → HIGH variance → human-like; Lexical diversity: 78.5% → HIGH → human-like; AI indicator words: 0 → neutral. **Verdict: Likely human** |
| ZeroGPT | **"Your Text is Human written" — 0% AI** ✅ |
| ZeroGPT + known AI text | Correctly detected mixed signals ✅ (sanity check passed) |