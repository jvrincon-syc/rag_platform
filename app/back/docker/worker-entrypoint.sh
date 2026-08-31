#!/bin/sh
set -eu

interval="${CHATBOT_RUNTIME_WARM_INTERVAL_SECONDS:-1800}"
status_file="${CHATBOT_RUNTIME_WARM_STATUS_FILE:-/tmp/chatbot-runtime-worker-ready}"

while true
do
  if python -m chatbot_runtime.warmup
  then
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "$status_file"
  else
    rm -f "$status_file"
  fi

  sleep "$interval"
done
