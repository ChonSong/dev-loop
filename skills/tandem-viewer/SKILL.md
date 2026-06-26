---
name: tandem-viewer
description: Tandem Browser viewer for viewing and interacting with web content via CDP (Chrome DevTools Protocol). Includes navigation, screenshot capture, element interaction, and troubleshooting for browser-based applications.
tags: [tandem, cdp, viewer, browser, automation]
category: productivity
---
## Tandem Viewer - Core Concepts

### What is Tandem Viewer?
Tandem Viewer is a lightweight HTTP server that connects to Tandem Browser's CDP (Chrome DevTools Protocol) to provide a web-based interface for viewing and interacting with web content. It allows you to:
- View live screenshots of the current page
- Navigate to different URLs without leaving your browser
- Interact with page elements (click, fill, scroll)
- Capture screenshots programmatically
- Troubleshoot browser issues in real-time

### Key Features
- **Live Page Viewing**: See the current page state through a dedicated viewer at `http://localhost:3099`
- **Direct Navigation**: Enter URLs directly in the viewer's URL input field
- **Element Interaction**: Click on elements, fill forms, and execute JavaScript
- **CAPTCHA Handling**: View and solve CAPTCHA challenges (clock grid, image-based, etc.)
- **Session Persistence**: Maintains the same browser session as Tandem Browser (same cookies, authentication)

### Getting Started

#### 1. Start Tandem Browser
Run the startup script to launch Tandem Browser with CDP enabled:
```bash
bash /home/sc/.hermes/scripts/start-tandem.sh
```

This will:
- Kill any existing processes on ports 9222 and 3099
- Launch Tandem Browser with remote debugging on port 9222
- Start the Electron viewer on port 3099

#### 2. Access the Viewer
Open `http://localhost:3099` in your browser. You should see:
- A toolbar with URL input and navigation controls
- A viewer area showing the current page screenshot
- A status bar indicating connection status

#### 3. Basic Navigation
To navigate to a new page:
1. Type the URL in the input field (e.g., `https://seek.com.au`)
2. Click the "Go" button or press Enter
3. The viewer will update to show the new page

#### 4. Basic Interaction
To interact with elements on the page:
1. Use the "click" button to click on specific coordinates (x, y)
3. Use the "fill" button to enter text into form fields
4. Use the "evaluate" button to run JavaScript in the page context

### CAPTCHA Handling

Tandem Viewer includes specific tools for solving CAPTCHA challenges:

#### Clock Grid CAPTCHA (6-image)
- The CAPTCHA shows a circular grid with numbers 1-9 arranged like a clock face
- Numbers are typically positioned at:
  - 12 o'clock: 1
  - 3 o'clock: 4
  - 6 o'clock: 7
  - 9 o'clock: 10 (or similar)
- The correct sequence is usually clockwise from 12 o'clock
- Click each number in order, then click "Confirm"

#### Common CAPTCHA Types
1. **Clock Grid**: 6-image grid with numbers 1-9 (as described above)
2. **Image-based**: Select specific images from a grid
3. **Text-based**: Enter text from distorted characters
4. **Slider-based**: Drag a slider to complete the verification

### Troubleshooting

#### Common Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Viewer not loading** | Blank page or error message | 1. Ensure Tandem Browser is running (`ps aux | grep tandem`)<br>2. Verify ports 9222 and 3099 are open (`ss -tlnp | grep 9222 3099`)<br>3. Restart the viewer: `killall electron-viewer.js && bash /home/sc/.hermes/scripts/start-tandem.sh` |
| **CAPTCHA not visible** | CAPTCHA not showing in viewer | 1. Ensure you're on the correct page (use `/info` to check available pages)<br>2. Try refreshing the viewer (`/refresh` endpoint)<br>3. Check if the CAPTCHA type changed (different page types may have different CAPTCHA styles) |
| **429 GoUsageLimitError** | "Monthly usage limit reached" | 1. Wait for reset (typically 10 days)<br>2. Use an alternative CAPTCHA solving method (manual input)<br>3. Check if there's a different viewer instance running |
| **Page not loading** | Page fails to load after navigation | 1. Verify the URL is correct<br>2. Check if the page requires authentication<br>3. Try navigating through the Tandem Browser directly instead of via the viewer |
| **Viewer not updating** | Page content doesn't change after navigation | 1. Click the "refresh" button in the viewer toolbar<br>2. Use `/refresh` endpoint to force reload<br>3. Check if the page is using JavaScript-heavy loading (may need to wait) |

