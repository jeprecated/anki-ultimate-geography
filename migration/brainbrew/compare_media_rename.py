#!/usr/bin/env python3
"""Verify the approved ug-flag/ug-map output filename migration."""

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from migration.brainbrew.compare_crowdanki import json_differences, load_target

PREFIXES = (("ug-flag-", "flag-"), ("ug-map-", "map-"))


def renamed_filename(filename):
    for old, new in PREFIXES:
        if filename.startswith(old):
            return new + filename[len(old):]
    return filename


def renamed_deck(deck):
    deck = copy.deepcopy(deck)
    deck["media_files"] = [renamed_filename(name) for name in deck["media_files"]]
    for note in deck["notes"]:
        for index, field in enumerate(note["fields"]):
            for old, new in PREFIXES:
                field = field.replace(f'src="{old}', f'src="{new}')
                field = field.replace(f"src='{old}", f"src='{new}")
            note["fields"][index] = field
    return deck


def compare(before_path, after_path):
    before = load_target(before_path, "before rename")
    after = load_target(after_path, "after rename")

    differences = json_differences(renamed_deck(before["deck"]), after["deck"])
    expected_media = {renamed_filename(name): digest for name, digest in before["media"].items()}
    renamed_count = sum(name != renamed_filename(name) for name in before["media"])
    if renamed_count != 550:
        raise ValueError(f"expected 550 renamed media files, found {renamed_count}")
    if len(expected_media) != len(before["media"]):
        raise ValueError("media rename creates a filename collision")

    missing = sorted(expected_media.keys() - after["media"].keys())
    extra = sorted(after["media"].keys() - expected_media.keys())
    changed = sorted(
        name
        for name in expected_media.keys() & after["media"].keys()
        if expected_media[name] != after["media"][name]
    )
    return differences, missing, extra, changed


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("Usage: compare_media_rename.py BEFORE AFTER", file=sys.stderr)
        return 2
    try:
        differences, missing, extra, changed = compare(Path(argv[0]), Path(argv[1]))
    except (OSError, ValueError) as error:
        print(f"Comparison error: {error}", file=sys.stderr)
        return 2

    if differences or missing or extra or changed:
        for path, before, after in differences[:20]:
            print(f"JSON difference at {path}: {before!r} != {after!r}")
        if missing:
            print(f"Missing media: {', '.join(missing[:20])}")
        if extra:
            print(f"Extra media: {', '.join(extra[:20])}")
        if changed:
            print(f"Changed media bytes: {', '.join(changed[:20])}")
        return 1

    print("Media rename parity: equal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
