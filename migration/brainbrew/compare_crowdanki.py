#!/usr/bin/env python3
"""Compare two CrowdAnki export directories without serializer-order noise."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

MAX_DIAGNOSTICS = 20


class InputError(ValueError):
    pass


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reject_constant(value):
    raise InputError(f"non-finite JSON number {value}")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_target(root, label):
    if not root.is_dir():
        raise InputError(f"{label}: target directory is missing")
    deck_path = root / "deck.json"
    if not deck_path.is_file():
        raise InputError(f"{label}: deck.json is missing")
    raw = deck_path.read_bytes()
    try:
        deck = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, InputError) as error:
        raise InputError(f"{label}: invalid deck.json: {error}") from error
    if not isinstance(deck, dict):
        raise InputError(f"{label}: deck.json must contain a top-level object")

    declared = deck.get("media_files")
    if not isinstance(declared, list) or any(type(name) is not str for name in declared):
        raise InputError(f"{label}: media_files must be a list of strings")
    if len(declared) != len(set(declared)):
        raise InputError(f"{label}: media_files contains duplicate names")
    for name in declared:
        path = PurePosixPath(name)
        if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
            raise InputError(f"{label}: unsafe media filename {name!r}")

    media_root = root / "media"
    if not media_root.is_dir():
        raise InputError(f"{label}: media directory is missing")
    actual = {
        path.relative_to(media_root).as_posix()
        for path in media_root.rglob("*")
        if path.is_file()
    }
    expected = set(declared)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details = []
        if missing:
            details.append("missing declared media: " + ", ".join(missing[:MAX_DIAGNOSTICS]))
        if extra:
            details.append("undeclared media: " + ", ".join(extra[:MAX_DIAGNOSTICS]))
        raise InputError(f"{label}: " + "; ".join(details))

    media = {}
    tree_digest = hashlib.sha256()
    for name in sorted(actual):
        path = media_root / name
        digest = sha256_file(path)
        size = path.stat().st_size
        media[name] = (size, digest)
        tree_digest.update(name.encode("utf-8"))
        tree_digest.update(b"\0")
        tree_digest.update(bytes.fromhex(digest))
    return {
        "deck": deck,
        "deck_size": len(raw),
        "deck_sha256": hashlib.sha256(raw).hexdigest(),
        "canonical_sha256": hashlib.sha256(
            json.dumps(deck, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "media": media,
        "media_tree_sha256": tree_digest.hexdigest(),
    }


def _render(value):
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return rendered if len(rendered) <= 160 else rendered[:157] + "..."


def json_differences(left, right, path="$"):
    differences = []
    if type(left) is not type(right):
        return [(path, left, right)]
    if isinstance(left, dict):
        for key in sorted(left.keys() | right.keys()):
            child = f"{path}.{key}" if key.isidentifier() else f"{path}[{json.dumps(key)}]"
            if key not in left:
                differences.append((child, "<missing>", right[key]))
            elif key not in right:
                differences.append((child, left[key], "<missing>"))
            else:
                differences.extend(json_differences(left[key], right[key], child))
    elif isinstance(left, list):
        for index in range(max(len(left), len(right))):
            child = f"{path}[{index}]"
            if index >= len(left):
                differences.append((child, "<missing>", right[index]))
            elif index >= len(right):
                differences.append((child, left[index], "<missing>"))
            else:
                differences.extend(json_differences(left[index], right[index], child))
    elif left != right:
        differences.append((path, left, right))
    return differences


def compare(legacy, candidate):
    differences = json_differences(legacy["deck"], candidate["deck"])
    for path, before, after in differences[:MAX_DIAGNOSTICS]:
        print(f"JSON difference {path}: legacy={_render(before)} candidate={_render(after)}")
    if differences:
        print(f"JSON differences: {len(differences)} total")

    print(
        f"deck.json bytes: legacy size={legacy['deck_size']} sha256={legacy['deck_sha256']}; "
        f"candidate size={candidate['deck_size']} sha256={candidate['deck_sha256']}; "
        f"{'identical' if legacy['deck_sha256'] == candidate['deck_sha256'] else 'different'}"
    )
    print(
        f"canonical JSON sha256: legacy={legacy['canonical_sha256']}; "
        f"candidate={candidate['canonical_sha256']}"
    )

    legacy_media = legacy["media"]
    candidate_media = candidate["media"]
    missing = sorted(legacy_media.keys() - candidate_media.keys())
    extra = sorted(candidate_media.keys() - legacy_media.keys())
    changed = sorted(
        name for name in legacy_media.keys() & candidate_media.keys()
        if legacy_media[name] != candidate_media[name]
    )
    for name in missing[:MAX_DIAGNOSTICS]:
        print(f"Media missing from candidate: {name}")
    for name in extra[:MAX_DIAGNOSTICS]:
        print(f"Media extra in candidate: {name}")
    for name in changed[:MAX_DIAGNOSTICS]:
        print(
            f"Media changed: {name}: legacy size={legacy_media[name][0]} sha256={legacy_media[name][1]}; "
            f"candidate size={candidate_media[name][0]} sha256={candidate_media[name][1]}"
        )
    print(
        f"media: legacy count={len(legacy_media)} tree_sha256={legacy['media_tree_sha256']}; "
        f"candidate count={len(candidate_media)} tree_sha256={candidate['media_tree_sha256']}"
    )
    media_difference_count = len(missing) + len(extra) + len(changed)
    if media_difference_count:
        print(f"Media differences: {media_difference_count} total")
    if differences or media_difference_count:
        print("Parity: different")
        return 1
    print("Parity: equal")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legacy", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args(argv)
    try:
        legacy = load_target(args.legacy, "legacy")
        candidate = load_target(args.candidate, "candidate")
    except (InputError, OSError) as error:
        print(f"Input error: {error}")
        return 2
    return compare(legacy, candidate)


if __name__ == "__main__":
    raise SystemExit(main())
