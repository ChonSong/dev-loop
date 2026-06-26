import json, urllib.request, time

# HN Front Page - top 10 stories with points
def hn_front_page():
    url = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=10"
    resp = urllib.request.urlopen(url, timeout=10)
    data = json.loads(resp.read())
    for h in data.get('hits', []):
        print(f"{h['title']} ({h['points']} pts)")

# HN AI/LLM stories from last 12 hours
def hn_ai_stories():
    twelve_hours_ago = int(time.time() - 43200)
    url = f"https://hn.algolia.com/api/v1/search?query=AI+LLM+GPT+Claude+Gemini&tags=story&numericFilters=created_at_i>{twelve_hours_ago}&hitsPerPage=8"
    resp = urllib.request.urlopen(url, timeout=10)
    data = json.loads(resp.read())
    for h in data.get('hits', []):
        print(f"{h['title']} ({h['points']} pts)")

# Fetch details for a specific HN story by ID
def hn_story_details(story_id):
    url = f"https://hn.algolia.com/api/v1/items/{story_id}"
    resp = urllib.request.urlopen(url, timeout=10)
    item = json.loads(resp.read())
    return item
