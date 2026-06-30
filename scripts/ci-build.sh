#!/bin/bash
# DuckBotOS CI Build Entry Point
# Called by GitHub Actions as: sudo bash scripts/ci-build.sh
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
CX_DISTRO="$REPO_ROOT/cx-distro"
DUCKBOTOS_MODE="${DUCKBOTOS_MODE:-hermes}"

echo "[CI] Mode: $DUCKBOTOS_MODE"
echo "[CI] Repo: $REPO_ROOT"
echo "[CI] cx-distro: $CX_DISTRO"

cd "$CX_DISTRO"

echo "[CI] Making scripts executable..."
chmod +x src/build.sh
chmod +x src/mods/install_all_mods.sh
chmod +x scripts/*.sh
chmod +x scripts/install-deps.sh

echo "[CI] Setting build mode..."
python3 scripts/set-mode.py "$DUCKBOTOS_MODE"

echo "[CI] Running ISO build..."
./src/build.sh

echo "[CI] Build done. ISO files:"
find . -name "*.iso" -type f 2>/dev/null | head -5
