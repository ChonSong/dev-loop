#!/usr/bin/env python3
"""
APH Hansard Transcript Monitor — v4 (LLM-powered)
Fetches latest Hansard transcripts from APH, extracts structured content via regex,
generates summaries via MiniMax LLM, and posts to Discord.
"""

import urllib.request
import urllib.error
import json
import re
import os
import time
from datetime import datetime

CHANNEL_ID = "1486919044757061652"
STATE_FILE = "/opt/data/aph-hansard-state.json"
TRANSCRIPTS_DIR = "/opt/data/aph-transcripts"
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

MINIMAX_API_URL = "https://api.minimax.io/anthropic/v1/messages"


def load_env_key(prefix):
    # Check environment variable first (always override)
    env_val = os.environ.get(prefix)
    if env_val:
        return env_val
    # Fall back to .env file at /opt/data/.env
    try:
        with open("/opt/data/.env") as f:
            for line in f:
                if line.startswith(prefix + "="):
                    val = line.split("=", 1)[1].strip()
                    if val and not val.startswith("***"):
                        return val
    except Exception:
        pass
    return None


def get_discord_token():
    return load_env_key("DISCORD_BOT_TOKEN")


def get_minimax_key():
    return load_env_key("MINIMAX_API_KEY")


def get_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {"seen_ids": [], "last_run": None}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def fetch_with_retry(url, max_attempts=3, retry_delay=5):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
    }
    for attempt in range(max_attempts):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace"), None
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 504, 429) and attempt < max_attempts - 1:
                print(f"  Attempt {attempt+1} got {e.code}, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                return None, f"HTTP Error {e.code}"
        except Exception as e:
            return None, str(e)
    return None, "Max retries exceeded"


def clean_whitespace(text):
    return re.sub(r'\s+', ' ', text).strip()


def extract_text_from_xml(xml_str):
    """Strip all XML tags to get plain text."""
    return re.sub(r'<[^>]+>', ' ', xml_str).strip()


def parse_hansard_xml_regex(xml_content, chamber_type):
    """
    Parse Hansard XML using regex (more reliable than ET for this format).
    Extracts debate titles, questions, answers, and speaker info.
    """
    result = {
        "date": "",
        "chamber": chamber_type,
        "debate_titles": [],
        "questions": [],
        "total_questions": 0,
        "opening_business": [],
    }

    # Extract date from session header
    date_m = re.search(r'<date>([^<]+)</date>', xml_content)
    if date_m:
        result["date"] = date_m.group(1)

    # Extract all debate/bill titles
    for title in re.findall(r'<title>([^<]+)</title>', xml_content):
        t = clean_whitespace(title)
        if t and len(t) > 4 and len(t) < 200:
            result["debate_titles"].append(t)

    # Extract questions and answers (key structure: <question>...<answer>...)
    # Each question block starts with <question> and has talk.start/talk.text inside
    question_blocks = re.findall(r'<question>(.*?)</question>', xml_content, re.DOTALL)
    answer_blocks = re.findall(r'<answer>(.*?)</answer>', xml_content, re.DOTALL)

    result["total_questions"] = len(question_blocks)

    for i, q_block in enumerate(question_blocks):
        # Extract asker name from talker
        asker_m = re.search(r'<name role="metadata">([^<]+)</name>', q_block)
        asker = asker_m.group(1) if asker_m else "Unknown"

        # Extract question text from talk.text paragraphs (HPS-Small and HPS-Normal)
        q_paragraphs = re.findall(r'<p class="HPS-Small"[^>]*>.*?<span class="HPS-Small">([^<]+)</span>', q_block, re.DOTALL)
        q_paragraphs2 = re.findall(r'<p class="HPS-Normal"[^>]*>.*?<span class="HPS-Normal">([^<]+)</span>', q_block, re.DOTALL)

        q_text_parts = []
        for p in q_paragraphs:
            t = clean_whitespace(p)
            if t and len(t) > 10:
                q_text_parts.append(t)
        for p in q_paragraphs2:
            t = clean_whitespace(p)
            if t and len(t) > 10:
                q_text_parts.append(t)

        q_text = clean_whitespace(" ".join(q_text_parts))

        # Get the answer for this question if available
        answer_text = ""
        if i < len(answer_blocks):
            a_block = answer_blocks[i]
            a_paragraphs = re.findall(r'<p class="HPS-Small"[^>]*>.*?<span class="HPS-Small">([^<]+)</span>', a_block, re.DOTALL)
            a_paragraphs2 = re.findall(r'<p class="HPS-Normal"[^>]*>.*?<span class="HPS-Normal">([^<]+)</span>', a_block, re.DOTALL)

            a_text_parts = []
            for p in a_paragraphs:
                t = clean_whitespace(p)
                if t and len(t) > 10:
                    a_text_parts.append(t)
            for p in a_paragraphs2:
                t = clean_whitespace(p)
                if t and len(t) > 10:
                    a_text_parts.append(t)
            answer_text = clean_whitespace(" ".join(a_text_parts))

        if q_text and len(q_text) > 15:
            result["questions"].append({
                "asker": asker,
                "question": q_text[:800],
                "answer": answer_text[:400] if answer_text else "",
            })

    # Extract top-level debate items (titles from debateinfo, not subdebate)
    debate_infos = re.findall(r'<debateinfo>.*?<title>([^<]+)</title>', xml_content, re.DOTALL)
    result["debate_titles"] = [clean_whitespace(t) for t in debate_infos if clean_whitespace(t)]

    # Get first few debate topics for context
    result["top_issues"] = result["debate_titles"][:15]

    return result


def fetch_and_parse_transcript(hansard_id, chamber_type):
    if chamber_type == "Senate":
        path_prefix = "chamber/hansards"
    else:
        path_prefix = "chamber/hansardr"

    url = f"https://www.aph.gov.au/api/hansard/link/?id={path_prefix}/{hansard_id}/toc&linktype=xml&fulltranscript=True"
    xml_content, error = fetch_with_retry(url)
    if error:
        return None, error

    return parse_hansard_xml_regex(xml_content, chamber_type), None


def scrape_hansard_ids():
    url = "https://www.aph.gov.au/News_and_Events/Watch_Read_Listen"
    html, error = fetch_with_retry(url)
    if error:
        return [], error

    results = []
    for match in re.findall(r'chamber/hansardr/(\d+)', html):
        idx = html.find(f'chamber/hansardr/{match}')
        context = html[max(0, idx-400):idx+150] if idx >= 0 else ""
        date_str = extract_date(context)
        results.append({"id": match, "chamber": "House of Representatives", "date": date_str})

    for match in re.findall(r'chamber/hansards/(\d+)', html):
        idx = html.find(f'chamber/hansards/{match}')
        context = html[max(0, idx-400):idx+150] if idx >= 0 else ""
        date_str = extract_date(context)
        results.append({"id": match, "chamber": "Senate", "date": date_str})

    seen = set()
    unique = []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)
    return unique, None


