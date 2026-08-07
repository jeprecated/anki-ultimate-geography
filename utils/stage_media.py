#!/usr/bin/env python3
"""Verify and flatten ordinary flag/map media for Rust Brain Brew."""

import argparse
import hashlib
import re
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = (ROOT / "src/media/flags", ROOT / "src/media/maps")
MANIFEST = ROOT / "media.yaml"
DESTINATION = ROOT / "build/brainbrew-media/standard"
ENTRY = re.compile(
    r"(?m)^(media\.[a-z0-9.-]+):\n  path: ([^\n]+)\n  sha256: ([0-9a-f]{64})$"
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def declarations(path):
    text = path.read_text(encoding="utf-8")
    matches = ENTRY.findall(text)
    if "".join(match.group(0) + "\n" for match in ENTRY.finditer(text)) != text:
        raise ValueError(f"malformed media manifest: {path}")
    by_path = {}
    ids = set()
    for media_id, filename, expected_hash in matches:
        if media_id in ids:
            raise ValueError(f"duplicate media id: {media_id}")
        if filename in by_path:
            raise ValueError(f"duplicate media path: {filename}")
        if Path(filename).name != filename:
            raise ValueError(f"media path is not flat: {filename}")
        ids.add(media_id)
        by_path[filename] = expected_hash
    return by_path


def sources(source_dirs):
    found = {}
    for directory in source_dirs:
        for path in sorted(directory.iterdir()):
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"source is not a regular file: {path}")
            if path.name in found:
                raise ValueError(f"media basename collision: {path.name}")
            found[path.name] = path
    return found


def verify_source(source_dirs, manifest, expected_count=550):
    declared = declarations(manifest)
    found = sources(source_dirs)
    if len(found) != expected_count:
        raise ValueError(f"expected {expected_count} source files, found {len(found)}")
    if declared.keys() != found.keys():
        missing = sorted(declared.keys() - found.keys())
        extra = sorted(found.keys() - declared.keys())
        raise ValueError(f"media set mismatch; missing={missing}, extra={extra}")
    for filename, path in found.items():
        actual = digest(path)
        if actual != declared[filename]:
            raise ValueError(f"media hash mismatch: {path}: {actual}")
    return found


def check(source_dirs, manifest, destination, expected_count=550):
    found = verify_source(source_dirs, manifest, expected_count)
    if not destination.is_dir() or destination.is_symlink():
        raise ValueError(f"staging directory is missing or invalid: {destination}")
    staged = sources((destination,))
    if staged.keys() != found.keys():
        missing = sorted(found.keys() - staged.keys())
        extra = sorted(staged.keys() - found.keys())
        raise ValueError(f"staged set mismatch; missing={missing}, extra={extra}")
    for filename, path in staged.items():
        if digest(path) != digest(found[filename]):
            raise ValueError(f"staged media differs from source: {filename}")
    return len(staged)


def stage(source_dirs, manifest, destination, expected_count=550):
    found = verify_source(source_dirs, manifest, expected_count)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent))
    try:
        for filename, source in sorted(found.items()):
            shutil.copyfile(source, temporary / filename)
        check(source_dirs, manifest, temporary, expected_count)
        if destination.exists():
            shutil.rmtree(destination)
        temporary.replace(destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return len(found)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("stage", "check"), nargs="?", default="stage")
    args = parser.parse_args()
    count = (
        stage(SOURCE_DIRS, MANIFEST, DESTINATION)
        if args.command == "stage"
        else check(SOURCE_DIRS, MANIFEST, DESTINATION)
    )
    print(f"verified {count} flat media files in {DESTINATION}")


if __name__ == "__main__":
    main()
