// Blank Space & Overflow Measurement Script
// Run after PDF generation to verify page fit.
// Usage: node measure.cjs (expects .page, .footer, .main selectors in HTML)

const { chromium } = require('playwright');
const CHROME = '/home/sc/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome';

async function measure(htmlPath) {
  const b = await chromium.launch({ executablePath: CHROME });
  const p = await b.newPage({ viewport: { width: 1240, height: 1754 } });
  await p.goto('file://' + htmlPath, { waitUntil: 'networkidle', timeout: 30000 });

  const m = await p.evaluate(() => {
    const page = document.querySelector('.page');
    const footer = document.querySelector('.footer');
    const r = page.getBoundingClientRect();
    const fr = footer.getBoundingClientRect();
    return {
      pageHeightPx: r.height,
      a4HeightPx: 1123,  // A4 at 96 DPI
      footerTopPx: fr.top,
      footerBottomPx: fr.bottom,
      blankPx: r.height - fr.bottom,
      blankPercent: ((r.height - fr.bottom) / r.height * 100).toFixed(1),
      overflows: r.height > 1123 ? 'YES' : 'NO'
    };
  });

  console.log(`Page: ${m.pageHeightPx}px (A4: ${m.a4HeightPx}px)`);
  console.log(`Footer: ${m.footerTopPx}px top, ${m.footerBottomPx}px bottom`);
  console.log(`Blank: ${m.blankPx}px (${m.blankPercent}%)`);
  console.log(`Overflow: ${m.overflows}`);

  if (m.overflows === 'YES') {
    console.log(`⚠️ ${(m.pageHeightPx - m.a4HeightPx).toFixed(0)}px over A4 — tighten spacing`);
  }
  if (parseFloat(m.blankPercent) > 5) {
    console.log(`⚠️ ${m.blankPercent}% blank — content too sparse, loosen spacing`);
  }

  await b.close();
}

const path = process.argv[2];
if (!path) { console.error('Usage: node measure.cjs <path-to-html>'); process.exit(1); }
measure(path).catch(e => { console.error(e); process.exit(1); });
