#!/bin/sh
set -eu

: "${TEMPORAL_ADDRESS:?TEMPORAL_ADDRESS is required}"

if temporal operator namespace describe --namespace default >/dev/null 2>&1; then
    exit 0
fi

if ! temporal operator namespace create --namespace default; then
    temporal operator namespace describe --namespace default >/dev/null
fi

temporal operator namespace describe --namespace default >/dev/null
