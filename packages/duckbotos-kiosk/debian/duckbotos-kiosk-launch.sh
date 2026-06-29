#!/bin/bash
# duckbotos-kiosk-launch — starts Weston + Chromium in kiosk mode
# Called by the duckbotos-kiosk systemd service
# URL loaded depends on which mode package is installed

set -e

# Determine which agent URL to load
HERMES_URL="http://localhost:9119"
OPENCLAW_URL="http://localhost:18789/plugins/openclawos"
PICKER_URL="http://localhost:8080"

# Default: Hermes (install-time set via symlink)
KIOSK_URL="${HERMES_URL}"

# Override via environment or symlink detection
if [ -L /etc/duckbotos/kiosk-mode ] && [ -e /etc/duckbotos/kiosk-mode ]; then
    KIOSK_URL=$(readlink -f /etc/duckbotos/kiosk-mode)
fi

# Allow override via env var
KIOSK_URL="${DUCKBOTOS_KIOSK_URL:-${KIOSK_URL}}"

# Wayland display
export WAYLAND_DISPLAY=wayland-0

echo "[duckbotos-kiosk] Starting kiosk — URL: $KIOSK_URL"

# Start Weston (kiosk mode, no cursor, no wallpaper)
echo "[duckbotos-kiosk] Starting Weston compositor..."
weston \
    --backend=drm-backend.so \
    --idle-time=0 \
    --shell=kiosk \
    --no-outputs-config \
    --output-mode=1920x1080 \
    --socket=wayland-0 \
    --developers \
    &

WESTON_PID=$!

# Wait for Wayland socket to appear
TIMEOUT=10
COUNTER=0
while [ ! -S "/run/user/0/wayland-0" ] && [ ! -S "$XDG_RUNTIME_DIR/wayland-0" ]; do
    sleep 0.5
    COUNTER=$((COUNTER+1))
    if [ $COUNTER -ge $TIMEOUT ]; then
        echo "[duckbotos-kiosk] ERROR: Weston failed to start"
        kill $WESTON_PID 2>/dev/null || true
        exit 1
    fi
done

echo "[duckbotos-kiosk] Weston running (PID $WESTON_PID)"

# Small delay for compositor to settle
sleep 2

# Find Chromium binary
CHROMIUM_BIN=""
for bin in chromium-browser google-chrome chromium-browser-unstable chromium; do
    if command -v "$bin" >/dev/null 2>&1; then
        CHROMIUM_BIN="$bin"
        break
    fi
done

if [ -z "$CHROMIUM_BIN" ]; then
    echo "[duckbotos-kiosk] ERROR: No Chromium found"
    kill $WESTON_PID 2>/dev/null || true
    exit 1
fi

echo "[duckbotos-kiosk] Using Chromium: $CHROMIUM_BIN"

# Start Chromium in kiosk mode
echo "[duckbotos-kiosk] Launching Chromium kiosk — $KIOSK_URL"
exec "$CHROMIUM_BIN" \
    --kiosk \
    --noerrdialogs \
    --disable-features=Translate,ChromeToDesktopShortcutV2 \
    --disable-extensions \
    --disable-translate \
    --disable-background-networking \
    --disable-sync \
    --disable-default-apps \
    --no-first-run \
    --no-default-browser-check \
    --disable-session-crashed-bubble \
    --disable-logging \
    --silent-debugger-extension-api \
    --window-size=1920,1080 \
    --start-fullscreen \
    --app="$KIOSK_URL" \
    --enable-features=VaapiVideoDecoder,VaapiVideoEncoder,UseOzonePlatform \
    --ozone-platform=wayland \
    2>&1 | while read line; do
        echo "[chromium] $line"
    done