#!/usr/bin/env python3
"""Validate the unchanged legacy CSV and separate Rust identity inventory."""

import csv
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
MAIN_HEADERS = ["country", "flag", "map", "region code", "ISO", "tags"]
ID_HEADERS = ["country", "stable_id", "flag_media_id", "map_media_id"]
MAIN_SHA256 = "c1688b7f47950f6ab83425e58543b16f1a161c65461a7bb680cd09acc0a7e1c2"
IMAGE_TAG = re.compile(r'<img src="([^"<>\r\n]+)" />')
STABLE_ID = re.compile(r"note\.[a-z0-9.-]+")


def read_csv(path, headers):
    lines = path.read_bytes().splitlines(keepends=True)
    if len(lines) != 324 or any(not line.endswith(b"\n") for line in lines):
        raise ValueError(f"{path.name} must have exactly 324 LF-terminated lines")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, strict=True))
    if not rows or list(rows[0]) != headers:
        raise ValueError(f"unexpected {path.name} headers")
    if len(rows) != 323:
        raise ValueError(f"expected 323 {path.name} rows, found {len(rows)}")
    return rows


def image_names(value, row_number):
    matches = list(IMAGE_TAG.finditer(value))
    if "".join(match.group(0) for match in matches) != value:
        raise ValueError(f"row {row_number} has non-canonical image HTML")
    return [match.group(1) for match in matches]


def flag_id(filename):
    match = re.fullmatch(r"ug-flag-([a-z0-9_-]+?)(-blur)?\.svg", filename)
    if not match:
        raise ValueError(f"invalid flag filename {filename!r}")
    media_id = f"media.flag.{match.group(1).replace('_', '-')}"
    return media_id + (".blur" if match.group(2) else "")


def map_id(filename):
    match = re.fullmatch(r"ug-map-([a-z0-9_-]+)\.png", filename)
    if not match:
        raise ValueError(f"invalid map filename {filename!r}")
    return f"media.map.{match.group(1).replace('_', '-')}"


def validate(
    main_path=ROOT / "src/data/main.csv",
    ids_path=ROOT / "src/data/ids.csv",
):
    if hashlib.sha256(main_path.read_bytes()).hexdigest() != MAIN_SHA256:
        raise ValueError("main.csv differs from the legacy source")
    main_rows = read_csv(main_path, MAIN_HEADERS)
    id_rows = read_csv(ids_path, ID_HEADERS)
    if [row["country"] for row in main_rows] != [row["country"] for row in id_rows]:
        raise ValueError("ids.csv country inventory differs from main.csv")

    stable_ids = [row["stable_id"] for row in id_rows]
    if any(STABLE_ID.fullmatch(value) is None for value in stable_ids):
        raise ValueError("invalid stable ID")
    if len(stable_ids) != len(set(stable_ids)):
        raise ValueError("stable IDs are not unique")

    flag_ids = []
    map_ids = []
    for row_number, (main, identity) in enumerate(zip(main_rows, id_rows), 2):
        flags = image_names(main["flag"], row_number)
        maps = image_names(main["map"], row_number)
        typed_flags = identity["flag_media_id"].split("|") if identity["flag_media_id"] else []
        typed_maps = [identity["map_media_id"]] if identity["map_media_id"] else []
        if typed_flags != [flag_id(filename) for filename in flags]:
            raise ValueError(f"row {row_number} flag media IDs differ from legacy HTML")
        if typed_maps != [map_id(filename) for filename in maps]:
            raise ValueError(f"row {row_number} map media ID differs from legacy HTML")
        flag_ids.extend(typed_flags)
        map_ids.extend(typed_maps)

    all_media_ids = flag_ids + map_ids
    if len(flag_ids) != 227 or len(map_ids) != 323 or len(set(all_media_ids)) != 550:
        raise ValueError("identity media coverage is not exactly 227 flags and 323 maps")
    return len(stable_ids), len(flag_ids), len(map_ids), len(all_media_ids)


if __name__ == "__main__":
    notes, flags, maps, media = validate()
    print(f"Validated {notes} note IDs, {flags} flag references, {maps} maps, and {media} media IDs")
