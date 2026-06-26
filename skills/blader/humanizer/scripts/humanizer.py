#!/usr/bin/env python3
"""
humanizer.py — strip AI tells from text. Free, local, zero deps.
Usage:
  python3 humanizer.py < input.txt > output.txt
  cat essay.txt | python3 humanizer.py --aggressive

Part of the creative/humanizer skill. For editorial humanization
guidelines (29 patterns, voice calibration, etc.), see SKILL.md.
"""

import re
import sys
import random
import argparse


def _fix_not_only(m: re.Match) -> str:
    content = m.group(0)
    inner = re.sub(r'(?i)^not only\s+', '', content)
    inner = re.sub(r'(?i)\s+but also\s*', ' and ', inner)
    return inner.strip()


def _fix_a_an(text: str) -> str:
    return re.sub(r'\ba\s+([aeiou])', r'an \1', text)


# ── Pattern-based rewrites (structural, not just word swaps) ──
PHRASE_PATTERNS = [
    (r"(?i)\bin\s+today['′]s\s+digital\s+(landscape|age|world|era)\b", "these days"),
    (r"(?i)\bin\s+this\s+(ever-)?evolving\s+(landscape|world|environment|climate)\b", "right now"),
    (r"(?i)\ba\s+(plethora|multitude)\s+of\b", "a lot of"),
    (r"(?i)\bits\s+(important|crucial|essential|vital)\s+(to|that)\b", "we need to"),
    (r"(?i)\bit\s+is\s+worth\s+noting\b", "also"),
    (r"(?i)\bit['′]s\s+(important|crucial|essential|vital)\s+to\s+(note|remember|understand)\b", "keep in mind"),
    (r"(?i)\bit\s+should\s+be\s+noted\b", "worth saying"),
    (r"(?i)\bin\s+other\s+words\b", "basically"),
    (r"(?i)\bwhen\s+it\s+comes\s+to\b", "when talking about"),
    (r"(?i)\bas\s+(mentioned|discussed|stated|noted)\s+(earlier|previously|above)\b", "like I said"),
    (r"(?i)\bin\s+terms\s+of\b", "around"),
    (r"(?i)\bthe\s+fact\s+of\s+the\s+matter\b", "honestly"),
    (r"(?i)\ball\s+things\s+considered\b", "overall"),
    (r"(?i)\bat\s+the\s+end\s+of\s+the\s+day\b", "ultimately"),
    (r"(?i)\bon\s+a\s+(grander|broader|larger)\s+scale\b", "more broadly"),
    (r"(?i)\bplay\s+(a|an)\s+(pivotal|integral|crucial|vital|key)\s+role\b", "matters a lot"),
    (r"(?i)\bgoes\s+without\s+saying\b", "obviously"),
    (r"(?i)\bsuffice\s+(it\s+)?to\s+say\b,\s*", ""),
    (r"(?i)\bsuffice\s+(it\s+)?to\s+say\b", ""),
    (r"(?i)\blast\s+but\s+(not\s+least|by\s+no\s+means)\b", "finally"),
    (r"(?i)\bin\s+a\s+similar\s+vein\b", "likewise"),
    (r"(?i)\bby\s+the\s+same\s+token\b", "also"),
    (r"(?i)\bnot\s+only\s+.*?\s+but\s+also\b", _fix_not_only),
    (r"(?i)\ba\s+tapestry\s+of\b", "a mix of"),
    (r"(?i)\bnavigate\s+the\s+(complexities|nuances|intricacies)\b", "handle"),
]

# ── Word swaps — only common AI overused words ─────────────────
WORD_SWAPS = {
    "unprecedented": ["new", "unusual", "rare"],
    "empower": ["help", "let", "enable"],
    "holistic": ["overall", "big-picture"],
    "seamless": ["smooth", "easy", "natural"],
    "leverage": ["use", "tap into"],
    "utilize": ["use"],
    "facilitate": ["help", "make easier"],
    "optimize": ["improve", "tune", "refine"],
    "demonstrate": ["show", "prove"],
    "endeavor": ["try", "effort"],
    "commence": ["start", "begin"],
    "bespoke": ["custom", "tailored"],
    "granular": ["detailed", "fine-grained"],
    "meticulous": ["careful", "thorough"],
    "transparent": ["clear", "open"],
    "pragmatic": ["practical", "realistic"],
    "incentivize": ["motivate", "encourage"],
    "cutting-edge": ["modern", "latest"],
    "state-of-the-art": ["modern", "top-tier"],
    "actionable": ["useful", "practical"],
    "deliverable": ["result", "output"],
    "captivate": ["grab", "hook"],
    "immersive": ["deep", "hands-on"],
}

# ── Transition words to thin ───────────────────────────────────
FORMAL_TRANSITIONS = {
    "furthermore", "moreover", "consequently", "nonetheless",
    "nevertheless", "notwithstanding", "heretofore", "hitherto",
    "thereafter", "wherein", "thereby", "thusly",
}


