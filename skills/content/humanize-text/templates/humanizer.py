#!/usr/bin/env python3
"""
humanizer.py — data-driven humanizer, built from 278K human/AI text pairs.
Usage:
  python3 humanizer.py < input.txt  > output.txt
  python3 humanizer.py -a < input.txt  # more aggressive
"""

import re, sys, random, argparse

# ── DATA-DRIVEN WORD SWAPS ────────────────────────────────────
# Top words AI overuses (from 10K-row analysis of dmitva/human_ai_generated_text)
# Format: word -> (replacement, probability)
AI_OVERUSED = {
    "additionally":    ("also", 0.95),
    "furthermore":     ("also", 0.95),
    "moreover":        ("plus", 0.90),
    "nevertheless":    ("still", 0.80),
    "nonetheless":     ("still", 0.75),
    "heretofore":      ("so far", 1.0),
    "hitherto":        ("so far", 1.0),
    "thereafter":      ("then", 0.85),
    "thereby":         ("and", 0.70),
    "consequently":    ("so", 0.80),
    "subsequently":    ("then", 0.75),
    "accordingly":     ("so", 0.80),
    "notably":         ("especially", 0.80),
    "similarly":       ("same with", 0.75),
    "conversely":      ("but", 0.85),
    "alternatively":   ("or", 0.75),
    "thusly":          ("so", 1.0),
    "namely":          ("like", 0.50),

    "provide":         ("give", 0.60),
    "provides":        ("gives", 0.60),
    "providing":       ("giving", 0.60),
    "utilize":         ("use", 0.90),
    "utilizes":        ("uses", 0.90),
    "utilizing":       ("using", 0.90),
    "implement":       ("set up", 0.40),
    "implementation":  ("setup", 0.35),
    "facilitate":      ("help", 0.70),
    "facilitates":     ("helps", 0.70),
    "demonstrate":     ("show", 0.60),
    "demonstrates":    ("shows", 0.60),
    "elucidate":       ("explain", 0.85),
    "endeavor":        ("try", 0.80),
    "commence":        ("start", 0.90),
    "optimize":        ("improve", 0.50),
    "incentivize":     ("encourage", 0.60),

    "essential":       ("important", 0.40),
    "paramount":       ("key", 0.85),
    "imperative":      ("necessary", 0.70),
    "significant":     ("serious", 0.35),
    "comprehensive":   ("full", 0.30),
    "pivotal":         ("key", 0.80),
    "integral":        ("key", 0.70),
    "multifaceted":    ("complex", 0.60),
    "profound":        ("deep", 0.45),
    "transformative":  ("powerful", 0.30),
    "unprecedented":   ("new", 0.60),
    "bespoke":         ("custom", 0.70),
    "seamless":        ("smooth", 0.50),
    "holistic":        ("overall", 0.55),
    "robust":          ("strong", 0.35),
    "granular":        ("detailed", 0.50),
    "actionable":      ("useful", 0.50),
    "deliverable":     ("result", 0.50),
    "substantial":     ("big", 0.50),

    "fosters":         ("builds", 0.50),
    "fostering":       ("building", 0.50),
    "empower":         ("help", 0.60),
    "empowers":        ("helps", 0.60),
    "leverage":        ("use", 0.65),
    "leveraging":      ("using", 0.65),
    "strive":          ("try", 0.70),
    "strives":         ("tries", 0.70),
    "navigate":        ("handle", 0.50),

    "paradigm":        ("model", 0.30),  # context-checked: skip if "shift" follows
    "perspectives":    ("viewpoints", 0.60),
    "nuances":         ("details", 0.50),
    "intricacies":     ("details", 0.55),
    "facets":          ("sides", 0.50),
    "ramifications":   ("effects", 0.60),
    "implications":    ("effects", 0.30),

    "plethora":        ("lot", 0.90),
    "multitude":       ("lot", 0.90),
    "myriad":          ("countless", 0.70),

    "undoubtedly":     ("no doubt", 0.50),
    "arguably":        ("maybe", 0.40),
    "inevitably":      ("sooner or later", 0.40),
    "increasingly":    ("more and more", 0.40),
    "ultimately":      ("in the end", 0.35),
}

AI_SENTENCE_STARTERS = {
    "ultimately": 0.90, "additionally": 0.95, "furthermore": 0.95,
    "moreover": 0.90, "nevertheless": 0.85, "nonetheless": 0.85,
    "consequently": 0.85, "similarly": 0.80, "conversely": 0.85,
    "alternatively": 0.80, "notably": 0.80, "accordingly": 0.85,
    "subsequently": 0.80, "hence": 0.80, "thus": 0.60,
    "therefore": 0.50, "overall": 0.50, "despite": 0.40,
}

