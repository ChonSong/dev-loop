# Quickstart: Job-search Skill

## 1. Prerequisites
- Free Apify account (https://apify.com/signup)
- API token: *Account → Integrations → API token*

## 2. Store the token
```bash
mkdir -p ~/.hermes/secrets
echo "APIFY_TOKEN=apify_api_cyGeU5JxD8TSBO3KeM9lzO2ige1o3p3blhXX" > ~/.hermes/secrets/apify.env
chmod 600 ~/.hermes/secrets/apify.env
```

## 3. Run a test (Indeed)
```bash
python3 ~/.hermes/skills/automation/job-search/scripts/run_search.py \\
  --positions "Data Scientist" \\
  --locations "Sydney, NSW" \\
  --country "AU" \\
  --max 5
```

Expected output: JSON array of jobs + credit usage ≤ $0.05.

## 4. Run a test (Seek)
```bash
python3 ~/.hermes/skills/automation/job-search/scripts/seek_search.py \\
  --positions "Data Scientist" \\
  --locations "Sydney, NSW" \\
  --max 5
```

Expected output: JSON array of Seek jobs + credit usage ≤ $0.10.

## 5. Broaden Your Search (Recommended)
For comprehensive Australian job market coverage, run BOTH Indeed AND Seek:

```bash
# Run Indeed search
python3 ~/.hermes/skills/automation/job-search/scripts/run_search.py \\
  --positions "Data Scientist" \\
  --locations "Sydney, NSW" \\
  --country "AU" \\
  --max 200 \\
  --outdir ~/.hermes/jobs/indeed

# Run Seek search
python3 ~/.hermes/skills/automation/job-search/scripts/seek_search.py \\
  --positions "Data Scientist" \\
  --locations "Sydney, NSW" \\
  --max 200 \\
  --outdir ~/.hermes/jobs/seek

# Combine results (optional)
jq -s '.[0] + .[1]' ~/.hermes/jobs/indeed/*.json ~/.hermes/jobs/seek/*.json \\
  > ~/.hermes/jobs/combined_$(date +%s).json
```

## 6. Monitor Your Credits
```bash
python3 ~/.hermes/skills/automation/job-search/scripts/check_credit.py
```

## Best Practices
See `references/best_practices.md` for:
- Reliable execution patterns (why direct scripts beat Hermes CLI)
- Timing expectations and polling intervals
- Credit management guidelines
- Error handling checklist
- Combining results from multiple sources
- Production-ready search scripts