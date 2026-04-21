#!/bin/sh
# =============================================================================
# trigger‑kaggle.sh – Trigger Kaggle Nightly Consolidation
# =============================================================================
# Calls the Kaggle API to start the nightly notebook execution.
# Designed for cron‑job.org (recommended: daily at 19:30 UTC = 1:00 AM IST).
# =============================================================================

KAGGLE_USERNAME="${KAGGLE_USERNAME:-}"
KAGGLE_KEY="${KAGGLE_KEY:-}"
NOTEBOOK_SLUG="${NOTEBOOK_SLUG:-revarie-nightly-consolidation}"

if [ -z "$KAGGLE_USERNAME" ] || [ -z "$KAGGLE_KEY" ]; then
    echo "[$(date)] ERROR: Kaggle credentials not set"
    exit 1
fi

# Trigger notebook via Kaggle API
RESPONSE=$(curl -s -X POST \
    -u "${KAGGLE_USERNAME}:${KAGGLE_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"slug\":\"${NOTEBOOK_SLUG}\",\"newTitle\":\"Revarie Nightly $(date +%Y-%m-%d)\"}" \
    "https://www.kaggle.com/api/v1/kernels/push")

if echo "$RESPONSE" | grep -q "ref"; then
    echo "[$(date)] Kaggle notebook triggered successfully"
    exit 0
else
    echo "[$(date)] Kaggle trigger failed: $RESPONSE"
    exit 1
fi
