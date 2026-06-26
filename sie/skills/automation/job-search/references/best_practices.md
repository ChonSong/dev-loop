# Best Practices for Reliable Job Search Execution

## Why Direct Scripts Beat Hermes CLI Commands

Based on field testing (June 2026), the most reliable approach for job searching via Apify is using direct Python scripts rather than Hermes CLI commands like `hermes -z` or attempting to use the non-existent `hermes skill run`.

### Problems with Hermes CLI Approaches

1. **`hermes -z "prompt" -s job-search`** (One-shot mode)
   - Silently fails with "no final response was produced" when the model doesn't invoke Apify tools
   - No way to debug why the model didn't call the tools
   - Depends on model's ability to correctly format and execute the skill

2. **`hermes skill run`**
   - This subcommand does not exist in Hermes v0.16.0
   - Attempting to use it results in "invalid choice: 'skill'" error

3. **`hermes chat -p`**
   - The `-p` flag is not a valid argument
   - Correct flag is `-z` for one-shot mode

### Why Direct Scripts Work Reliably

Direct Python scripts bypass the Hermes agent/model entirely:
- Make direct HTTP calls to Apify API
- Full control over request/response handling
- Explicit error handling and retry logic
- Visible progress logging
- No dependency on model tool invocation success

## Recommended Execution Pattern

For production job searches, use this pattern:

```bash
# 1. Write search script to temporary file (or use existing scripts/)
cat > /tmp/job_search.py << 'EOF'
#!/usr/bin/env python3
import os, sys, json, time, urllib.request, urllib.error

# [Insert script content here - use run_search.py or seek_search.py as template]
# Key: Always include progress logging and explicit polling

python3 -u /tmp/job_search.py 2>&1
EOF

# 2. Run with unbuffered output for real-time progress
python3 -u /tmp/job_search.py

# 3. OR use the existing scripts directly (recommended)
python3 ~/.hermes/skills/automation/job-search/scripts/run_search.py --positions "Data Scientist" --locations "Sydney, NSW" --country AU --max 200
python3 ~/.hermes/skills/automation/job-search/scripts/seek_search.py --positions "Data Scientist" --locations "Sydney, NSW" --max 200
```

## Timing Expectations

| Scraper | Typical Runtime | Polling Interval | Max Attempts |
|---------|----------------|------------------|--------------|
| Indeed AU | 2-5 minutes | 10 seconds | 60 attempts |
| Seek AU/NZ | 3-8 minutes | 15 seconds | 120 attempts |

## Credit Management

- Indeed AU: ~$0.06 per 1,000 results (~83k jobs/$5 free tier)
- Seek AU/NZ: ~$0.20 per 1,000 results (~25k jobs/$5 free tier)
- Always check remaining credits before large searches:
  ```bash
  python3 ~/.hermes/skills/automation/job-search/scripts/check_credit.py
  ```

## Error Handling Checklist

Before declaring a search "failed", verify:
1. ✅ Actor run reached SUCCEEDED status (not FAILED/TIMED-OUT/ABORTED)
2. ✅ Dataset ID was returned by the run actor call
3. ✅ Dataset fetch returned valid JSON array
4. ✅ Results file was written to expected location
5. ✅ Credit usage reported and within expected bounds

## Combining Results from Multiple Sources

To combine Indeed and Seek results for deduplication and analysis:

```bash
# Install jq if not available: apt-get install -y jq

# Combine all Indeed and Seek jobs from today
find ~/.hermes/jobs -name "*.json" -newermt "today" | xargs jq -s '.[0] + .[1]' > combined_today.json

# Deduplicate by job URL (keep first occurrence)
jq -n 'reduce inputs as $item ({}; .[$item.url] //= $item)' combined_today.json | jq -s '.' > deduplicated.json

# Count unique positions
jq 'map(.title) | unique | length' deduplicated.json
```