# Human-favored sentence starters (from data: humans use "because" 109x more,
# "so" 12.5x more, "and" 13x more as sentence starters)
HUMAN_STARTERS = ["so", "but", "and", "also", "because", "actually",
                  "well", "then", "now", "sometimes", "honestly",
                  "sure", "you"]
_STARTER_WORDS = set(HUMAN_STARTERS)

PHRASE_REPLACEMENTS = [
    (r"(?i)\bin\s+today['’]s\s+(digital\s+)?(landscape|age|world|era)\b",
     "right now"),
    (r"(?i)\bin\s+this\s+(ever-)?evolving\s+(landscape|world|environment)\b",
     "today"),
    (r"(?i)\ba\s+tapestry\s+of\b", "a mix of"),
    (r"(?i)\ba\s+(wealth|treasure)\s+trove\s+of\b", "a lot of"),
    (r"(?i)\bcutting-edge\b", "modern"),
    (r"(?i)\bstate-of-the-art\b", "modern"),
    (r"(?i)\bgame-changer\b", "big step forward"),
    (r"(?i)\bdeep\s+dive\b", "close look"),
    (r"(?i)\bcircle\s+back\b", "revisit"),
    (r"(?i)\btouch\s+base\b", "check in"),
    (r"(?i)\bbandwidth\b", "time"),
    (r"(?i)\bnot\s+only\s+.*?\s+but\s+also\b", "while"),
    (r"(?i)\bis\s+(crucial|essential|imperative|vital)\s+that\b",
     "is important that"),
    (r"(?i)\bis\s+(crucial|essential|imperative|vital)\s+to\b",
     "is important to"),
    (r"(?i)\bit\s+(should\s+)?be\s+noted\b", ""),
    (r"(?i)\bit[''']s\s+important\s+to\s+(note|remember|understand)\b", "keep in mind"),
    (r"(?i)\bin\s+other\s+words\b", "basically"),
    (r"(?i)\bwhen\s+it\s+comes\s+to\b", "for"),
    (r"(?i)\bplay\s+(a|an)\s+(pivotal|integral|crucial|vital|key|significant)\s+role\b",
     "matters"),
    (r"(?i)\bit\s+is\s+worth\s+noting\b", ""),
    (r"(?i)\bgoes\s+without\s+saying\b", "obviously"),
    (r"(?i)\bsuffice\s+(it\s+)?to\s+say\b,?\s*", ""),
    (r"(?i)\bin\s+a\s+similar\s+vein\b", "likewise"),
    (r"(?i)\bby\s+the\s+same\s+token\b", "also"),
    (r"(?i)\ball\s+things\s+considered\b", "overall"),
    (r"(?i)\bat\s+the\s+end\s+of\s+the\s+day\b", "in the end"),
    (r"(?i)\bon\s+a\s+(grander|broader|larger)\s+scale\b", "more broadly"),
    (r"(?i)\bdrill\s+down\s+into\b", "look into"),
    (r"(?i)\bon\s+the\s+fence\b", "unsure"),
    (r"(?i)\bhit\s+the\s+ground\s+running\b", "get started fast"),
    (r"(?i)\bthink\s+outside\s+the\s+box\b", "think differently"),
    (r"(?i)\btrailblazing\b", "pioneering"),
    (r"(?i)\bgroundbreaking\b", "important"),
]

# Words that can't follow "You" naturally (prevent "You in/at/the/it's")
_HUMAN_START_BLOCK = {
    "in", "at", "on", "for", "with", "by", "from", "to",
    "it's", "its", "it", "is", "are", "was", "were",
    "the", "this", "that", "these", "those",
}


def _fix_a_an(text: str) -> str:
    """Fix article mismatches caused by word swaps: 'a' before vowel, 'an' before consonant."""
    text = re.sub(r'\ba\s+([aeiou])', r'an \1', text)
    text = re.sub(r'\ban\s+([bcdgfhjklmnpqrstvwxyz])', r'a \1', text)
    return text


def replace_phrases(text: str) -> str:
    for pat, repl in PHRASE_REPLACEMENTS:
        if isinstance(repl, tuple):
            text = re.sub(pat, repl[0], text)
        else:
            text = re.sub(pat, repl, text)
    return text


