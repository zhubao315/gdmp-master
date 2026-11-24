#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="${GDMP_KNOWLEDGE_HOME:-$ROOT/.installed}"
VER="$(cat "$ROOT/VERSION")"
rm -rf "$HOME_DIR/$VER"
rm -f "$HOME_DIR/install-registry.json"
echo "removed knowledge package $VER (AI runtime was never enabled)"
