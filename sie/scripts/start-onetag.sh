#!/bin/bash
# Start OneTag Streamlit + Auth Wrapper
set -e

cd /home/sean/workspace/forrest-plan-and-track/streamlit_onetag

# Kill old processes
pkill -f "streamlit run app.py" 2>/dev/null || true
pkill -f "auth_wrapper.py" 2>/dev/null || true
sleep 2

# Start streamlit on internal port 8502
nohup ./venv/bin/streamlit run app.py \
  --server.port 8502 \
  --server.headless true \
  --server.address 127.0.0.1 \
  > /tmp/streamlit-onetag.log 2>&1 &
echo "Streamlit started"

# Wait for streamlit
for i in $(seq 1 15); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8502/ 2>/dev/null || echo "000")
  if [ "$CODE" = "200" ]; then
    echo "Streamlit ready on :8502"
    break
  fi
  echo "Waiting for streamlit... ($i/15) code=$CODE"
  sleep 2
done

# Start auth wrapper on 8501
nohup ./venv/bin/python auth_wrapper.py 8501 \
  > /tmp/auth-wrapper.log 2>&1 &
echo "Auth wrapper started"

sleep 3

# Test
echo "--- No auth (expect 401) ---"
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8501/
echo ""
echo "--- With auth sa:dawnofdarren (expect 200) ---"
curl -s -o /dev/null -w "%{http_code}" -u sa:dawnofdarren http://127.0.0.1:8501/
echo ""
