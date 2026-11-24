#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="${GDMP_KNOWLEDGE_HOME:-$ROOT/.installed}"
VER="$(cat "$ROOT/VERSION")"
DEST="$HOME_DIR/$VER"
[ -f "$DEST/SKILL.md" ] || { echo "NOT INSTALLED"; exit 1; }
cmp -s "$DEST/SKILL.md" "$ROOT/SKILL.md" && echo "content: OK" || { echo "content mismatch"; exit 1; }
python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));print("registry:",d["name"],d["version"],"ai_execution:",d["ai_execution"])' "$HOME_DIR/install-registry.json"
