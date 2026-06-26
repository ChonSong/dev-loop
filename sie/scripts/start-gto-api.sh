#!/bin/bash
# Start GTO Wizard API server (uvicorn) via systemd --user
cd /home/sc/repos/gto-wizard-clone
export PYTHONPATH=apps/api
exec uv run uvicorn main:app --host 0.0.0.0 --port 8000
