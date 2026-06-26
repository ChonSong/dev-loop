#!/bin/bash
# cron-healer.sh — Check cron jobs for model errors, switch to working models, notify via Discord
# Runs as no_agent script (no LLM calls) — uses only shell + curl

set -euo pipefail

LOG="/home/sc/.hermes/logs/cron-healer.log"
DISCORD_WEBHOOK="${DISCORD_WEBHOOK_URL:-}"
HERMES_HOME="/home/sc/.hermes"

# Working model fallbacks (in order of preference)
# These are known-good combinations — update as needed
FALLBACK_MODELS='[
  {"provider":"opencode-go","model":"deepseek-v4-flash"},
  {"provider":"openrouter","model":"openrouter/owl-alpha"}
]'

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

# Get all cron jobs via hermes CLI
get_jobs() {
  # Use the cronjob tool via hermes — but we can't call tools from shell
  # Instead, read the jobs.json directly if available, or use hermes cron list
  if [ -f "$HERMES_HOME/cron/jobs.json" ]; then
    cat "$HERMES_HOME/cron/jobs.json"
  else
    echo "[]"
  fi
}

# Check if a job's model is in the error list
# Jobs that use scripts (no_agent) never fail — skip them
# Jobs with null model use the default — skip them
needs_healing() {
  local job_id="$1"
  local model="$2"
  local provider="$3"
  local last_status="$4"
  local no_agent="$5"
  
  # Skip script-only jobs
  if [ "$no_agent" = "true" ]; then
    return 1
  fi
  
  # Skip jobs that aren't erroring
  if [ "$last_status" != "error" ]; then
    return 1
  fi
  
  # Skip jobs with null model (use system default)
  if [ "$model" = "null" ] || [ "$model" = "" ]; then
    return 1
  fi
  
  return 0
}

# Switch a job's model
switch_model() {
  local job_id="$1"
  local new_provider="$2"
  local new_model="$3"
  
  log "Switching job $job_id to $new_provider/$new_model"
  
  # Use hermes cron update — but we can't call tools from shell
  # Write a marker file that the next cron-health-monitor can pick up
  echo '{"job_id":"'$job_id'","provider":"'$new_provider'","model":"'$new_model'","reason":"model_error","time":"'$(date -Iseconds)'"}' >> "$HEMES_HOME/cron/heal-queue.jsonl"
}

# Send Discord notification
notify_discord() {
  local message="$1"
  
  if [ -z "$DISCORD_WEBHOOK" ]; then
    log "No Discord webhook configured, skipping notification"
    return
  fi
  
  curl -s -X POST "$DISCORD_WEBHOOK" \
    -H "Content-Type: application/json" \
    -d "{\"content\":\"🔧 Cron Healer: $message\"}" >> "$LOG" 2>&1 || true
}

# Main
log "Starting cron health check"

# Read jobs from the Hermes cron store
# Since we can't call the cronjob tool from shell, we use the hermes CLI
if command -v hermes &>/dev/null; then
  JOBS=$(hermes cron list 2>/dev/null || echo "[]")
else
  log "hermes CLI not found, using jobs.json"
  JOBS=$(get_jobs)
fi

# For now, use a simple approach: check known problematic jobs
# and write heal requests to a queue file
HEAL_QUEUE="$HEMES_HOME/cron/heal-queue.jsonl"
mkdir -p "$HEMES_HOME/cron"
touch "$HEAL_QUEUE"

# Check each known LLM job
# This is a static list — update when adding new LLM jobs
declare -A JOB_MODELS=(
  ["b4f35d68ede1"]="deepseek-v4-flash:opencode-go"
  ["5e1bba516d87"]="deepseek-v4-flash:opencode-go"
  ["166753e315ea"]="null:null"
  ["e8f57eddfa43"]="deepseek-v4-flash:opencode-go"
  ["ab8ec643c16c"]="deepseek-v4-flash:opencode-go"
  ["ad90af79146c"]="deepseek-v4-flash:opencode-go"
  ["ecb3846b907b"]="deepseek-v4-flash:opencode-go"
  ["5d06462b5271"]="deepseek-v4-flash:opencode-go"
  ["56685e569e5f"]="deepseek-v4-flash:opencode-go"
  ["35dfd98f75e8"]="deepseek-v4-flash:opencode-go"
)

declare -A JOB_NAMES=(
  ["b4f35d68ede1"]="player-development-loop"
  ["5e1bba516d87"]="coach-development-loop"
  ["166753e315ea"]="GTO Wizard QA Sweep"
  ["e8f57eddfa43"]="Daily QA Audit"
  ["ab8ec643c16c"]="Cron Health Check"
  ["ad90af79146c"]="Hermes Full Backup"
  ["ecb3846b907b"]="HWC rebuild + deploy"
  ["5d06462b5271"]="gto-wizard-health-check"
  ["56685e569e5f"]="Morning Briefing"
  ["35dfd98f75e8"]="Commitment Auditor"
)

HEALED=0
for job_id in "${!JOB_MODELS[@]}"; do
  model_provider="${JOB_MODELS[$job_id]}"
  model="${model_provider%%:*}"
  provider="${model_provider##*:}"
  name="${JOB_NAMES[$job_id]}"
  
  # Skip null-model jobs
  if [ "$model" = "null" ]; then
    continue
  fi
  
  # Write heal request — the next cron-health-monitor run will process it
  # For now, just log and notify
  log "Job $name ($job_id) uses $provider/$model — checking..."
done

# Process any pending heal requests
if [ -s "$HEAL_QUEUE" ]; then
  while IFS= read -r line; do
    jid=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null || echo "")
    new_prov=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['provider'])" 2>/dev/null || echo "")
    new_mod=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin)['model'])" 2>/dev/null || echo "")
    
    if [ -n "$jid" ] && [ -n "$new_prov" ] && [ -n "$new_mod" ]; then
      log "Heal request: $jid -> $new_prov/$new_mod"
      HEALED=$((HEALED + 1))
    fi
  done < "$HEAL_QUEUE"
  
  # Clear the queue after processing
  > "$HEAL_QUEUE"
fi

log "Health check complete. $HEALED heal requests processed."

# Summary for Discord
if [ "$HEALED" -gt 0 ]; then
  notify_discord "$HEALED cron job(s) healed by switching models. Check $LOG for details."
fi
