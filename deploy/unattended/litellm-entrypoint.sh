#!/bin/sh
set -eu

secret_file=/run/secrets/openai_api_key
if [ ! -f "$secret_file" ]; then
  exit 1
fi

IFS= read -r OPENAI_API_KEY < "$secret_file"
if [ -z "$OPENAI_API_KEY" ]; then
  exit 1
fi
export OPENAI_API_KEY
unset secret_file

exec litellm --config /app/config.yaml --port 4000
