---
name: english-speaking-shadowing
description: Download 198 Instagram English speaking clips into macOS Photos with topic/person albums and an iPhone swipe-through shortcut. Use when the user wants to set up this shadowing library on their Mac.
---

# English speaking shadowing library

Build a shadowing (跟读) library out of 198 public Instagram Reels: download, transcode,
import into macOS Photos, create two album folders, install an iPhone shortcut.

## What the user ends up with

```
Photos
├── 英语素材｜由浅入深｜001–198     198 videos, sorted easy → hard
├── 英语素材｜按话题              17 albums in 2 folder levels
└── 英语素材｜按人物              26 albums
```

A shortcut picks 10 random clips from the main album and quick-looks them, so the user
swipes left/right and repeats out loud.

## Hard rules

1. Only create. Never delete or modify existing photos, albums or folders in Photos.
2. Do not rewrite `notes/` or `data/` — they are the index, not scratch data.
3. Never commit video/audio files or cookie files.

## Steps

1. Confirm `uname -s` is `Darwin`; confirm `brew` exists, otherwise stop and have the user install Homebrew.
2. `brew install yt-dlp ffmpeg` (system `python3` is enough, stdlib only).
3. Tell the user, and wait for confirmation:
   - Chrome must be logged into Instagram (cookies are read from Chrome).
   - The first AppleScript call triggers a macOS prompt "Terminal wants to control Photos" — allow it.
   - Downloads are serial with a 3–5s delay to avoid Instagram rate limits; 198 clips ≈ 30–60 min.
4. `bash scripts/install.sh` (= `download.py` then `photos.py`). Output goes to `~/EnglishShadowing/videos/`.
   Rerunning resumes: finished files are skipped, failures land in `~/EnglishShadowing/failed.csv`.
5. Report the counts printed by `photos.py`: main album 198, 17 topic albums summing 198,
   26 person albums summing 198. If any number is off, paste the full output instead of deleting albums.
6. Install the shortcut on the iPhone: use the iCloud link in the README, or generate locally with
   `python3 shortcut/build_shortcut.py` and open the resulting `.shortcut` file.

## Why the dates matter

Photos always returns album contents sorted by date. Each file is written with
`creation_time = 2026-01-01T00:00:00Z + NNN seconds`, so date order *is* difficulty order.
`photos.py` verifies every item and repairs the date if it drifted. Never rely on add order.

## Known failure modes

- `AppleEvent timed out (-1712)` — too many items in one `add`. Keep batches at 20.
- `delete (every album whose name is …)` → `-10000`, and enumerating a folder after deleting
  inside the same script → `-1728`. Separate deletion from creation; reference nested folders by
  full name path (`folder "1.1 内在系统" of folder "1 与自己相处" of folder "英语素材｜按话题"`).
- `yt-dlp` login required — Chrome is not logged in or Instagram is throttling: change network, retry.
- `shortcuts sign --mode anyone` failing with NSURLErrorDomain 5xx — Apple's signing service;
  retry, then fall back to `--mode people-who-know-me`.