def replace_overused_words(text: str) -> str:
    words = text.split()
    result = []
    for i, w in enumerate(words):
        stripped = w.lower().strip("(),.;:!?\"'")
        if stripped in AI_OVERUSED:
            repl, prob = AI_OVERUSED[stripped]
            if random.random() < prob:
                # Keep "paradigm shift" intact
                if stripped == "paradigm" and i + 1 < len(words):
                    nxt = words[i + 1].lower().strip("(),.;:!?\"'")
                    if nxt == "shift":
                        result.append(w)
                        continue
                if w[0].isupper():
                    repl = repl[0].upper() + repl[1:] if len(repl) > 1 else repl.upper()
                trail = ''
                while w and not w[-1].isalpha() and w[-1] != "'":
                    trail = w[-1] + trail
                    w = w[:-1]
                result.append(repl + trail)
                continue
        result.append(w)
    return " ".join(result)


def fix_ai_sentence_starts(text: str) -> str:
    """Replace AI-favored sentence starters with human equivalents."""
    def _replace_start(m):
        word = m.group(1).lower()
        if word in AI_SENTENCE_STARTERS and random.random() < AI_SENTENCE_STARTERS[word]:
            repl = random.choice(HUMAN_STARTERS)
            if m.group(1)[0].isupper():
                repl = repl[0].upper() + repl[1:]
            comma = m.group(2) or ""
            return repl + comma
        return m.group(0)
    text = re.sub(r'(?i)(?:^|(?<=[.!?])\s+)(\w[\w']*)(,?\s)', _replace_start, text)
    return text


