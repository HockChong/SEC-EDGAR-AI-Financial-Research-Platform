#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
# Cloud workspaces may have a read-only home directory.
export UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/sec-research-uv-cache}"
export UV_LINK_MODE="${UV_LINK_MODE:-copy}"
exec uv "$@"
