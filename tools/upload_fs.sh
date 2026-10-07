#!/usr/bin/env bash
# Build a LittleFS image from gateway_esp32/data and flash it to the gateway.
# Layout matches the ESP32 "Default 4MB with spiffs" partition table:
#   spiffs partition at 0x290000, size 0x160000 (LittleFS uses it).
# Usage: tools/upload_fs.sh [/dev/ttyUSB0]
set -euo pipefail

PORT="${1:-/dev/ttyUSB0}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$HOME/.arduino15/packages/esp32/tools"
MKLITTLEFS="$(ls -d "$TOOLS"/mklittlefs/*/mklittlefs | tail -1)"
ESPTOOL="$(ls -d "$TOOLS"/esptool_py/*/esptool | tail -1)"
IMG="$(mktemp -d)/littlefs.bin"

"$MKLITTLEFS" -c "$ROOT/gateway_esp32/data" -p 256 -b 4096 -s 0x160000 "$IMG"
"$ESPTOOL" --chip esp32 --port "$PORT" --baud 921600 write_flash 0x290000 "$IMG"
echo "LittleFS uploaded to $PORT"
