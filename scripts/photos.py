#!/usr/bin/env python3
"""Import the transcoded clips into Photos and rebuild the two album folders.

Result (identical to the reference library):

    英语素材｜由浅入深｜001–198                (one album, 198 videos)
    英语素材｜按话题
      1 与自己相处 / 1.1 内在系统 / 1.1.1 面对恐惧（9） ...
      2 与他人相处 / 2.1 人际关系 / ...
      3 与世界交手（21）, 4 附属（11）
    英语素材｜按人物
      Chris Williamson（7） ... 其他人物·各1条（125）

Ordering comes from each file's creation_time (2026-01-01T00:00:00Z + no
seconds), because Photos always returns album contents sorted by date.

Safety: nothing is ever deleted or edited in place. If either target folder
already exists the script stops and leaves the decision to you.

Usage:
    python3 scripts/photos.py                 # import + build
    python3 scripts/photos.py --check-only    # report what Photos has now
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "index.json"
ALBUMS = ROOT / "data" / "albums.json"
HOME = Path.home() / "EnglishShadowing"
VIDEOS = HOME / "videos"

MAIN_ALBUM = "英语素材｜由浅入深｜001–198"
TOPIC_FOLDER = "英语素材｜按话题"
PERSON_FOLDER = "英语素材｜按人物"
EPOCH_2026 = 1767225600          # 2026-01-01T00:00:00Z
IMPORT_BATCH = 20
ADD_BATCH = 20

EPOCH_HANDLER = '''on epochBase()
	set e to current date
	set day of e to 1
	set month of e to January
	set year of e to 1970
	set hours of e to 0
	set minutes of e to 0
	set seconds of e to 0
	return e
end epochBase

on epochOf(theDate)
	return (theDate - (my epochBase()))
end epochOf
'''


def as_str(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def run_osascript(script: str, what: str) -> str:
    result = subprocess.run(["osascript", "-"], input=script, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        err = (result.stderr or "").strip()
        sys.exit(f"[{what}] AppleScript failed ({result.returncode}): {err}")
    return result.stdout.strip()


def album_ref(album: str, folder_path: list[str]) -> str:
    if not folder_path:
        return f"album {as_str(album)}"
    chain = " of ".join(f"folder {as_str(f)}" for f in reversed(folder_path))
    return f"album {as_str(album)} of {chain}"


def folder_ref(folder_path: list[str]) -> str:
    chain = " of ".join(f"folder {as_str(f)}" for f in reversed(folder_path[:-1]))
    return f"folder {as_str(folder_path[-1])}" + (f" of {chain}" if chain else "")


def load():
    items = json.loads(INDEX.read_text(encoding="utf-8"))
    albums = json.loads(ALBUMS.read_text(encoding="utf-8"))
    return items, albums


def video_path(it: dict) -> Path:
    return VIDEOS / f"{it['no']:03d}｜{it['title']}｜{it['ig']}.mp4"


def check_videos(items) -> None:
    missing = [video_path(it).name for it in items if not video_path(it).exists()]
    if missing:
        print(f"missing {len(missing)} of {len(items)} video files in {VIDEOS}:")
        for m in missing[:10]:
            print("  ", m)
        if len(missing) > 10:
            print(f"   ... {len(missing) - 10} more")
        sys.exit("run scripts/download.py first")


def state() -> dict:
    """Read-only snapshot of what already exists (writes nothing)."""
    script = f'''
tell application "Photos"
	set out to ""
	try
		set a to album {as_str(MAIN_ALBUM)}
		set out to out & "main_album|" & (count of media items of a) & linefeed
	end try
	try
		set f to folder {as_str(TOPIC_FOLDER)}
		set out to out & "topic_folder|1" & linefeed
	end try
	try
		set f to folder {as_str(PERSON_FOLDER)}
		set out to out & "person_folder|1" & linefeed
	end try
	return out
end tell
'''
    raw = run_osascript(script, "state")
    st = {}
    for line in raw.splitlines():
        if "|" in line:
            k, v = line.split("|", 1)
            st[k] = v
    return st


def create_main_album() -> None:
    script = f'''
tell application "Photos"
	with timeout of 900 seconds
		if not (exists album {as_str(MAIN_ALBUM)}) then
			make new album named {as_str(MAIN_ALBUM)}
		end if
	end timeout
end tell
'''
    run_osascript(script, "create album")


def import_batches(files: list[Path]) -> None:
    total = len(files)
    for start in range(0, total, IMPORT_BATCH):
        chunk = files[start:start + IMPORT_BATCH]
        refs = ", ".join(f"POSIX file {as_str(str(p))}" for p in chunk)
        script = f'''
tell application "Photos"
	with timeout of 1800 seconds
		import {{{refs}}} into album {as_str(MAIN_ALBUM)} skip check duplicates true
	end timeout
end tell
'''
        print(f"  import {start + 1}-{start + len(chunk)} / {total}", flush=True)
        run_osascript(script, "import")


def check_dates() -> tuple[int, int]:
    """The date drives the sort order, so verify every item and repair on mismatch.

    Each filename starts with the three-digit order number, so the expected date
    is fully recoverable from the photo library itself.
    """
    script = f'''
{EPOCH_HANDLER}
tell application "Photos"
	with timeout of 1800 seconds
		set a to album {as_str(MAIN_ALBUM)}
		set e to my epochBase()
		set checked to 0
		set fixedCount to 0
		repeat with mi in (media items of a)
			set n to filename of mi
			set want to {EPOCH_2026} + ((text 1 thru 3 of n) as integer)
			set checked to checked + 1
			set got to (date of mi) - e
			if (got - want) > 2 or (want - got) > 2 then
				set date of mi to (e + want)
				set fixedCount to fixedCount + 1
			end if
		end repeat
		return (checked as text) & "|" & (fixedCount as text)
	end timeout
end tell
'''
    raw = run_osascript(script, "check dates")
    checked, fixed = (raw.split("|") + ["0", "0"])[:2]
    return int(checked or 0), int(fixed or 0)


def main_album_order() -> list[str]:
    """Filenames in the order Photos returns them (date order)."""
    script = f'''
tell application "Photos"
	with timeout of 600 seconds
		set out to ""
		repeat with mi in (media items of album {as_str(MAIN_ALBUM)})
			set out to out & (filename of mi) & linefeed
		end repeat
		return out
	end timeout
end tell
'''
    raw = run_osascript(script, "read order")
    igs = []
    for line in raw.splitlines():
        name = line.strip()
        if not name:
            continue
        igs.append(name.rsplit("｜", 1)[-1].rsplit(".", 1)[0])
    return igs


def build_structure(albums) -> list[tuple[str, list[str]]]:
    """Create the folder/album tree. Returns [(album_ref, igs)] for the add phase."""
    plan: list[tuple[str, list[str]]] = []

    def make_folder(path: list[str]) -> None:
        parent = " at " + " of ".join(f"folder {as_str(f)}" for f in reversed(path[:-1])) if len(path) > 1 else ""
        script = f'''
tell application "Photos"
	with timeout of 600 seconds
		if not (exists {folder_ref(path)}) then
			make new folder named {as_str(path[-1])}{parent}
		end if
	end timeout
end tell
'''
        run_osascript(script, "make folder")

    def make_album(name: str, path: list[str]) -> None:
        parent = " of ".join(f"folder {as_str(f)}" for f in reversed(path))
        script = f'''
tell application "Photos"
	with timeout of 600 seconds
		if not (exists {album_ref(name, path)}) then
			make new album named {as_str(name)} at {parent}
		end if
	end timeout
end tell
'''
        run_osascript(script, "make album")

    make_folder([TOPIC_FOLDER])
    for folder in albums["topic_folders"]:
        make_folder([TOPIC_FOLDER, folder["name"]])
        for sub in folder.get("folders", []):
            make_folder([TOPIC_FOLDER, folder["name"], sub["name"]])
            for alb in sub["albums"]:
                make_album(alb["name"], [TOPIC_FOLDER, folder["name"], sub["name"]])
                plan.append((album_ref(alb["name"], [TOPIC_FOLDER, folder["name"], sub["name"]]), alb["igs"]))
        for alb in folder.get("albums", []):
            make_album(alb["name"], [TOPIC_FOLDER, folder["name"]])
            plan.append((album_ref(alb["name"], [TOPIC_FOLDER, folder["name"]]), alb["igs"]))
    for alb in albums["topic_root_albums"]:
        make_album(alb["name"], [TOPIC_FOLDER])
        plan.append((album_ref(alb["name"], [TOPIC_FOLDER]), alb["igs"]))

    make_folder([PERSON_FOLDER])
    for alb in albums["person_albums"]:
        make_album(alb["name"], [PERSON_FOLDER])
        plan.append((album_ref(alb["name"], [PERSON_FOLDER]), alb["igs"]))
    return plan


def add_items(plan: list[tuple[str, list[str]]], order: list[str]) -> None:
    """`order` is what Photos actually returns for the main album, so index N
    really is the Nth clip on screen."""
    ordinal = {ig: i + 1 for i, ig in enumerate(order)}
    for ref, igs in plan:
        idx = [ordinal[ig] for ig in igs if ig in ordinal]
        name = ref.split('"')[1]
        for start in range(0, len(idx), ADD_BATCH):
            chunk = idx[start:start + ADD_BATCH]
            picks = ", ".join(f"item {i} of allItems" for i in chunk)
            script = f'''
tell application "Photos"
	with timeout of 900 seconds
		set allItems to media items of album {as_str(MAIN_ALBUM)}
		add {{{picks}}} to {ref}
	end timeout
end tell
'''
            print(f"  add {len(chunk)} -> {name}" + (f" ({start + len(chunk)}/{len(idx)})" if len(idx) > ADD_BATCH else ""), flush=True)
            run_osascript(script, "add items")


def verify(albums) -> bool:
    script = f'''
tell application "Photos"
	set out to ""
	set out to out & "MAIN|" & (count of media items of album {as_str(MAIN_ALBUM)}) & linefeed
	set f to folder {as_str(TOPIC_FOLDER)}
	repeat with a in (every album of f)
		set out to out & "TOPIC_ALBUM|" & (name of a) & "|" & (count of media items of a) & linefeed
	end repeat
	repeat with sub in (every folder of f)
		repeat with a in (every album of sub)
			set out to out & "TOPIC_ALBUM|" & (name of a) & "|" & (count of media items of a) & linefeed
		end repeat
		repeat with sub2 in (every folder of sub)
			repeat with a in (every album of sub2)
				set out to out & "TOPIC_ALBUM|" & (name of a) & "|" & (count of media items of a) & linefeed
			end repeat
		end repeat
	end repeat
	set p to folder {as_str(PERSON_FOLDER)}
	repeat with a in (every album of p)
		set out to out & "PERSON_ALBUM|" & (name of a) & "|" & (count of media items of a) & linefeed
	end repeat
	return out
end tell
'''
    raw = run_osascript(script, "verify")
    main_count = topic_total = person_total = 0
    topic_albums = person_albums = 0
    for line in raw.splitlines():
        parts = line.split("|")
        if parts[0] == "MAIN" and len(parts) == 2:
            main_count = int(parts[1])
        elif parts[0] == "TOPIC_ALBUM" and len(parts) == 3:
            topic_total += int(parts[2]); topic_albums += 1
        elif parts[0] == "PERSON_ALBUM" and len(parts) == 3:
            person_total += int(parts[2]); person_albums += 1

    expected_topic = (sum(len(f.get("albums", [])) + sum(len(s["albums"]) for s in f.get("folders", []))
                          for f in albums["topic_folders"])
                      + len(albums["topic_root_albums"]))
    expected_person = len(albums["person_albums"])
    ok = (main_count == 198 and topic_total == 198 and topic_albums == expected_topic
          and person_total == 198 and person_albums == expected_person)
    print(f"\n合集: {main_count} items (expected 198)")
    print(f"按话题: {topic_albums} albums (expected {expected_topic}), {topic_total} items (expected 198)")
    print(f"按人物: {person_albums} albums (expected {expected_person}), {person_total} items (expected 198)")
    print("RESULT:", "OK" if ok else "MISMATCH — see the log above")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Import clips into Photos and build the album tree")
    ap.add_argument("--check-only", action="store_true", help="only report what Photos already has")
    args = ap.parse_args()

    items, albums = load()

    if args.check_only:
        print(state())
        return 0

    check_videos(items)
    st = state()
    if "topic_folder" in st or "person_folder" in st:
        print("These folders already exist in Photos:")
        for k, label in (("topic_folder", TOPIC_FOLDER), ("person_folder", PERSON_FOLDER)):
            if k in st:
                print("  ", label)
        print("Nothing was changed. Delete them yourself if you really want to rebuild, then rerun.")
        return 2

    print(f"1/4 album {MAIN_ALBUM}")
    create_main_album()

    files = [video_path(it) for it in sorted(items, key=lambda x: x["no"])]
    print(f"2/4 importing {len(files)} videos (batches of {IMPORT_BATCH})")
    import_batches(files)

    print("3/4 checking dates (the sort order depends on them)")
    checked, fixed = check_dates()
    print(f"  checked {checked}, repaired {fixed}")

    order = main_album_order()
    if len(order) != 198:
        print(f"  WARNING: album returned {len(order)} items, expected 198")

    print("4/4 building album folders")
    plan = build_structure(albums)
    add_items(plan, order)

    return 0 if verify(albums) else 1


if __name__ == "__main__":
    raise SystemExit(main())
