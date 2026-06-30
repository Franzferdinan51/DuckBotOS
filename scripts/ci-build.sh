#!/bin/bash
# DuckBotOS CI Build Entry Point
# Run by GitHub Actions: sudo ./scripts/ci-build.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
CX_DISTRO="$REPO_ROOT/cx-distro"

DUCKBOTOS_MODE="${DUCKBOTOS_MODE:-hermes}"

echo "[DuckBotOS CI] Mode: $DUCKBOTOS_MODE"
echo "[DuckBotOS CI] Repo root: $REPO_ROOT"
echo "[DuckBotOS CI] cx-distro: $CX_DISTRO"

cd "$CX_DISTRO"

echo "[DuckBotOS CI] Making scripts executable..."
chmod +x src/build.sh
chmod +x src/mods/install_all_mods.sh
chmod +x scripts/*.sh
chmod +x scripts/install-deps.sh

echo "[DuckBotOS CI] Setting build mode..."
sed -i "s/^export DUCKBOTOS_MODE=.*/export DUCKBOTOS_MODE=\"$DUCKBOTOS_MODE\"/" src/args.sh

echo "[DuckBotOS CI] Running ISO build..."
sudo ./src/build.sh

echo "[DuckBotOS CI] Build complete."
find . -name "*.iso" -type f 2>/dev/null | head -5
