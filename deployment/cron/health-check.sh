#!/bin/sh
# =============================================================================
# health‑check.sh – Full System Health Check
# =============================================================================
# Verifies all critical endpoints are responding.
# =============================================================================

HF_URL="${HF_SPACE_URL:-https://revarie-lm-v1-engine.hf.space}"
VERCEL_URL="${VERCEL_URL:-https://revarie.imace.online}"

FAILURES=0

# Check HF Space
if curl -sf --max-time 10 "${HF_URL}/health" > /dev/null; then
    echo "[OK] HF Space"
else
    echo "[FAIL] HF Space"
    FAILURES=$((FAILURES + 1))
fi

# Check Vercel frontend
if curl -sf --max-time 10 "${VERCEL_URL}" > /dev/null; then
    echo "[OK] Vercel"
else
    echo "[FAIL] Vercel"
    FAILURES=$((FAILURES + 1))
fi

if [ $FAILURES -eq 0 ]; then
    echo "All systems operational"
    exit 0
else
    echo "$FAILURES failure(s) detected"
    exit 1
fi
