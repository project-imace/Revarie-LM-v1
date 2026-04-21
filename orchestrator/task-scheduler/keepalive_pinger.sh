#!/bin/sh
# =============================================================================
# keepalive_pinger.sh – Lightweight Hugging Face Space Keepalive
# 
# Designed to be called by cron-job.org or similar free cron services.
# Pings the /health endpoint every 5 minutes to prevent the free Hugging Face
# Space from sleeping after 48 hours of inactivity.
#
# Usage:
#   ./keepalive_pinger.sh [HF_SPACE_URL]
#
# If HF_SPACE_URL is not provided, defaults to the standard Revarie Space.
# =============================================================================

# Default Hugging Face Space URL
HF_SPACE_URL="${1:-https://revarie-lm-v1-engine.hf.space}"

# Health endpoint
HEALTH_URL="${HF_SPACE_URL}/health"

# Maximum time to wait for response (seconds)
TIMEOUT=10

# Log file (optional – comment out to disable logging)
# LOG_FILE="/tmp/revarie-keepalive.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pinging ${HEALTH_URL}"

# Perform the ping using curl or wget
if command -v curl >/dev/null 2>&1; then
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$HEALTH_URL")
    CURL_EXIT=$?
    
    if [ $CURL_EXIT -eq 0 ] && [ "$RESPONSE" = "200" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: HTTP $RESPONSE"
        STATUS="success"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] FAILURE: curl exit $CURL_EXIT, HTTP $RESPONSE"
        STATUS="failure"
    fi
elif command -v wget >/dev/null 2>&1; then
    RESPONSE=$(wget --timeout="$TIMEOUT" --server-response --spider "$HEALTH_URL" 2>&1 | grep "HTTP/" | tail -1 | awk '{print $2}')
    WGET_EXIT=$?
    
    if [ $WGET_EXIT -eq 0 ] && [ "$RESPONSE" = "200" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: HTTP $RESPONSE"
        STATUS="success"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] FAILURE: wget exit $WGET_EXIT, HTTP $RESPONSE"
        STATUS="failure"
    fi
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Neither curl nor wget found"
    STATUS="error"
fi

# Optional: Log to file
if [ -n "$LOG_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $STATUS" >> "$LOG_FILE"
fi

# Exit with appropriate code
if [ "$STATUS" = "success" ]; then
    exit 0
else
    exit 1
fi