def add_human_sentence_starts(text: str) -> str:
    """
    Randomly convert some sentences to start human-style:
    - 8% lowercase start (matches human 7.7%)
    - 15% chance to prepend 'So', 'But', 'And', etc.
    Skips sentences already starting with transition or human words
    to prevent "And however" or "So additionally" doubling.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) < 2:
        return text
    for idx in range(1, len(sentences)):
        s = sentences[idx]
        if not s or len(s) < 10:
            continue
        first_word = re.match(r"(\w[\w']*)", s)
        if not first_word:
            continue
        fw = first_word.group(1)
        fw_lower = fw.lower()
        # Skip if already starts with a human starter or AI transition
        if fw_lower in _STARTER_WORDS:
            continue
        if fw_lower in ("additionally", "furthermore", "moreover", "nevertheless",
                         "nonetheless", "consequently", "subsequently",
                         "alternatively", "conversely", "in",
                         "finally", "lastly", "however", "but", "so"):
            continue
        # Lowercase start (8% chance)
        if random.random() < 0.08 and s[0].isupper():
            sentences[idx] = s[0].lower() + s[1:]
        # Prepend human starter (15% chance)
        if random.random() < 0.15:
            starter = random.choice(HUMAN_STARTERS)
            if starter in ("well", "so", "now", "honestly", "also", "then"):
                sentences[idx] = starter[0].upper() + starter[1:] + ", " + s[0].lower() + s[1:]
            else:
                sentences[idx] = starter[0].upper() + starter[1:] + " " + s[0].lower() + s[1:]
    return " ".join(sentences)


def boost_contractions(text: str) -> str:
    """Match human contraction rate (~85/10K words vs AI's ~14)."""
    pairs = [
        (r"(?i)\bwill not\b", "won't"),
        (r"(?i)\bcannot\b", "can't"),
        (r"(?i)\bis not\b", "isn't"),
        (r"(?i)\bare not\b", "aren't"),
        (r"(?i)\bwas not\b", "wasn't"),
        (r"(?i)\bwere not\b", "weren't"),
        (r"(?i)\bhas not\b", "hasn't"),
        (r"(?i)\bhave not\b", "haven't"),
        (r"(?i)\bhad not\b", "hadn't"),
        (r"(?i)\bdoes not\b", "doesn't"),
        (r"(?i)\bdo not\b", "don't"),
        (r"(?i)\bdid not\b", "didn't"),
        (r"(?i)\bwould not\b", "wouldn't"),
        (r"(?i)\bcould not\b", "couldn't"),
        (r"(?i)\bshould not\b", "shouldn't"),
        (r"(?i)\bmight not\b", "mightn't"),
        (r"(?i)\bthey are\b", "they're"),
        (r"(?i)\bwe are\b", "we're"),
        (r"(?i)\byou are\b", "you're"),
        (r"(?i)\bi am\b", "I'm"),
        (r"(?i)\bhe is\b", "he's"),
        (r"(?i)\bshe is\b", "she's"),
        (r"(?i)\bit is\b", "it's"),
        (r"(?i)\bthere is\b", "there's"),
        (r"(?i)\bthat is\b", "that's"),
        (r"(?i)\bwhat is\b", "what's"),
        (r"(?i)\bwho is\b", "who's"),
        (r"(?i)\bwould have\b", "would've"),
        (r"(?i)\bcould have\b", "could've"),
        (r"(?i)\bshould have\b", "should've"),
        (r"(?i)\bmight have\b", "might've"),
    ]
    for pat, repl in pairs:
        if random.random() < 0.70:
            text = re.sub(pat, repl, text, count=2)
    return text


def fix_ai_punctuation(text: str) -> str:
    """Reduce AI punctuation tells: em-dashes, Oxford commas, hyphens."""
    text = re.sub(r'\s*—\s*', '. ', text)
    text = re.sub(r'\s*--\s*', '. ', text)
    if random.random() < 0.5:
        text = re.sub(r',\s+and\b', ' and', text)
        text = re.sub(r',\s+or\b', ' or', text)
    if random.random() < 0.3:
        text = re.sub(r',\s+but\b', ' but', text)
    text = re.sub(r'(\w+)-(\w+)',
                  lambda m: m.group(1) + ' ' + m.group(2)
                  if random.random() < 0.3 else m.group(0), text)
    return text


def add_burstiness(text: str) -> str:
    """
    Create sentence-length variance matching human CV (~0.85 vs AI ~0.35).
    Splits long sentences at introductory phrases or conjunctions,
    creating short fragments alongside longer ones.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    i = 0
    while i < len(sentences):
        s = sentences[i].strip()
        if not s:
            i += 1
            continue
        wc = len(s.split())
        if wc > 28 and random.random() < 0.5:
            # Try introductory phrase split: "In/As/While/By/For ... ,"
            m = re.match(
                r'(In|As|While|Although|When|If|Through|Despite|By|For|With|Since)\s+\w[^,]{4,35}?,\s+',
                s, re.IGNORECASE
            )
            if m:
                p1 = m.group(0).strip(', ')
                rest = s[m.end():]
                w1 = len(p1.split())
                if w1 >= 2 and w1 <= 10 and len(rest.split()) > 6:
                    result.append(p1 + ".")
                    result.append(rest[0].upper() + rest[1:])
                    i += 1
                    continue
            # Comma + conjunction split
            m2 = re.split(r'(?:,\s+(?:and|but|or|so|yet|because|while|although|since|whereas)\s+|; )',
                          s, maxsplit=1)
            if len(m2) >= 2 and len(m2[-1].split()) >= 6:
                p1, p2 = m2[0].strip(), m2[-1].strip()
                result.append(p1 + ".")
                result.append(p2[0].upper() + p2[1:])
                i += 1
                continue
            # First-comma split
            parts = s.split(', ', 1)
            if len(parts) == 2:
                p1, p2 = parts[0].strip(), parts[1].strip()
                w1 = len(p1.split())
                if w1 >= 2 and w1 <= 8 and len(p2.split()) > 10:
                    result.append(p1 + ".")
                    result.append(p2[0].upper() + p2[1:])
                    i += 1
                    continue
        result.append(s)
        i += 1
    return " ".join(result)


def add_human_voice(text: str) -> str:
    """
    Insert "you" at sentence start (humans use 6.6x more second-person).
    Only fires when the next word is verb-friendly (not prep/conj/pronoun).
    """
    if random.random() < 0.3 and len(text) > 100:
        if not re.search(r"(?i)\byou\b", text):
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for idx in range(len(sentences)):
                if random.random() < 0.15 and len(sentences[idx].split()) > 8:
                    s = sentences[idx]
                    fw = re.match(r"(\w[\w']*)", s)
                    if fw:
                        first = fw.group(1).lower()
                        if first in _HUMAN_START_BLOCK:
                            continue
                        sentences[idx] = "You " + s[0].lower() + s[1:]
                        break
            text = " ".join(sentences)
    return text


def humanize(text: str, aggressive: bool = False) -> str:
    text = replace_phrases(text)
    text = replace_overused_words(text)
    text = fix_ai_sentence_starts(text)
    text = add_human_sentence_starts(text)
    text = add_burstiness(text)
    text = boost_contractions(text)
    text = fix_ai_punctuation(text)
    text = add_human_voice(text)

    if aggressive:
        text = replace_overused_words(text)
        text = add_burstiness(text)
        text = add_human_sentence_starts(text)
        text = boost_contractions(text)
        text = fix_ai_sentence_starts(text)

    text = _fix_a_an(text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Data-driven AI text humanizer")
    p.add_argument("--aggressive", "-a", action="store_true")
    args = p.parse_args()
    txt = sys.stdin.read()
    if not txt.strip():
        print("No input", file=sys.stderr); sys.exit(1)
    print(humanize(txt, aggressive=args.aggressive))
