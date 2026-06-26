# Data-Driven Human Writing Profile Analysis

## Method

1. Collect real human-written text from public APIs (HN, Reddit, Medium RSS)
2. Extract sentence-level and word-level statistics
3. Build a weighted profile of natural human writing patterns
4. Generate transformations that match the profile

## Sources Used

| Source | Access | Samples | Quality |
|--------|--------|---------|---------|
| HN Algolia API | `hn.algolia.com/api/v1` (free, no key) | 136 comments | High — personal, opinionated |
| HN Firebase API | `hacker-news.firebaseio.com` (free) | 26 story titles | Medium — short |
| Reddit JSON | `reddit.com/r/X/hot.json` | ~0 (403 blocked) | — |

Total: **162 samples**, ~9,590 words, ~454 sentences.

## Statistical Findings

### Sentence Length Distribution
- **Mean**: 21.5 words
- **Median**: 16 words
- **Range**: 1–148 words
- **Variance**: 318.5

**Signal**: Low variance (<50) means sentences are too uniform → AI marker.
Human writing naturally swings between fragments and long clauses.

### Sentence Starters (top 15 by frequency)
```
i        × 37
the      × 33
and      × 13
we       × 13
but      × 10
so       × 9
if       × 9
our      × 7
it's     × 7
i'm      × 7
you      × 7
this     × 6
they     × 6
why      × 6
it       × 5
```

**Signal**: Humans start sentences with pronouns, articles, conjunctions. Zero occurrences of "furthermore", "moreover", "additionally", "in conclusion" as sentence starters. This is the highest-signal feature for detection.

### Transition Word Usage
| Word | Share |
|------|-------|
| and | 61% |
| but | 16% |
| so | 8% |
| because | 6% |
| also | 4% |
| then | 2% |
| thus | 0.5% |

**Signal**: Humans use simple coordinating conjunctions ("and", "but", "so"). Adversative transitions ("however", "nevertheless", "nonetheless") were absent. The AI preference for "however" is a strong tell.

### Filler Word Frequency
```
like    × 25  (most common)
just    × 19
really  × 16
quite   × 7
pretty  × 6
actually × 9
basically × 2
```

**Signal**: Fillers are natural in human writing. Their complete absence is suspicious.

## Practical Rules Derived

1. **Replace AI sentence starters** with human alternatives. Weight by real frequencies.
2. **Vary sentence length** — break long (>30 word) sentences ~35% of the time. Don't break if it makes the text uniform.
3. **Add filler words** at ~20% probability per sentence. Place mid-sentence after verbs.
4. **Use contractions** universally. "Do not" → "don't", "it is" → "it's", etc.
5. **Replace "furthermore"** → "And"/"Plus"/"Also" (no "furthermore" = more human)
6. **Replace "in conclusion"** → "Bottom line"/"So"/"Basically"

## Implementation

The profile is stored as a JSON dict with keys:
- `contractions`: mapping of formal → contracted forms
- `sentence_starts`: weighted dict (word → count) for sampling human starters
- `ai_starters`: phrases to detect and replace
- `transitions`: weighted dict of natural transition words
- `fillers`: list of filler words to insert occasionally
- `sent_len_mean` / `sent_len_variance`: target distribution

The `--train` flag in `humanizer.py` learns all these from a JSONL file and writes a `.json` profile.
