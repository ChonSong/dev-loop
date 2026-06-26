---
name: university-essay
description: "Write research-backed university essays with strict formatting constraints (Chicago referencing, no contractions/semi-colons/dot points, paragraph word limits, AI-humanizer audit). Covers: question analysis, source triage from PDFs/markdown, thesis construction, draft writing, formatting QA, AI-tell audit."
version: 1.0.0
author: Hermes Agent
platforms: [linux, macos]
metadata:
  hermes:
    tags: [university, essay, writing, chicago, academic, research, AI-humanizer]
    related_skills: [teac-assignment-writing, google-workspace, humanizer]
---

# University Essay Writing

Write research-backed university essays from source materials (PDFs, markdown, lecture notes) with tight formatting and style constraints. Applies to any discipline; adaptable to any citation style.

## Workflow

### Phase 1: Source Triage

1. **Map the folder** in Drive — list all subfolders and files. Usually the course folder (e.g. `cult1001`) has weekly subfolders (`Week_01/` through `Week_12/`) with PDFs + markdown readings.
2. **Identify the primary textbook** — often a single large PDF (10–20 MB). Download it first.
3. **Download in parallel** using `delegate_task` with `terminal` toolset — one subagent per PDF. Use `fitz` (PyMuPDF) for text extraction, not `pdfminer`.
4. **Extract targeted content** — don't dump entire PDFs. For essay research, extract only the chapters/sections relevant to the question. Write extracted text to `research/<source>_relevant.txt`.
5. **Read module markdown files** — these often contain lecture content and essay guidance. Summarize each into `research/<module>_summary.md`.

### Phase 2: Question Analysis

Break the question down before writing:
- What is the claim being made?
- What would support it? What would contradict it?
- What period/region/topic must be covered?
- What citation style is required? (Chicago, APA, Harvard — confirm before writing)
- Are there hard constraints? (word limit, no X, must use Y sources)

### Phase 3: Thesis Construction

Good thesis for an essay (not a report):
- Takes a position, not a description
- Is specific enough to argue across the whole essay
- Has intrinsic tension (two plausible views, choose one)

Thesis formula: "[Subject] was [claim] because [evidence]."

### Phase 4: Draft Writing

**Structure (chronological for history/cultural essays):**
- Intro (2–3 paragraphs): framing → thesis → roadmap
- Body (4–8 paragraphs): each paragraph has a topic sentence and develops one idea with specific evidence
- Conclusion: restate thesis with added nuance, don't just repeat

**Paragraph rules:**
- No paragraph exceeds ~100 words (split if necessary)
- No single-sentence paragraphs
- No paragraph opens with a quotation
- No semi-colons
- **No em-dashes** — use commas instead. Example: "Japan was a borrower, an energetic borrower" not "Japan was a borrower — an energetic borrower"
- No contractions
- No dot points or bullet lists
- Avoid vague temporal markers ("In ancient times" → use "In the sixth century CE")
- **Use simple, direct sentences** — avoid subordinate clauses and nested modifiers. Short sentences (10–15 words) are often better than long ones. If a sentence has more than two commas, split it. The user will explicitly ask for simpler sentences if the draft is too dense — don't wait to be asked.
- Avoid opening sentences with "The [noun]..." when a named subject reads more naturally

**Quote rules:**
- No block quotes (anything over ~20 words)
- No quote in a topic sentence
- Prefer paraphrasing over quoting

**AI vocabulary to avoid:** distinctive, pivotal, exceptional, crucial, monumental, groundbreaking, testament, underscores, showcases, serves as, stands as

### Phase 5: Formatting QA

Run these checks on every draft:

```python
import re

with open('/workspace/essay.md') as f:
    text = f.read()

body = text.split('## References')[0] if '## References' in text else text

checks = {
    "Word count": len(body.split()),
    "Semi-colons": ';' in body,
    "Contractions": any(re.search(r"\b(don't|doesn't|can't|won't|it's|that's)\b", body)),
    "Dot points": '§' in text or '•' in text,
    "AI vocabulary": any(w in body.lower() for w in [
        'serves as','stands as','underscoring','showcasing',
        'vital role','pivotal','distinctive','exceptional'
    ]),
    "Long quotes (>20 words)": any(len(q.split()) > 20 for q in re.findall(r'"([^"]+)"', text)),
}

for check, result in checks.items():
    status = "FAIL" if result else "OK"
    print(f"  [{status}] {check}: {result}")
```

**Always also run:** `python /home/hermeswebui/.hermes/skills/productivity/university-essay/scripts/essay_qa.py /workspace/essay.md`

