#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
# Keep Docker's existing authentication/context; relocate only buildx's writable state.
export BUILDX_CONFIG="${BUILDX_CONFIG:-${TMPDIR:-/tmp}/sec-research-buildx}"
exec docker "$@"
