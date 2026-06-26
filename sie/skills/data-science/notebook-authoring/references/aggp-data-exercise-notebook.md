# Example: AGGP Data Stream Data Exercise Notebook

Generated June 2026 for the 2027 Australian Government Graduate Program (Data Stream) interview.

## Structure

- 35 cells total: 13 markdown + 22 code
- 46 KB .ipynb
- 10 sections from CARR Method → Mock Walkthrough → Pitfalls

## Key Design Decisions

**Two dataset generators** — retail (stores, sales, ratings) and government (agencies, processing times, satisfaction). Each creates different data per seed so candidates can't memorise answers. Injected patterns: weekend effects, remote region slowdowns, complexity correlations.

**Statistical Tests Master Table** — 14-row reference table covering parametric/non-parametric tests, assumptions, when to use, Python code, and interpretation. Includes decision flow for normality → homogeneity → test selection, plus effect size thresholds (Cohen's d, r, rho, Cramer's V, eta-squared). Added as a dedicated markdown cell after the Quick Reference section, then patched into the generator script for persistence.

**Mock walkthrough** — self-contained scenario ("reduce processing times by 15%") that runs end-to-end and produces a recommendation with quantified impact estimates.

**Practice task picker** — random selection from 6 tasks with hints, so candidates can simulate the real assessment.

## Generator Script Pattern

```python
# gen_notebook.py — single file, no dependencies beyond json + stdlib
cells = []

def M(lines):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": [l+'\n' for l in lines]})

def C(lines):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": [l+'\n' for l in lines]})

# ... build content ...

notebook = {"nbformat": 4, "nbformat_minor": 4,
    "metadata": {"kernelspec": {"display_name": "Python 3", ...}},
    "cells": cells}

with open("output.ipynb", "w") as f:
    json.dump(notebook, f, indent=1)
```

## Escaping Fix — Trailing Backslash in ASCII Art

The pyramid diagram in Section 7 (Recommendation Framework) exposed a Python string-escaping gotcha. Lines like `'              /     +-------------+     \\',` — where `\\'` at line-end is meant as a literal backslash in markdown — caused `SyntaxError: unterminated string literal` because Python interprets `\'` as an escaped single quote (string continues), not a backslash.

**Fix applied across 5 lines in the generator script:** doubled the backslash so `\\'` becomes `\\'` (i.e. `\\` = literal backslash, `'` = close string). The ASCII art ends with one trailing backslash per line in the notebook output.

This is now captured as an explicit pitfall in the notebook-authoring skill's "String Escaping Pitfalls" section.

- **Filename:** `AGGP Data Stream - Data Exercise Masterclass.ipynb`
- **Drive link:** Shared with public read access
- **MIME type:** `application/x-ipynb+json` (added to upload_drive.py)