This catches paragraph length violations (warn at >100w, split any >110w) that the inline checks above miss.

### Phase 6: AI-Humanizer Audit

Run the `humanizer` skill on the draft. Key patterns to fix:

1. **Meta-intro phrases** — avoid "This essay argues that...", "This paper examines..."
2. **Sweeping generalisations** — "The mechanism was the same everywhere" is too tidy
3. **Formulaic topic sentences** — "This pattern...", "This was..." reads as AI-generated
4. **Aphoristic closers** — neat moral conclusions like "X was Y. The results were Z."
5. **"Murphey observes/maintains/writes"** — use "Murphey notes" or "Murphey describes" or paraphrase without attribution tic
6. **Over-explaining** — let claims emerge from evidence, don't state them explicitly
7. **Tidy parallelism** — break up matching sentence structures

**Process:** Read the draft aloud (or feed to `humanizer` skill). Fix what sounds robotic. Verify formatting checks still pass after edits.

## Source Verification Pitfalls

### When user wants scholarly sources only — use Crossref API, not course materials
When the user says "use scholarly sources" or "don't use course materials for sources", immediately:
1. Use Crossref API to find real academic sources with DOIs
2. Remove all WSU course materials (Western Sydney University references) from both in-text citations AND the References section
3. Only keep real scholarly books/journal articles
4. The user will explicitly confirm which version they want — treat course material removal as the default for "scholarly sources" requests

Crossref API research pattern:
```python
import urllib.request, json
url = f"https://api.crossref.org/works?query={q.replace(' ','+')}&filter=type:book,type:journal-article&rows=5&mailto=hermes@example.com"
req = urllib.request.Request(url, headers={"User-Agent": "hermes-research/1.0"})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())
    for item in data.get('message', {}).get('items', [])[:5]:
        authors = [f"{a.get('family','')}" for a in item.get('author', [])]
        year = item.get('published-print',{}).get('date-parts',[['']])[0][0] or item.get('published-online',{}).get('date-parts',[['']])[0][0]
        title = item.get('title', [''])[0]
        doi = item.get('DOI', '')
        venue = item.get('container-title', [''])[0] if item.get('container-title') else (item.get('publisher','') or 'book')
        print(f"{', '.join(authors)} ({year}). \"{title}\". {venue}. DOI: {doi}")
```

### Quoted text must be exact — verify page numbers, chapters, and wording
When attributing a specific claim or quote to a textbook (e.g., Murphey), **always verify the actual chapter and page**, not just the topic area. The same passage may appear in multiple chapters (e.g., a quote about Tokugawa national consciousness from p. 255–267 is in Chapter 12, not Chapter 9). Always note which chapter each specific paraphrase or quote comes from.

**Workflow:** Search the extracted PDF text for the exact phrase. Check it appears in the claimed chapter before attributing.

### Module PDFs are teaching materials, not primary scholarship
Lecture slides, module PDFs, and course discourse analyses are acceptable undergraduate sources but are not peer-reviewed. Don't over-represent them as independent scholarly evidence. Use them to supplement the textbook, not replace it. If the assignment requires "scholarly sources", replace course materials with the primary source anthologies they cite (e.g. Kublin, Ebrey).

### Use course materials as evidence — cite them in the references
The user sometimes wants to keep course materials (WSU module readings, discourse analyses, human experience files) as evidence in the essay body and in the bibliography, even though they are teaching materials. When this preference is expressed:
- Keep course materials in the References section
- Note the specific human sources (e.g., "Tale of Genji", "wabi-sabi aesthetics", "Hokusai", "kabuki theatre") in brackets after each reference
- Do NOT remove them just because they are not peer-reviewed — the user wants their course materials used
- The key principle: course materials can be cited if the user explicitly wants them included. The skill should not unilaterally remove them.

### Paraphrase must preserve nuance
If Murphey writes "without **in any way** diluting...", dropping "in any way" changes the emphasis. Search the source for the exact phrase and preserve qualifier words, even in paraphrase. If a single word was dropped and it matters, re-extract and fix before uploading.

### Full question in header, not an abbreviated topic line
When the user confirms which question they are answering, write the **full question text** into the document header metadata (below Student ID). Do not abbreviate it to a short topic line like "Japan's cultural borrowing and uniqueness." This ensures the writer and reviewer can always see exactly what was asked. Update it immediately on question confirmation.

### When the essay agrees AND disagrees — state both clearly in the thesis
If the question asks "do you agree or disagree", and the correct answer is "both, at different levels", the thesis must say so directly — not just "Japan was typical in its borrowing mechanism." The thesis should reflect the actual position being taken. E.g., "This essay agrees that Japan is both unique and typical — the mechanism was typical, but the outcomes were distinctive." Ambiguity in the thesis creates ambiguity throughout the essay.