### Advanced Usage

#### 1. Programmatic Interaction
You can interact with the viewer using curl commands:

```bash
# Navigate to a URL
curl -X POST http://localhost:3099/navigate -H "Content-Type: application/json" -d '{"url":"https://example.com"}'

# Click on an element (requires coordinates)
curl -X POST http://localhost:3099/click -H "Content-Type: application/json" -d '{"x": 100, "y": 200}'

# Fill a form field
curl -X POST http://localhost:3099/fill -H "Content-Type: application/json" -d '{"selector": "#email", "value": "user@example.com"}'

# Get page info
curl -X POST http://localhost:3099/info -H "Content-Type: application/json"
```

#### 2. Screenshot Capture
To capture a screenshot of the current page:
```bash
curl -X POST http://localhost:3099/screenshot.png
```

This will return a PNG image file that you can view or save.

#### 3. Advanced Interaction
For more complex interactions, you can use the `/evaluate` endpoint to run JavaScript:

```bash
curl -X POST http://localhost:3099/evaluate -H "Content-Type: application/json" -d '{"expression": "document.querySelector(\"#search\").value = \"search term\";"}' 
```

### Best Practices

1. **Always check the current page first** using `/info` before navigating
2. **Use the viewer to verify login states** before attempting to interact with protected content
3. **Save screenshots immediately** when you see important content (the viewer auto-refreshes every 2 seconds)
4. **For CAPTCHA solving**, take a screenshot first, then solve manually while looking at the viewer
5. **Keep the viewer window active** - don't minimize it or close the tab
6. **Use the viewer for debugging** - it's much easier to see what's happening than through Tandem Browser directly

### References
- `references/tandem-viewer-setup.md` - Detailed setup guide
- `templates/tandem-viewer-example.html` - Example HTML for custom viewer configurations
- `scripts/tandem-debug.sh` - Debugging script for Tandem Browser issues
- `https://github.com/your-repo/tandem-viewer` - Official repository (if available)

### Common Pitfalls
- **Port conflicts**: Ensure no other applications are using ports 9222 or 3099
- **Headless mode**: Tandem Browser must be running in non-headless mode for full functionality
- **Session expiration**: Viewer sessions may time out after prolonged inactivity
- **CAPTCHA changes**: Website updates may change CAPTCHA formats - always verify the current type

### When to Use Tandem Viewer
- When you need to view and interact with web content without leaving your current browser
- When dealing with CAPTCHA challenges that require visual confirmation
- When debugging browser-based applications or web automation workflows
- When you need to share the current page state with others (e.g., for collaborative debugging)

### Limitations
- Requires Tandem Browser to be running on your local machine
- Limited to localhost access (not accessible from external networks)
- Cannot interact with pages that require complex JavaScript execution beyond basic DOM manipulation
- Not suitable for high-volume automated scraping (use dedicated web scraping tools instead)

## Related Skills
- **SEEK Quick Apply**: Use Tandem Viewer to navigate SEEK job listings and submit applications
- **AWS Cloud Support Associate**: Use Tandem Viewer to navigate Amazon.jobs and solve CAPTCHA challenges
- **Browser Automation**: Tandem Viewer is a lighter-weight alternative to full browser automation tools

## References
- `references/tandem-viewer-setup.md` - Detailed setup guide
- `templates/tandem-viewer-example.html` - Example HTML for custom viewer configurations
- `scripts/tandem-debug.sh` - Debugging script for Tandem Browser issues
- `https://github.com/your-repo/tandem-viewer` - Official repository (if available)
", "path": "productivity/tandem-viewer/SKILL.md", "skill_dir": "/home/sc/.hermes/skills/productivity/tandem-viewer", "linked_files": {"references": ["references/tandem-viewer-setup.md"], "templates": ["templates/tandem-viewer-example.html"]}, "required_environment_variables": [], "required_commands": [], "missing_required_environment_variables": [], "missing_required_commands": [], "setup_needed": false, "setup_skipped": false, "readiness_status": "available"}