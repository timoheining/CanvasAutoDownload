#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

import requests

BASE = os.environ.get("CANVAS_URL") or sys.exit("CANVAS_URL is not set, e.g. https://canvas.example.edu")
OUT = Path(os.environ.get("CANVAS_OUT", Path.home() / "Documents" / "Canvas"))
CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) if os.name == "nt" else Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
TOKEN_FILE = Path(os.environ.get("CANVAS_TOKEN_FILE", CONFIG_DIR / "canvas-auto-download" / "token"))
OTHER = "Other files"

session = requests.Session()
session.headers["Authorization"] = f"Bearer {TOKEN_FILE.read_text().strip()}"


def get_json(url, params=None):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403, 404):
        return None
    r.raise_for_status()
    return r


def pages(url, params=None):
    while url:
        r = get_json(url, params)
        if r is None:
            return
        yield from r.json()
        url = r.links.get("next", {}).get("url")
        params = None


def safe(name):
    return re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .") or "_"


def fetch(file, path):
    if file.get("locked_for_user") or not file.get("url"):
        return 0
    if path.exists() and path.stat().st_size == file["size"]:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    try:
        with session.get(file["url"], stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(tmp, "wb") as fh:
                for chunk in r.iter_content(1 << 16):
                    fh.write(chunk)
    except requests.RequestException as e:
        print(f"  failed: {path.name}: {e}", file=sys.stderr)
        tmp.unlink(missing_ok=True)
        return 0
    tmp.replace(path)
    print(f"  new: {path.relative_to(OUT)}")
    return 1


def sync_course(course):
    cid = course["id"]
    course_dir = OUT / safe(course["name"])
    new = 0
    seen = set()

    for module in pages(f"{BASE}/api/v1/courses/{cid}/modules", {"per_page": 100}):
        module_dir = course_dir / safe(module["name"])
        for item in pages(module["items_url"], {"per_page": 100}):
            if item["type"] != "File":
                continue
            r = get_json(f"{BASE}/api/v1/courses/{cid}/files/{item['content_id']}")
            if r is None:
                continue
            file = r.json()
            seen.add(file["id"])
            new += fetch(file, module_dir / safe(file["display_name"]))

    folders = {
        f["id"]: f["full_name"]
        for f in pages(f"{BASE}/api/v1/courses/{cid}/folders", {"per_page": 100})
    }
    for file in pages(f"{BASE}/api/v1/courses/{cid}/files", {"per_page": 100}):
        if file["id"] in seen:
            continue
        parts = folders.get(file["folder_id"], "course files").split("/")[1:]
        path = course_dir.joinpath(OTHER, *map(safe, parts), safe(file["display_name"]))
        new += fetch(file, path)
    return new


def main():
    total = 0
    for course in pages(f"{BASE}/api/v1/users/self/favorites/courses", {"per_page": 100}):
        if "name" not in course:
            continue
        print(course["name"])
        total += sync_course(course)
    print(f"Done, {total} new file(s)")


if __name__ == "__main__":
    main()