def extract_date(context):
    for pat in [r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})', r'(\d{4}-\d{2}-\d{2})']:
        m = re.search(pat, context)
        if m:
            return m.group(1)
    return "Recent"


def llm_summarize(transcript_data, retries=2):
    """Generate a plain-English summary of a Hansard transcript using MiniMax LLM."""
    api_key = get_minimax_key()
    if not api_key:
        print("  No MiniMax API key found")
        return None

    date = transcript_data.get("date", "Unknown date")
    chamber = transcript_data.get("chamber", "Unknown")
    questions = transcript_data.get("questions", [])
    top_issues = transcript_data.get("top_issues", [])

    # Format Q&A for the prompt
    qa_lines = []
    for i, q in enumerate(questions[:10], 1):
        asker = q.get("asker", "Unknown").split('(')[0].strip()
        question = q.get("question", "")[:300]
        answer = q.get("answer", "")[:200] if q.get("answer") else ""
        qa_lines.append(f"Q{i}: [{asker}] {question}")
        if answer:
            qa_lines.append(f"   A: {answer}")

    qa_section = "\n".join(qa_lines) if qa_lines else "None recorded."
    issues_section = "\n".join([f"• {t[:100]}" for t in top_issues[:12]]) if top_issues else "Not available."

    prompt = f"""You are summarizing Australian Parliament Hansard transcripts for a Discord audience.

CHARACTER LIMIT: Your entire response must be under 1900 characters (Discord embed limit).

CHAMBER: {chamber}
DATE: {date}

TOP ISSUES DEBATED:
{issues_section}

QUESTION TIME — KEY EXCHANGES:
{qa_section}

Based on the above, write a concise plain-English summary (no markdown, no bullet points, no preamble like "Here's a summary") covering:
1. The main issues debated and any major announcements
2. The most significant question-and-answer exchanges
3. Notable political exchanges or developments

Your response should be 120-180 words of clear prose. Start directly with the content."""


    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": "MiniMax-M2.7",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.3,
    }

    for attempt in range(retries):
        req = urllib.request.Request(
            MINIMAX_API_URL,
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read())
                content = result.get("content", [])
                # content is a list of blocks; find the text block
                text = ""
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        break
                if text and len(text.strip()) > 50:
                    return text
                print(f"  LLM returned empty/short response, attempt {attempt+1}")
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            print(f"  LLM HTTP error {e.code}: {body}, attempt {attempt+1}")
        except Exception as e:
            print(f"  LLM error: {e}, attempt {attempt+1}")
        if attempt < retries - 1:
            time.sleep(5)

    return None


