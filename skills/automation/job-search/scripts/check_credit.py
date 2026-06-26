#!/usr/bin/env python3
"""Print remaining Apify free-tier credits."""
import os, requests

token = os.getenv("APIFY_TOKEN") or open(os.path.expanduser("~/.hermes/secrets/apify.env")).read().split("=", 1)[1].strip()
r = requests.get("https://api.apify.com/v2/user/credits", headers={"Authorization": f"Bearer {token}"})
print(f"Remaining credits: ${r.json()['data']['remaining']:.2f}")