def swap_words(text: str) -> str:
    for word, replacements in WORD_SWAPS.items():
        if random.random() < 0.6:
            continue
        r = random.choice(replacements)
        text = re.sub(r'\b' + re.escape(word) + r'\b', r, text,
                      count=1 + int(random.random() < 0.3), flags=re.IGNORECASE)
    return text


def thin_transitions(text: str) -> str:
    words = text.split()
    kept = []
    for w in words:
        stripped = w.strip("(),.;:!?").lower()
        if stripped in FORMAL_TRANSITIONS and random.random() < 0.6:
            continue
        kept.append(w)
    return " ".join(kept)


def vary_sentence_lengths(text: str) -> str:
    """Create sentence-length variance (burstiness)."""
    raw = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in raw if s.strip()]
    result = []
    i = 0
    while i < len(sentences):
        s = sentences[i]
        wc = len(s.split())

        if wc > 30 and random.random() < 0.4:
            parts = re.split(
                r'(?:,\s+(and|but|or|so|yet|because|while|although|since)|[:;])',
                s, maxsplit=1
            )
            if len(parts) >= 2:
                p1, p2 = parts[0].strip(), parts[-1].strip()
                if len(p2.split()) > 6:
                    result.append(p1 + ".")
                    result.append(p2[0].upper() + p2[1:])
                    i += 1
                    continue

        if wc < 8 and i + 1 < len(sentences) and random.random() < 0.2:
            n = sentences[i + 1].strip()
            if n and len(n.split()) > 4:
                j = random.choice([", and ", "; ", ". "])
                result.append(s + j + n[0].lower() + n[1:])
                i += 2
                continue

        result.append(s)
        i += 1
    return " ".join(result)


def add_imperfections(text: str) -> str:
    """Add natural speech patterns that formal AI writing avoids."""

    # Start some mid-text sentences with conjunctions
    if random.random() < 0.3:
        parts = re.split(r'(?<=[.!?])\s+', text)
        for idx in range(1, len(parts)):
            f4 = parts[idx][:4].lower()
            if f4 not in ("and ", "but ", "so  ", "or  ") and random.random() < 0.12:
                s = random.choice(["And ", "But ", "So "])
                parts[idx] = s + parts[idx][0].lower() + parts[idx][1:]
        text = " ".join(parts)

    # Contractions (~35% per type)
    pairs = [
        (r"(?i)\bwill not\b", "won't"),
        (r"(?i)\bcannot\b", "can't"),
        (r"(?i)\bwould have\b", "would've"),
        (r"(?i)\bcould have\b", "could've"),
        (r"(?i)\bshould have\b", "should've"),
        (r"(?i)\bthere is\b", "there's"),
        (r"(?i)\bthat is\b", "that's"),
        (r"(?i)\bit is\b", "it's"),
        (r"(?i)\bdoes not\b", "doesn't"),
        (r"(?i)\bdo not\b", "don't"),
        (r"(?i)\bare not\b", "aren't"),
        (r"(?i)\bwas not\b", "wasn't"),
        (r"(?i)\bhas not\b", "hasn't"),
        (r"(?i)\bhave not\b", "haven't"),
        (r"(?i)\bdid not\b", "didn't"),
        (r"(?i)\bwould not\b", "wouldn't"),
        (r"(?i)\bcould not\b", "couldn't"),
        (r"(?i)\bshould not\b", "shouldn't"),
    ]
    for pat, repl in pairs:
        if random.random() < 0.35:
            text = re.sub(pat, repl, text, count=1 + int(random.random() < 0.3))

    # Drop some Oxford commas
    if random.random() < 0.3:
        text = re.sub(r'(?<=[a-zA-Z]),\s+and\b', ' and', text)
        text = re.sub(r'(?<=[a-zA-Z]),\s+or\b', ' or', text)

    return text


def humanize(text: str, aggressive: bool = False) -> str:
    for pat, repl in PHRASE_PATTERNS:
        if callable(repl):
            text = re.sub(pat, repl, text)
        else:
            text = re.sub(pat, repl, text)

    text = swap_words(text)
    text = thin_transitions(text)
    text = _fix_a_an(text)
    text = vary_sentence_lengths(text)
    text = add_imperfections(text)

    if aggressive:
        text = vary_sentence_lengths(text)
        text = thin_transitions(text)
        text = swap_words(text)
        text = add_imperfections(text)

    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strip AI tells from text")
    parser.add_argument("--aggressive", "-a", action="store_true",
                        help="Double pass for more aggressive rewriting")
    args = parser.parse_args()
    txt = sys.stdin.read()
    if not txt.strip():
        print("No input", file=sys.stderr)
        sys.exit(1)
    print(humanize(txt, aggressive=args.aggressive))
