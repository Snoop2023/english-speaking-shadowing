#!/usr/bin/env bash
# One-shot install: download + transcode -> import into Photos -> build albums.
# Run from anywhere: bash scripts/install.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This only works on macOS (it drives Photos via AppleScript)." >&2
  exit 1
fi

for bin in python3 ffmpeg ffprobe yt-dlp; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "missing $bin — run: brew install yt-dlp ffmpeg" >&2
    exit 1
  fi
done

echo "== 1/2 download + transcode (~198 clips, several seconds apart on purpose)"
python3 scripts/download.py "$@"

echo "== 2/2 import into Photos and build albums"
python3 scripts/photos.py
