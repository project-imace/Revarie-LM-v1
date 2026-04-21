#!/bin/sh
# =============================================================================
# keepalive‑hf.sh – Hugging Face Space Keepalive Ping
# =============================================================================
# Prevents free Hugging Face Spaces from sleeping after 48h inactivity.
# Designed for cron‑job.org (recommended interval: 5 minutes).
# =============================================================================

HF_SPACE_URL="${HF_SPACE_URL:-https://revarie-lm-v1-engine.hf.space}"
HEALTH_URL="${HF_SPACE_URL}/health"

if command -v curl >/dev/null 2>&1; then
    curl -s -f --max-time 10 "$HEALTH_URL" > /dev/null
    if [ $? -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] HF Space ping SUCCESS"
        exit 0
    fi
elif command -v wget >/dev/null 2>&1; then
    wget -q --timeout=10 --spider "$HEALTH_URL"
    if [ $? -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] HF Space ping SUCCESS"
        exit 0
    fi
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] HF Space ping FAILED"
exit 1
