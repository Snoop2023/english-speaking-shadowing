#!/usr/bin/env python3
"""Download the practice clips from Instagram and transcode them into
Photo-library friendly H.264 files.

Reads data/index.json, writes into ~/EnglishShadowing/videos/.

Each output file is named  NNN｜title｜IG_ID.mp4  and carries a creation_time of
2026-01-01T00:00:00Z + NNN seconds, which is 2026-01-01 08:00:00 +08:00 + NNN
seconds. Photos sorts by date, so that timestamp *is* the easy-to-hard order:
do not change it or the albums will come out shuffled.

Usage:
    python3 scripts/download.py                 # all clips
    python3 scripts/download.py --limit 3       # first 3 (test)
    python3 scripts/download.py --from-local ~/path/to/01_videos_compatible
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "index.json"
HOME = Path.home() / "EnglishShadowing"
RAW = HOME / "raw"
VIDEOS = HOME / "videos"
FAILED = HOME / "failed.csv"

BASE_DATETIME = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def creation_time(no: int) -> str:
    return (BASE_DATETIME + timedelta(seconds=no)).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_name(text: str) -> str:
    for bad, good in (("/", "／"), (":", "：")):
        text = text.replace(bad, good)
    return text.strip()


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def probe(path: Path) -> dict:
    result = run(["ffprobe", "-v", "error", "-print_format", "json",
                  "-show_streams", "-show_format", str(path)])
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return {}


def is_compatible(path: Path) -> bool:
    if not path.exists() or path.stat().st_size <= 1024:
        return False
    data = probe(path)
    videos = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
    if not videos:
        return False
    return videos[0].get("codec_name") == "h264" and videos[0].get("pix_fmt") == "yuv420p"


def transcode(src: Path, dst: Path, no: int) -> tuple[bool, str]:
    """H.264 + AAC + faststart. `-map 0:a?` keeps the 6 silent source clips working."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp.mp4")
    if tmp.exists():
        tmp.unlink()
    cmd = [
        "ffmpeg", "-hide_banner", "-y", "-nostdin", "-loglevel", "error",
        "-i", str(src),
        "-map", "0:v:0", "-map", "0:a?",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-profile:v", "high", "-level", "4.1", "-tag:v", "avc1",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-metadata", f"creation_time={creation_time(no)}",
        "-threads", "2",
        str(tmp),
    ]
    result = run(cmd)
    if result.returncode == 0 and is_compatible(tmp):
        tmp.replace(dst)
        return True, ""
    if tmp.exists():
        tmp.unlink()
    return False, (result.stderr or "").strip()[-800:]


def download(url: str, ig: str) -> tuple[Path | None, str]:
    RAW.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp",
        "--cookies-from-browser", "chrome",
        "--no-playlist", "--quiet", "--no-warnings",
        "-f", "bv*+ba/b",
        "-o", str(RAW / "%(id)s.%(ext)s"),
        url,
    ]
    result = run(cmd)
    if result.returncode != 0:
        return None, (result.stderr or "").strip()[-800:] or "yt-dlp failed"
    hits = sorted(RAW.glob(f"{ig}.*"))
    if not hits:
        hits = sorted(RAW.glob("*"))
    if not hits:
        return None, "downloaded but no file found in raw/"
    return hits[0], ""


def load_index() -> list[dict]:
    if not INDEX.exists():
        sys.exit(f"missing {INDEX}")
    return json.loads(INDEX.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Download + transcode Instagram shadowing clips")
    ap.add_argument("--limit", type=int, help="only handle the first N entries (testing)")
    ap.add_argument("--from-local", type=Path,
                    help="skip downloading; read <IG_ID>/<IG_ID>.mp4 from this directory")
    ap.add_argument("--delay", type=float, default=3.0,
                    help="base delay between downloads in seconds (3-5s used by default)")
    args = ap.parse_args()

    items = load_index()
    if args.limit:
        items = items[: args.limit]

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"missing {tool} — run: brew install ffmpeg")
    if not args.from_local and not shutil.which("yt-dlp"):
        sys.exit("missing yt-dlp — run: brew install yt-dlp")

    VIDEOS.mkdir(parents=True, exist_ok=True)
    failures: list[dict] = []
    done = skipped = 0

    for i, item in enumerate(items, 1):
        no, ig, title = item["no"], item["ig"], safe_name(item["title"])
        dst = VIDEOS / f"{no:03d}｜{title}｜{ig}.mp4"
        tag = f"[{i}/{len(items)}] {no:03d} {ig}"

        if dst.exists() and dst.stat().st_size > 1024:
            skipped += 1
            print(f"{tag} skip (exists)", flush=True)
            continue

        if args.from_local:
            src = Path(args.from_local).expanduser() / ig / f"{ig}.mp4"
            if not src.exists():
                candidates = list((Path(args.from_local).expanduser() / ig).glob("*.mp4"))
                src = candidates[0] if candidates else src
            if not src.exists():
                failures.append({"no": no, "ig": ig, "reason": f"missing local file {src}"})
                print(f"{tag} FAIL missing local file", flush=True)
                continue
        else:
            src, err = download(item["url"], ig)
            if src is None:
                failures.append({"no": no, "ig": ig, "reason": err})
                print(f"{tag} FAIL download: {err.splitlines()[-1] if err else ''}", flush=True)
                time.sleep(random.uniform(args.delay, args.delay + 2))
                continue
            time.sleep(random.uniform(args.delay, args.delay + 2))

        ok, err = transcode(src, dst, no)
        if ok:
            done += 1
            print(f"{tag} ok -> {dst.name}", flush=True)
        else:
            failures.append({"no": no, "ig": ig, "reason": err})
            print(f"{tag} FAIL transcode: {err.splitlines()[-1] if err else ''}", flush=True)

        if not args.from_local and src and src.exists():
            src.unlink()

    if not args.from_local:
        shutil.rmtree(RAW, ignore_errors=True)

    if failures:
        with FAILED.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["no", "ig", "reason"])
            w.writeheader()
            w.writerows(failures)

    print(f"\nconverted={done} skipped={skipped} failed={len(failures)} total={len(items)}")
    print(f"videos={VIDEOS}")
    if failures:
        print(f"failed list: {FAILED} (rerun the script to retry — finished files are skipped)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
