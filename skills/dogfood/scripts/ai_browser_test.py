#!/usr/bin/env python3
"""
AI Detection Browser Tests — Run on host via SSH tunnel
Usage: python3 ai_browser_test.py
Requires: pyppeteer installed on host (pip3 install --break-system-packages pyppeteer)
Requires: Chrome at /usr/bin/google-chrome-stable
Requires: SSH key at /home/hermeswebui/.hermes/container_key
"""
import asyncio
from pyppeteer import launch

TEST_TEXT = """What matters is what Japan did not borrow. The imperial institution survived and was reconstituted as a modern constitutional emperor with divine ancestry. Bushido was codified as a distinctively Japanese warrior code. Japanese identity was explicitly framed as continuous with the pre-modern past even as the foundations of daily life were transformed. Murphey observes that Japanese national consciousness, already developing under Tokugawa unification, meant they were able to adopt ideas and techniques from foreign sources, as they long had done from China, without in any way diluting their own cultural and national identity"""

HUMAN_TEXT = """Climate change has likely led to the decline of some of Scotland's mountain plants, according to new research. Scientists said many of the species relied on snow cover remaining high on hills until late spring. The study looked at more than 100 plant species across Scottish mountains over 50 years."""

AI_TEXT = """The convergence of artificial intelligence and sustainable development represents one of the most significant technological paradigm shifts in human history. Machine learning algorithms have demonstrated remarkable capabilities in optimizing complex systems."""

async def click_button_with_text(page, text_pattern):
    """Find and click a button containing text_pattern (case-insensitive)."""
    buttons = await page.querySelectorAll('button')
    for btn in buttons:
        btn_text = await page.evaluate('(el) => el.innerText', btn)
        if text_pattern.lower() in btn_text.lower():
            await btn.click()
            return btn_text
    return None

async def get_result_after_click(page, wait_seconds=8):
    """Generic result extractor after scan/detect click."""
    await asyncio.sleep(wait_seconds)
    result = await page.evaluate("""() => {
        const text = document.body.innerText;
        const percents = text.match(/(\\d+)%/g) || [];
        return {
            percents: [...new Set(percents)],
            body: text.substring(0, 2000)
        };
    }""")
    return result

async def test_gptzero():
    print('\n=== GPTZero ===')
    browser = await launch(
        headless=True,
        executablePath='/usr/bin/google-chrome-stable',
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
    )
    page = await browser.newPage()
    await page.setViewport({'width': 1280, 'height': 800})
    await page.evaluateOnNewDocument('''() => {
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
    }''')
    try:
        await page.goto('https://gptzero.me', {'waitUntil': 'networkidle2', 'timeout': 30000})
        await asyncio.sleep(2)
        await page.click('textarea')
        await page.type('textarea', TEST_TEXT, {'delay': 5})
        print(f'Typed {len(TEST_TEXT)} chars')
        btn = await click_button_with_text(page, 'Scan')
        print(f'Clicked: {btn}')
        result = await get_result_after_click(page, 15)
        print('Percentages:', result['percents'][:10])
        print('Body:', result['body'][300:1200])
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await browser.close()

async def test_zerogpt():
    print('\n=== ZeroGPT ===')
    browser = await launch(
        headless=True,
        executablePath='/usr/bin/google-chrome-stable',
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
    )
    page = await browser.newPage()
    await page.setViewport({'width': 1280, 'height': 800})
    await page.evaluateOnNewDocument('''() => {
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
    }''')
    try:
        await page.goto('https://www.zerogpt.com', {'waitUntil': 'networkidle2', 'timeout': 30000})
        await asyncio.sleep(2)
        textarea = await page.querySelector('textarea')
        if textarea:
            await textarea.click()
            await page.type('textarea', TEST_TEXT, {'delay': 5})
            print(f'Typed {len(TEST_TEXT)} chars')
            btn = await click_button_with_text(page, 'Detect')
            print(f'Clicked: {btn}')
            await asyncio.sleep(8)
            result = await page.evaluate("""() => {
                const text = document.body.innerText;
                const lines = text.split('\\n');
                const resultLine = lines.find(l => 'Your Text'.lower() in l.toLowerCase() || (l.includes('%') && l.length < 100));
                return { resultLine, body: text.substring(0, 1000) };
            }""")
            print('Result:', result['resultLine'])
            print('Output:', result['body'][:600])
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await browser.close()

async def test_quillbot():
    print('\n=== QuillBot AI ===')
    browser = await launch(
        headless=True,
        executablePath='/usr/bin/google-chrome-stable',
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
    )
    page = await browser.newPage()
    await page.setViewport({'width': 1280, 'height': 800})
    await page.evaluateOnNewDocument('''() => {
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
    }''')
    try:
        await page.goto('https://quillbot.com/ai-content-detector', {'waitUntil': 'networkidle2', 'timeout': 30000})
        await asyncio.sleep(2)
        editable = await page.querySelector('[contenteditable="true"]')
        if editable:
            await editable.click()
            await page.type('[contenteditable="true"]', TEST_TEXT, {'delay': 5})
            print(f'Typed {len(TEST_TEXT)} chars')
            btn = await click_button_with_text(page, 'detect')
            if not btn:
                btn = await click_button_with_text(page, 'Paste')
            print(f'Clicked: {btn}')
            await asyncio.sleep(8)
            result = await page.evaluate("""() => document.body.innerText.substring(0, 1000)""")
            print('Result:', result[:600])
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await browser.close()

async def test_zerogpt_ai_sanity():
    """Sanity check: known AI text should return non-zero AI %"""
    print('\n=== ZeroGPT Sanity (known AI text) ===')
    browser = await launch(
        headless=True,
        executablePath='/usr/bin/google-chrome-stable',
        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
    )
    page = await browser.newPage()
    await page.setViewport({'width': 1280, 'height': 800})
    await page.evaluateOnNewDocument('''() => {
        Object.defineProperty(navigator, 'webdriver', {get: () => false});
    }''')
    try:
        await page.goto('https://www.zerogpt.com', {'waitUntil': 'networkidle2', 'timeout': 30000})
        await asyncio.sleep(2)
        textarea = await page.querySelector('textarea')
        if textarea:
            await textarea.click()
            await page.type('textarea', AI_TEXT, {'delay': 5})
            print(f'Typed {len(AI_TEXT)} chars (AI text)')
            btn = await click_button_with_text(page, 'Detect')
            print(f'Clicked: {btn}')
            await asyncio.sleep(8)
            result = await page.evaluate("""() => document.body.innerText.substring(0, 800)""")
            print('AI text result:', result[:500])
    except Exception as e:
        print(f'Error: {e}')
    finally:
        await browser.close()

async def main():
    await test_gptzero()
    await asyncio.sleep(2)
    await test_zerogpt()
    await asyncio.sleep(2)
    await test_quillbot()
    await asyncio.sleep(2)
    await test_zerogpt_ai_sanity()

asyncio.get_event_loop().run_until_complete(main())