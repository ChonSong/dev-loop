# Multi-Page HTML Resume Pattern

Use this when content exceeds one A4 page. The key insight: **don't rely on CSS `page-break-before` inside a flex container with sidebar + main** — the sidebar is always shorter than the main column, leaving empty space on the continuation page.

Instead, use two completely separate `.page` divs.

## Page 1: Full Layout

```html
<div class="page">
  <!-- Full header with accent bar, name, contact details -->
  <header class="accent-bar px-7 py-5 text-white">
    <div class="flex items-center gap-5">
      <div class="flex-grow">
        <h1 class="text-2xl font-bold tracking-tight mb-0.5">Full Name</h1>
        <p class="text-xs font-light tracking-widest uppercase opacity-90">Target Role</p>
      </div>
      <div class="flex-shrink-0 text-right text-[9.5px] space-y-1 opacity-90">
        <p><i class="fas fa-phone mr-2 w-4 text-center"></i>Phone</p>
        <p><i class="fas fa-envelope mr-2 w-4 text-center"></i>Email</p>
        <p><i class="fas fa-map-marker-alt mr-2 w-4 text-center"></i>Location</p>
        <p><i class="fab fa-github mr-2 w-4 text-center"></i>github.com/user</p>
      </div>
    </div>
  </header>

  <!-- Two-column layout -->
  <div class="flex flex-1">
    <!-- Sidebar (30%) -->
    <aside class="w-[30%] bg-slate-50 p-3 border-r border-slate-200" style="width: 214.8px;">
      <!-- Skills, education, philosophy, etc. -->
    </aside>

    <!-- Main (70%) — FIRST HALF of content -->
    <main class="w-[70%] p-4">
      <!-- Professional Summary -->
      <!-- Experience (full entries) -->
      <!-- Projects section heading ONLY IF there's room -->
    </main>
  </div>
</div>
```

## Page 2: Continuation — Full Width

```html
<div class="page">
  <!-- Slim header: just name + title, no contact details -->
  <header class="accent-bar px-7 py-3 text-white">
    <div class="flex items-center gap-4">
      <h2 class="text-lg font-bold tracking-tight">Full Name</h2>
      <span class="text-[10px] font-light tracking-widest uppercase opacity-70">— Target Role</span>
    </div>
  </header>

  <!-- Full width — no sidebar -->
  <div class="flex-1 px-7 py-4">
    <!-- Remaining sections: Projects, etc. -->
    <!-- Each entry gets class="no-break" to keep it together -->
  </div>
</div>
```

## CSS Required

```css
@page { size: A4; margin: 0; }
.page {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto;
  background: white;
  display: flex;
  flex-direction: column;
}
.no-break { page-break-inside: avoid; }
@media print {
  .page { min-height: auto; }
}
```

## Content Split Heuristic

| If content includes... | Put on page 1 | Put on page 2 |
|---|---|---|
| Professional Summary | ✓ | |
| Experience (full roles with bullets) | ✓ | |
| Projects (4+ entries) | First 1-2 entries | Remaining entries |
| Empty stubs / "and more" footer | | ✓ |

**Rule of thumb:** If page 1 has the Experience section ending within ~30mm of the page bottom, the split is good. If there's 60mm+ of whitespace, move content from page 2 back, or add spacing between sections on page 1.

## Verification

Always run this before sending:

```python
import fitz
doc = fitz.open('/path/to/output.pdf')
print(f'Pages: {len(doc)}')
for i in range(len(doc)):
    text = doc[i].get_text()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    print(f'Page {i+1}: {len(lines)} lines — first: {lines[0]}, last: {lines[-1]}')
```

Expected: Page 1 has ~100-140 lines (dense sidebar + main). Page 2 has ~25-40 lines (projects only, full width). If page 2 has <20 lines the project section is too sparse — add breathing room or expand project descriptions.
