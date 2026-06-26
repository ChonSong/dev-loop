# Morning Briefing — Tool Reference

## wttr.in JSON Extraction

**Endpoint:** `https://wttr.in/Granville,+NSW,+Australia?format=j1`

**Example Python parsing for Agentic workflow (non-cron):**
```python
# Fires inside the agent via execute_code — NOT available in cron mode
import json

data = json.loads(raw_json)

current = data['current_condition'][0]
temp_c = current['temp_C']
feelsLike = current['FeelsLikeC']
humidity = current['humidity']
wind_speed = current['windspeedKmh']
wind_dir = current['winddir16Point']
uv = current['UVIndex']
rain_mm = current['precipMM']

print(f"{temp_c}°C, feels {feelsLike}°C, humidity {humidity}%, wind {wind_speed}km/h {wind_dir}, UV {uv}, rain {rain_mm}mm")
```

**Fallback (plain text):**
```
https://wttr.in/Granville,+NSW?format=3
→ "Granville, NSW: ☀️ +18°C"
```

**Cron-mode weather (bare curl, no pipes to python):**
```
curl -s 'https://wttr.in/Granville,+NSW?format=%l:+%c+%t,+feels+like+%f,+humidity+%h,+wind+%w,+UV+%u'
```

---

## BBC World News RSS

**Endpoint:** `https://feeds.bbci.co.uk/news/world/rss.xml`

Use `web_extract(urls=['https://feeds.bbci.co.uk/news/world/rss.xml'])` for parsing. The RSS XML is automatically extracted into readable markdown.

**Tech RSS (fallback):** `https://feeds.bbci.co.uk/news/technology/rss.xml`

---

## Optional: Email via himalaya

Not configured. If installed:
```bash
himalaya list --unread --limit 5
```
Auth: `~/.config/himalaya/config.toml`

---

## Optional: Calendar via gcalcli

Not configured. If installed:
```bash
gcalcli --nocolor agenda today
```
