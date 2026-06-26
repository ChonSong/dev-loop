---
name: morning-briefing
description: Generate a comprehensive morning briefing with world news, tech, unrestricted models, weather (Quakers Hill NSW), email, calendar, and system status
always: true
---

# Morning Briefing Skill

Generate a comprehensive morning briefing covering all of Sean's interests. This skill aggregates information from multiple sources and presents findings in a structured format.

## Trigger

- Keywords: "morning briefing", "daily briefing", "good morning"
- Cron: 8 AM Mon-Fri New York time (via openclawhub Telegram group)

## Topics to Cover

The briefing MUST include ALL 8 sections in order:

### 1. 🌍 World News
- Fetch top headlines from BBC World News RSS
- Include top 5 breaking headlines with summaries
- Command: `curl -s 'https://feeds.bbci.co.uk/news/world/rss.xml' | python3 -c "import sys,xml.etree.ElementTree as ET; root=ET.parse(sys.stdin).getroot(); [print('- ' + i.find('title').text.strip()) for i in root.findall('.//item')[:5]]"`

### 2. 💻 Tech & AI News
- Search for latest AI/tech news using web_search
- Include major announcements, product releases, and trends
- Topics: AI models, big tech, regulations, industry moves
- Use: `web_search` tool with query "AI technology news today 2026"

### 3. 🤖 Unrestricted Models
- Search for trending uncensored models on HuggingFace
- Include: Dolphin, EverythingLM, AI Power, other popular uncensored models
- Mention new releases and interesting models
- Use: `web_search` tool with query "trending uncensored LLM models HuggingFace 2026"

### 4. 🌤 Weather - Quakers Hill, NSW, Australia
- Use wttr.in for weather data
- Command: `curl -s 'wttr.in/Quakers+Hill,+NSW,+Australia?format=%l:+%c+%t,+feels+like+%f,+humidity+%h,+wind+%w,+UV+%u,+rain+%p'`
- Also get visual forecast: `curl -s 'wttr.in/Quakers+Hill,+NSW?format=3'`
- Include: current temp, feels like, humidity, wind, UV index, rain chance

### 5. 📧 Email Status (FRESH SCAN)
- ALWAYS run a fresh email scan using Gmail skill
- Command: `gog gmail list --unread --limit 5`
- Summarize: unread count, important emails, sender breakdown, action needed

### 6. 📅 Calendar
- Check Google Calendar for today's events
- Use: `gog calendar list --today`
- Include: meetings, appointments, reminders

### 7. ⚙️ System Resources (ALWAYS FETCH FRESH)
- Memory: `free -h`
- CPU: `uptime`
- Disk space: `df -h`

### 8. 💾 Disk Space Analysis
- Only include if any mount >80% usage
- Command: `df -h | awk '{print $5 " " $6}' | grep -v 'Use%' | while read pct mp; do num=${pct%\%}; [ "$num" -gt 80 ] && echo "⚠️ $mp at $pct"; done`
- If no output: skip this section entirely

## Output Format

Generate a well-formatted briefing with emoji headers. Keep each section punchy — 3-5 bullets max per section. Format for Telegram (no markdown tables, use bullet lists).

Deliver directly to the Telegram group `openclawhub`.
