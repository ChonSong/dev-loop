#!/usr/bin/env python3
"""
SEEK Batch Quick Apply — reusable template.

Usage:
  1. Ensure Tandem Browser is running (bash ~/.hermes/scripts/start-tandem.sh)
  2. Edit the JOBS list below with target job URLs
  3. python3 this_script.py

The script handles the full Quick Apply flow:
  - Navigate to job page
  - Click Quick Apply
  - Select stored resume (if dropdown appears)
  - Fill employer question selects (right to work, salary, notice, etc.)
  - Click Continue through all steps
  - Click Submit application
  - Verify submission
"""
import json, urllib.request, time

API = "http://127.0.0.1:3099"

# ── EDIT THESE: job URLs to process ──
JOBS = [
    # ("Role Name @ Company", "https://au.seek.com/job/XXXXXXXXX"),
]


def evaluate(expression):
    """Evaluate JavaScript in the Tandem browser page context."""
    data = json.dumps({"expression": expression}).encode()
    req = urllib.request.Request(f"{API}/evaluate", data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp.get("result")

def navigate(url):
    data = json.dumps({"url": url}).encode()
    req = urllib.request.Request(f"{API}/navigate", data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req)
    time.sleep(3)

def click_by_testid(testid):
    """Click a button identified by data-testid attribute."""
    return evaluate(f"""
    (() => {{
        const btn = document.querySelector('button[data-testid="{testid}"]');
        if (btn) {{ btn.scrollIntoView({{block: 'center'}}); btn.click(); return 'clicked'; }}
        return 'none';
    }})()
    """)

def click_continue():
    """Click Continue button, handling zero-width characters."""
    return evaluate("""
    (() => {
        const btn = document.querySelector('button[data-testid="continue-button"]');
        if (btn) { btn.scrollIntoView({block: 'center'}); btn.click(); return 'clicked'; }
        // Fallback: fuzzy match any button containing Continue
        for (const b of document.querySelectorAll('button')) {
            if (b.textContent.includes('Continue')) {
                b.scrollIntoView({block: 'center'}); b.click(); return 'fuzzy';
            }
        }
        return 'none';
    })()
    """)

def fill_empty_selects():
    """Fill any select elements that don't have a value selected."""
    return evaluate("""
    (() => {
        const selects = document.querySelectorAll('select');
        let filled = 0;
        for (const s of selects) {
            if ((!s.value || s.value === '') && s.options.length > 1) {
                for (const o of s.options) {
                    if (o.value && o.value !== '') {
                        s.value = o.value;
                        s.dispatchEvent(new Event('change', {bubbles: true}));
                        filled++;
                        break;
                    }
                }
            }
        }
        return filled;
    })()
    """)

def click_submit():
    """Click the Submit application button."""
    return evaluate("""
    (() => {
        for (const b of document.querySelectorAll('button')) {
            if (b.textContent.includes('Submit application')) {
                b.scrollIntoView({block: 'center'}); b.click(); return 'submitted';
            }
        }
        return 'none';
    })()
    """)

def fill_all_fields():
    """Fill ALL form input types — selects, textareas, radios, checkboxes.
    Handles React SPAs that need native value setters and label clicks."""
    return evaluate("""
    (() => {
        // 1. TEXTAREAS — native value setter for React
        document.querySelectorAll('textarea').forEach(function(ta) {
            if (!ta.value) {
                var ns = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                ns.call(ta, 'Yes');
                ta.dispatchEvent(new Event('input', {bubbles: true}));
            }
        });
        // 2. SELECTS — pick first real option
        document.querySelectorAll('select').forEach(function(s) {
            if ((!s.value || s.value === '') && s.options.length > 1) {
                for (var i = 0; i < s.options.length; i++) {
                    var o = s.options[i];
                    if (o.value && o.value !== '') { s.value = o.value; s.dispatchEvent(new Event('change', {bubbles: true})); break; }
                }
            }
        });
        // 3. RADIOS — click LABEL, not the input (React needs label clicks)
        var groups = {};
        document.querySelectorAll('input[type="radio"]').forEach(function(r) {
            var n = r.name || '';
            if (!groups[n]) groups[n] = [];
            groups[n].push(r);
        });
        for (var name in groups) {
            var radios = groups[name];
            var anyChecked = radios.some(function(r) { return r.checked; });
            if (!anyChecked && name) {
                var last = radios[radios.length - 1];
                var label = document.querySelector('label[for="' + last.id + '"]');
                if (label) label.click();
                else { last.checked = true; last.dispatchEvent(new Event('change', {bubbles: true})); }
            }
        }
        // 4. CHECKBOXES — native setter
        document.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
            if (!cb.checked) {
                var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
                ns.call(cb, true);
                cb.dispatchEvent(new Event('change', {bubbles: true}));
            }
        });
        return 'filled';
    })()
    """)

def quick_apply(title, url):
    print(f"\n{'='*60}")
    print(f"Applying: {title}")
    
    navigate(url)
    time.sleep(1)
    
    # Click Quick Apply button
    r = evaluate("""
    (() => {
        for (const b of document.querySelectorAll('button, a')) {
            if (b.textContent.trim() === 'Quick apply') {
                b.scrollIntoView({block: 'center'}); b.click(); return 'clicked';
            }
        }
        return 'none';
    })()
    """)
    if r == 'none':
        print(f"  ⚠️  No Quick Apply button — already applied or not available")
        return False
    print(f"  QA clicked: {r}")
    time.sleep(3)
    
    # Step through form (up to 10 steps)
    for step in range(10):
        text = evaluate("document.body.innerText") or ""
        
        # Check for success
        if "applied" in text.lower():
            print(f"  ✅ Submitted!")
            return True
        
        # Check for submit button
        if "Submit application" in text:
            evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(0.5)
            r = click_submit()
            print(f"  Submit: {r}")
            time.sleep(3)
            text = evaluate("document.body.innerText") or ""
            if "applied" in text.lower():
                print(f"  ✅ Submitted!")
                return True
        
        # Fill all form fields (selects, textareas, radios, checkboxes)
        filled = fill_all_fields()
        if filled:
            print(f"  Filled form fields")
        
        # Try Continue
        r = click_continue()
        if r == 'none':
            print(f"  ⚠️  No Continue button at step {step+1}")
            return False
        time.sleep(2)


if __name__ == "__main__":
    if not JOBS:
        print("ERROR: No jobs configured. Edit the JOBS list at the top of this script.")
        sys.exit(1)
    
    results = []
    for title, url in JOBS:
        ok = quick_apply(title, url)
        results.append((title, "✅" if ok else "❌"))
    
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    for title, status in results:
        print(f"  {status} {title}")
