#!/usr/bin/env bash
# gdmp-master 版本化知识包安装（不注册 AI 运行时）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="${GDMP_KNOWLEDGE_HOME:-$ROOT/.installed}"
VER="$(cat "$ROOT/VERSION")"
DEST="$HOME_DIR/$VER"
[ -f "$ROOT/dist/SHA256SUMS" ] || { echo "缺少 dist/SHA256SUMS，请先打包"; exit 1; }
(cd "$ROOT/dist" && sha256sum -c SHA256SUMS) || { echo "校验失败"; exit 1; }
mkdir -p "$DEST"
cp -R "$ROOT/references" "$ROOT/runbooks" "$ROOT/audit" "$ROOT/SKILL.md" "$ROOT/manifest.yaml" "$DEST/"
printf '{"name":"gdmp-master","version":"%s","installed_at":"%s","path":"%s","ai_execution":"not_enabled"}\n' \
  "$VER" "$(date -Is)" "$DEST" > "$HOME_DIR/install-registry.json"
echo "installed knowledge package: $DEST"
