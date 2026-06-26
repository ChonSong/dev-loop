#!/bin/bash
export HOME=/home/sean
export PATH=/usr/local/bin:/usr/bin:/bin
export HERMES_HOME=/home/sean/.hermes

# Fix permissions — container writes as root, sync runs as sean
chmod -R a+rX \
  $HERMES_HOME/sessions \
  $HERMES_HOME/skills \
  $HERMES_HOME/memory \
  $HERMES_HOME/memories \
  $HERMES_HOME/cron \
  $HERMES_HOME/workspace \
  $HERMES_HOME/hooks \
  $HERMES_HOME/plans \
  $HERMES_HOME/hermes-agent \
  $HERMES_HOME/cache \
  $HERMES_HOME/scripts 2>/dev/null

/usr/bin/python3 $HERMES_HOME/scripts/hermes-sync-backup.py >> $HERMES_HOME/logs/sync-backup.log 2>&1
