#!/usr/bin/env python3
"""Queue a LinkedIn post for scheduling via n8n webhook or file-based queue."""

import sys
import json
import os
from datetime import datetime, timezone

QUEUE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "linkedin-queue")
os.makedirs(QUEUE_DIR, exist_ok=True)

def queue_post(text: str) -> dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    entry = {
        "id": timestamp,
        "text": text,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "platform": "linkedin",
    }
    filepath = os.path.join(QUEUE_DIR, f"post-{timestamp}.json")
    with open(filepath, "w") as f:
        json.dump(entry, f, indent=2)
    return entry

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 linkedin-queue-post.py 'Post text here'")
        sys.exit(1)
    text = sys.argv[1]
    result = queue_post(text)
    print(json.dumps(result, indent=2))