## Common Citation Styles

### Chicago (History/Arts)
```text
Author, Title (Place: Publisher, Year), page.
Author, "Chapter Title," in Book Title, ed. Editor (Place: Publisher, Year), page.
```

### APA 7th (Education/Sciences)
```text
Author, A. A. (Year). Title. Journal, Vol(Issue), pages. https://doi.org/
Book: Author, A. A. (Year). Title (ed.). Publisher.
```

### Harvard
```text
Author (Year) Title. Place: Publisher.
Author (Year) 'Chapter title', in Editor (ed.) Book Title. Place: Publisher, pages.
```

## Source Research Patterns

> **New support file:** `references/cult1001_murphey_passages.md` — verified Murphey quotes, page numbers, and Chicago formatting for CULT1001. Replicate the pattern for other courses: extract → verify exact wording → note chapter + page → update reference file.

### Word count targets
- Default: 1,200 words (body only, excluding references)
- If user specifies "1100" or "around 1100", target 1,050–1,100
- Never overshoot by more than 50 words if user has given a specific target
- If you are over by more than 50 words and trimming is hard, consolidate paragraphs rather than cutting whole sections

### In-text citations — (Author Year) format preferred
The user prefers **(Author Year) or (Author, Year)** inline parenthetical citations over superscript numerals. Default to this format.

When (Author Year) style is requested:
- Place citations immediately after the relevant claim: `Japan borrowed as Asia did (Murphey, 2019).`
- If citing a specific chapter: `(Murphey, 2019, Ch. 9)`
- Multiple citations for one claim: `(Murphey, 2019; Feng, 2019)`
- List all sources ONCE in a single References section at the end
- Do NOT use a separate Notes/footnotes section — one clean References list is sufficient

Only use superscript footnote-style numbers when the user explicitly requests them.

### Essay title
When naming the essay file, make the title descriptive and informative — not just "essay.docx". Something like "Japan_Borrowed_as_Asia_Did_CULT1001.docx" is better. If the user suggests a title, use theirs. The title should reflect the argument, not just the topic.

### When the user supplies draft text — reword minimally, fix only what is broken
When the user says "use this wording as much as possible", "reword as little as possible", or provides raw draft prose to incorporate:
1. Fix only clear grammatical errors, incomplete sentences, and nonsense phrases
2. Do NOT restructure paragraphs or rewrite sentences for style — preserve the user's voice
3. Remove all em-dashes (replace with commas or colons)
4. Fix citation format to (Author Year) or remove broken citation syntax
5. Fix "Lend, alter, obtain retentively" → "Borrow, transform, retain"
6. Fix capitalization errors ("china" → "China", "Geisha learn" → "Geisha learns")
7. Cut only truly nonsensical sentences (e.g., "it was a premeditation to Eat the meat, spit out the bones")
8. Preserve the user's sentence structure and rhythm — do not smooth it out

Do NOT apply the AI-humanizer audit to text the user has explicitly approved. Only audit text you generated yourself.

### Extract from PDF (PyMuPDF)
```python
import fitz
doc = fitz.open('/path/to/source.pdf')
for i, page in enumerate(doc):
    text = page.get_text()
    if relevant_keywords(text):
        with open('/workspace/research/source_pX.txt', 'a') as f:
            f.write(f"--- Page {i+1} ---\n{text}\n")
```

### Download from Google Drive (parallel)
Use `delegate_task` with `terminal` toolset. Each subagent:
1. Runs `$GAPI drive download FILE_ID --output /workspace/sources/filename.pdf`
2. Extracts relevant pages with `fitz`
3. Writes to `research/`

### Parse markdown sources
```python
import os
for f in os.listdir('/workspace/cult1001/sources'):
    if f.endswith('.md'):
        with open(f'/workspace/cult1001/sources/{f}') as fh:
            content = fh.read()
        # Summarize key facts for essay evidence
```

## Essays vs Reports

| | Essay | Report |
|--|-------|--------|
| Voice | First person allowed | Third person, neutral |
| Structure | Argument → evidence → conclusion | Findings → analysis → recommendations |
| Citations | In-text (Chicago/APA) | Numbered footnotes or reference list |
| Thesis | Position on a question | Summary of research |

Use essay format unless the assignment brief says "report".

## Triggers

- User says "write an essay", "draft essay", "university essay", "coursework"
- Assignment brief with word limit, citation style, and no structure provided
- User provides course materials (ZIP, PDF, Drive folder) and asks for "the essay"