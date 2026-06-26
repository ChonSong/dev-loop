# Systems Engineer HTML CV Template

HTML template pattern for a 1-page technical CV targeting infrastructure/systems engineer roles. This was built for Sean's Junior Systems Engineer application via Harvey Robinson ($105-115k).

## Layout Structure

```
.page (A4, flex column, min-height: 297mm)
  .main (flex: 1 — fills vertical space)
    h1 (name, 16pt)
    .contact (email, phone, location, GitHub link)

    h2 (Summary)
    hr
    p.section-text (2-3 lines)

    .phil-box (optional — parsimony/philosophy box)
      Muted background #f8fafc, accent left border 2px #2d7d6f, 8pt text

    h2 (Skills)
    hr
    .skills-line (two-column via column-count:2, 8.5pt)

    h2 (Experience)
    hr
    .entry × N
      p.job-title (9pt, 600 weight)
      p.job-sub (7.5pt, #2d7d6f — company/date/type)
      p.bullet × N (8pt, 1.5 line-height, 1px margin-bottom)

    h2 (Education)
    hr
    p.section-text (bold degree name, university, year)

  .footer (margin-top: auto — pinned to bottom)
    github.com/ChonSong · Additional details on request
```

## Key CSS Values

| Element | Size | Weight | Colour | Line Height |
|---------|------|--------|--------|-------------|
| Name | 16pt | 700 | #0f172a | — |
| Contact | 8.5pt | 400 | #475569 | — |
| Section heading | 10pt | 700 | #1e293b | — |
| Section text | 8.5pt | 400 | #334155 | 1.55 |
| Job title | 9pt | 600 | #0f172a | — |
| Job subtitle | 7.5pt | 600 | #2d7d6f | — |
| Bullet | 8pt | 400 | #334155 | 1.5 |
| Skills | 8.5pt | 400 | #334155 | 1.7 |
| Footer | 7.5pt | 400 | #94a3b8 | — |
| Philosophy box | 8pt | 400 | #475569 | 1.55 |

## Spacing

- `h2` margin-top: 10px, margin-bottom: 3px
- `hr` margin-bottom: 6px
- `.entry` margin-bottom: 7px
- `.bullet` margin-bottom: 1px, padding-left: 11px, text-indent: -11px
- `.phil-box` padding: 5px 8px, margin-bottom: 6px

## Philosophy Box HTML

```html
<div class="phil-box">
  <strong>Engineering Philosophy — Principle of Parsimony:</strong>
  Given multiple models with equivalent predictive accuracy, the simplest is
  favoured. Grounded in PAC learning theory, VC dimension, and Minimum
  Description Length — applies as much to system architecture as to machine
  learning.
</div>
```

## Two-Column Skills

```html
<div class="skills-line">
  <span class="skills-cat">Containers:</span> Docker, Compose, multi-stage<br>
  <span class="skills-cat">Cloud:</span> Cloudflare (Tunnels, DNS, Access)<br>
  ...
</div>
```

With CSS: `column-count: 2; column-gap: 12px;` — splits naturally into two columns.

## Flexbox Footer Pin

```css
.page { display: flex; flex-direction: column; min-height: 297mm; }
.main { flex: 1; }
.footer { margin-top: auto; }
```

The footer always sits at the bottom of the page regardless of content volume.
