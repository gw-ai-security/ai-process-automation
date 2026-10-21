#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
: "${WEBHOOK_HMAC_SECRET:?Set WEBHOOK_HMAC_SECRET or create .env}"

echo "Running valid lead flow"
bash scripts/curl_valid.sh

echo "Checking idempotency (repeat)"
bash scripts/curl_valid.sh

echo "Simulating bad signature"
bash scripts/curl_bad_sig.sh

echo "Simulating replay (old timestamp)"
bash scripts/curl_replay.sh

echo "Sending malformed payload"
bash scripts/curl_invalid_payload.sh