def post_discord(message):
    if len(message) > 2000:
        message = message[:1997] + "..."

    token = get_discord_token()
    if not token:
        print("  No Discord token found")
        return False

    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    data = json.dumps({"content": message}).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "Hermes-Bot/1.0"
    }, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            result = json.loads(resp.read())
            print(f"  Posted Discord message ID: {result.get('id')}")
            return True
    except urllib.error.HTTPError as e:
        print(f"  Discord error {e.code}: {e.read().decode()[:200]}")
        return False


def build_discord_message(transcript_summary):
    chamber = transcript_summary.get("chamber", "")
    date = transcript_summary.get("date", "")
    summary = transcript_summary.get("summary", "")
    questions = transcript_summary.get("questions", [])

    icon = "🏛️" if chamber == "House of Representatives" else "⚖️"

    lines = [
        f"**📜 {chamber} — {date}**\n",
        summary,
    ]

    if questions:
        lines.append("\n**Key Questions:**")
        for q in questions[:4]:
            asker = q.get("asker", "Unknown").split('(')[0].strip()
            question = q.get("question", "")[:120]
            lines.append(f"• **{asker}:** {question}...")

    return "\n".join(lines)


def main():
    state = get_state()
    seen_ids = set(state.get("seen_ids", []))

    ids_data, error = scrape_hansard_ids()
    if error:
        print(f"APH Hansard scrape failed: {error}")
        return

    new_entries = [e for e in ids_data if e["id"] not in seen_ids]

    if not new_entries:
        print(f"No new transcripts (checked {len(ids_data)} total)")
        return

    print(f"Found {len(new_entries)} new transcript(s): {[e['id'] for e in new_entries]}")

    posted_count = 0

    for entry in new_entries[:6]:
        hansard_id = entry["id"]
        chamber = entry["chamber"]

        print(f"\nProcessing {chamber} {hansard_id} ({entry.get('date', 'unknown')})...")
        transcript, err = fetch_and_parse_transcript(hansard_id, chamber)
        if err:
            print(f"  Error: {err}")
            continue
        if not transcript:
            print("  No transcript data")
            continue

        n_q = transcript.get("total_questions", 0)
        n_qa = len(transcript.get("questions", []))
        print(f"  -> {n_q} total questions, {n_qa} Q&A pairs extracted")
        print(f"  -> Top issues: {', '.join(transcript.get('top_issues', [])[:5])[:100]}")

        print("  Generating LLM summary...")
        summary_text = llm_summarize(transcript)

        if summary_text:
            msg = build_discord_message({
                "chamber": chamber,
                "date": entry.get("date", transcript.get("date", "Unknown")),
                "summary": summary_text,
                "questions": transcript.get("questions", []),
            })
            if post_discord(msg):
                posted_count += 1
                seen_ids.add(hansard_id)
        else:
            print("  Failed to generate summary, skipping Discord post")

    if posted_count:
        state["seen_ids"] = list(seen_ids)[-50:]
        state["last_run"] = datetime.now().isoformat()
        save_state(state)
        print(f"\nDone. Posted {posted_count} summary(ies) to Discord.")
    else:
        print("\nNo summaries were posted.")


if __name__ == "__main__":
    main()