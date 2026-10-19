#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
export BUILD_CA_BUNDLE="${BUILD_CA_BUNDLE:-${SSL_CERT_FILE:-}}"
if [[ -n "$BUILD_CA_BUNDLE" ]]; then
    [[ -r "$BUILD_CA_BUNDLE" ]] || { echo 'Trusted CA bundle is not readable.' >&2; exit 1; }
    bash scripts/docker.sh compose -f compose.yaml -f compose.ca.yaml --profile app build "$@"
else
    bash scripts/docker.sh compose --profile app build "$@"
fi
